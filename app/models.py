"""SQLAlchemy models for tickets, agent execution logs, and approvals."""

from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.db import Base


class Ticket(Base):
    """Support ticket table storing core attributes and workflow state."""

    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String(100), nullable=False)
    customer_email = Column(String(255), nullable=False)
    subject = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Classification fields
    category = Column(String(50), nullable=True)  # network, access, hardware, software, other
    priority = Column(String(50), nullable=True)  # low, medium, high, critical
    classifier_confidence = Column(Float, nullable=True)

    # Workflow and triage state
    status = Column(String(50), default="open", nullable=False)  # open, in_progress, pending_approval, resolved, rejected
    resolver_confidence = Column(Float, nullable=True)
    review_status = Column(String(50), nullable=True)  # auto_send, needs_human_approval

    draft_resolution = Column(Text, nullable=True)
    final_resolution = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    agent_logs = relationship(
        "AgentLog",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="AgentLog.id.asc()",
    )
    approvals = relationship(
        "Approval",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="Approval.id.desc()",
    )


class AgentLog(Base):
    """Audit log capturing every agent invocation step for explainability."""

    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_name = Column(String(50), nullable=False)  # classifier, resolver, reviewer
    input_data = Column(Text, nullable=False)  # Serialized JSON
    output_data = Column(Text, nullable=False)  # Serialized JSON
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="agent_logs")


class Approval(Base):
    """Human-in-the-loop approval record for low-confidence or sensitive tickets."""

    __tablename__ = "approvals"

    id = Column(Integer, primary_key=True, index=True)
    ticket_id = Column(Integer, ForeignKey("tickets.id", ondelete="CASCADE"), nullable=False, index=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, approved, rejected
    reviewer_notes = Column(Text, nullable=True)
    edited_response = Column(Text, nullable=True)
    decided_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    ticket = relationship("Ticket", back_populates="approvals")
