"""FastAPI backend application exposing REST API for agentic ticket triage."""

from contextlib import asynccontextmanager
from datetime import datetime
import json
import logging
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_db, init_db
from app.graph import ticket_graph
from app.models import Ticket, AgentLog, Approval
from app.schemas import (
    TicketCreate,
    TicketResponse,
    TicketDetailResponse,
    ApprovalActionRequest,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("agentic-ticket-triage")
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database tables and dependencies on startup."""
    logger.info("Initializing SQLite database tables...")
    init_db()
    yield


app = FastAPI(
    title="Agentic Ticket Triage API",
    description="Multi-agent IT support ticket triage, knowledge-base resolution, and safety review with LangGraph.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for local Streamlit dashboard integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["Health"])
def root():
    """Root status endpoint."""
    return {
        "service": "Agentic Ticket Triage API",
        "status": "online",
        "docs_url": "/docs",
        "llm_provider": settings.llm_provider,
    }


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


@app.post(
    "/tickets",
    response_model=TicketDetailResponse,
    status_code=status.HTTP_201_CREATED,
    tags=["Tickets"],
)
def submit_ticket(payload: TicketCreate, db: Session = Depends(get_db)):
    """Submit a new support ticket and execute the multi-agent triage workflow.

    The workflow:
    1. Creates initial ticket record in SQLite.
    2. Runs Classifier Agent -> Resolver Agent -> Reviewer Agent -> Routing.
    3. Persists all reasoning steps to agent_logs.
    4. Auto-resolves safe tickets or routes to human approval.
    """
    # 1. Create initial ticket entry
    ticket = Ticket(
        customer_name=payload.customer_name,
        customer_email=payload.customer_email,
        subject=payload.subject,
        description=payload.description,
        status="open",
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # 2. Invoke LangGraph multi-agent workflow
    initial_state = {
        "ticket_id": ticket.id,
        "customer_name": ticket.customer_name,
        "customer_email": ticket.customer_email,
        "subject": ticket.subject,
        "description": ticket.description,
        "db": db,
    }

    try:
        final_state = ticket_graph.invoke(initial_state)
        logger.info("Ticket #%d processed. Review status: %s", ticket.id, final_state.get("review_status"))
    except Exception as exc:
        logger.error("LangGraph processing failed for ticket #%d: %s", ticket.id, exc)
        ticket.status = "open"
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Triage workflow failed: {str(exc)}",
        )

    # 3. Refresh ticket state from DB including agent logs and approvals
    db.refresh(ticket)
    return ticket


@app.get("/tickets", response_model=List[TicketResponse], tags=["Tickets"])
def list_tickets(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status"),
    category_filter: Optional[str] = Query(None, alias="category", description="Filter by category"),
    priority_filter: Optional[str] = Query(None, alias="priority", description="Filter by priority"),
    db: Session = Depends(get_db),
):
    """Retrieve all tickets with optional filtering by status, category, or priority."""
    query = db.query(Ticket)

    if status_filter:
        query = query.filter(Ticket.status == status_filter)
    if category_filter:
        query = query.filter(Ticket.category == category_filter)
    if priority_filter:
        query = query.filter(Ticket.priority == priority_filter)

    return query.order_by(Ticket.id.desc()).all()


@app.get("/tickets/{ticket_id}", response_model=TicketDetailResponse, tags=["Tickets"])
def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    """Retrieve full details of a specific ticket including agent trace and approval history."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket #{ticket_id} not found",
        )
    return ticket


@app.post("/tickets/{ticket_id}/approve", response_model=TicketDetailResponse, tags=["Approvals"])
def approve_ticket(
    ticket_id: int,
    payload: Optional[ApprovalActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Approve a ticket awaiting human authorization.

    Optionally allows human reviewer to edit the final resolution text and provide notes.
    """
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket #{ticket_id} not found",
        )

    if ticket.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticket #{ticket_id} is not awaiting approval (current status: {ticket.status})",
        )

    req_payload = payload or ApprovalActionRequest()

    # Determine final resolution (human override or agent draft)
    final_res = req_payload.edited_response if req_payload.edited_response else ticket.draft_resolution
    notes = req_payload.reviewer_notes or "Approved by human reviewer."

    ticket.status = "resolved"
    ticket.final_resolution = final_res

    # Update or create approval record
    pending_approval = (
        db.query(Approval)
        .filter(Approval.ticket_id == ticket_id, Approval.status == "pending")
        .first()
    )
    if pending_approval:
        pending_approval.status = "approved"
        pending_approval.reviewer_notes = notes
        pending_approval.edited_response = req_payload.edited_response
        pending_approval.decided_at = datetime.utcnow()
    else:
        approval_record = Approval(
            ticket_id=ticket.id,
            status="approved",
            reviewer_notes=notes,
            edited_response=req_payload.edited_response,
            decided_at=datetime.utcnow(),
        )
        db.add(approval_record)

    # Log human action to agent audit trace
    human_log = AgentLog(
        ticket_id=ticket.id,
        agent_name="human_supervisor",
        input_data=json.dumps({"action": "approve", "notes": notes}),
        output_data=json.dumps({"status": "resolved", "final_resolution": final_res}),
    )
    db.add(human_log)

    db.commit()
    db.refresh(ticket)
    return ticket


@app.post("/tickets/{ticket_id}/reject", response_model=TicketDetailResponse, tags=["Approvals"])
def reject_ticket(
    ticket_id: int,
    payload: Optional[ApprovalActionRequest] = None,
    db: Session = Depends(get_db),
):
    """Reject a proposed ticket draft awaiting human authorization."""
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ticket #{ticket_id} not found",
        )

    if ticket.status != "pending_approval":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Ticket #{ticket_id} is not awaiting approval (current status: {ticket.status})",
        )

    req_payload = payload or ApprovalActionRequest()
    notes = req_payload.reviewer_notes or "Rejected by human reviewer."

    ticket.status = "rejected"

    pending_approval = (
        db.query(Approval)
        .filter(Approval.ticket_id == ticket_id, Approval.status == "pending")
        .first()
    )
    if pending_approval:
        pending_approval.status = "rejected"
        pending_approval.reviewer_notes = notes
        pending_approval.decided_at = datetime.utcnow()
    else:
        approval_record = Approval(
            ticket_id=ticket.id,
            status="rejected",
            reviewer_notes=notes,
            decided_at=datetime.utcnow(),
        )
        db.add(approval_record)

    human_log = AgentLog(
        ticket_id=ticket.id,
        agent_name="human_supervisor",
        input_data=json.dumps({"action": "reject", "notes": notes}),
        output_data=json.dumps({"status": "rejected"}),
    )
    db.add(human_log)

    db.commit()
    db.refresh(ticket)
    return ticket
