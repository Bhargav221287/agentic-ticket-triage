"""LangGraph workflow definition for multi-agent ticket triage."""

from typing import TypedDict, Optional, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from app.agents.classifier import classifier_agent
from app.agents.resolver import resolver_agent
from app.agents.reviewer import reviewer_agent


class TicketState(TypedDict, total=False):
    """Typed shared state container passed between agents in the workflow."""

    ticket_id: int
    customer_name: str
    customer_email: str
    subject: str
    description: str

    # Classifier agent outputs
    category: Optional[str]
    priority: Optional[str]
    classifier_confidence: Optional[float]
    classifier_reasoning: Optional[str]

    # Resolver agent outputs
    draft_resolution: Optional[str]
    resolver_confidence: Optional[float]
    resolver_reasoning: Optional[str]
    sources_used: Optional[List[str]]
    kb_results: Optional[List[Dict[str, Any]]]
    similar_tickets: Optional[List[Dict[str, Any]]]

    # Reviewer agent outputs
    review_status: Optional[str]  # "auto_send" or "needs_human_approval"
    review_confidence: Optional[float]
    policy_violations: Optional[List[str]]
    missing_information: Optional[List[str]]
    review_reasoning: Optional[str]
    final_response: Optional[str]
    status: Optional[str]  # "resolved" or "pending_approval"


def route_review_decision(state: TicketState) -> Literal["auto_dispatch", "human_approval_queue"]:
    """Conditional router: Directs ticket based on reviewer decision and safety thresholds.

    Critical priority, confidence < 0.70, or policy violations always route to human approval.
    """
    decision = state.get("review_status")
    priority = (state.get("priority") or "").lower()
    classifier_conf = state.get("classifier_confidence") or 0.0
    resolver_conf = state.get("resolver_confidence") or 0.0
    reviewer_conf = state.get("review_confidence") or 0.0
    violations = state.get("policy_violations") or []

    # Extra routing defense in case of state tampering
    if (
        priority == "critical"
        or classifier_conf < 0.70
        or resolver_conf < 0.70
        or reviewer_conf < 0.70
        or len(violations) > 0
        or decision != "auto_send"
    ):
        return "human_approval_queue"

    return "auto_dispatch"


def auto_dispatch_node(state: TicketState) -> Dict[str, Any]:
    """Terminal node for tickets that passed automated quality and security checks."""
    return {
        "status": "resolved",
        "final_response": state.get("draft_resolution"),
    }


def human_approval_queue_node(state: TicketState) -> Dict[str, Any]:
    """Terminal node for tickets requiring human verification and approval."""
    return {
        "status": "pending_approval",
        "final_response": None,
    }


def build_ticket_triage_graph():
    """Compile and return the executable LangGraph ticket triage workflow."""
    workflow = StateGraph(TicketState)

    # 1. Register agents and terminal nodes
    workflow.add_node("classifier", classifier_agent)
    workflow.add_node("resolver", resolver_agent)
    workflow.add_node("reviewer", reviewer_agent)
    workflow.add_node("auto_dispatch", auto_dispatch_node)
    workflow.add_node("human_approval_queue", human_approval_queue_node)

    # 2. Define workflow flow
    workflow.set_entry_point("classifier")
    workflow.add_edge("classifier", "resolver")
    workflow.add_edge("resolver", "reviewer")

    # 3. Conditional routing after review
    workflow.add_conditional_edges(
        "reviewer",
        route_review_decision,
        {
            "auto_dispatch": "auto_dispatch",
            "human_approval_queue": "human_approval_queue",
        },
    )

    workflow.add_edge("auto_dispatch", END)
    workflow.add_edge("human_approval_queue", END)

    return workflow.compile()


# Pre-compiled graph instance
ticket_graph = build_ticket_triage_graph()
