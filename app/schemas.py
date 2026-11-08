"""Pydantic schemas for request/response serialization and agent outputs."""

from datetime import datetime
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, EmailStr, ConfigDict


# Agent Structured Output Schemas
CategoryType = Literal["network", "access", "hardware", "software", "other"]
PriorityType = Literal["low", "medium", "high", "critical"]
ReviewDecisionType = Literal["auto_send", "needs_human_approval"]


class ClassifierOutput(BaseModel):
    """Validated structured output from the Classifier Agent."""

    category: CategoryType = Field(
        ...,
        description="Ticket category: network, access, hardware, software, or other",
    )
    priority: PriorityType = Field(
        ...,
        description="Ticket priority: low, medium, high, or critical",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for classification (0.0 to 1.0)",
    )
    reasoning: str = Field(
        ...,
        description="Brief justification for assigned category and priority",
    )


class ResolverOutput(BaseModel):
    """Validated structured output from the Resolver Agent."""

    draft_resolution: str = Field(
        ...,
        description="Actionable draft resolution addressed to the customer",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score for proposed resolution (0.0 to 1.0)",
    )
    reasoning: str = Field(
        ...,
        description="Explanation of steps and tools consulted to formulate resolution",
    )
    sources_used: List[str] = Field(
        default_factory=list,
        description="Knowledge base articles or past tickets referenced",
    )


class ReviewerOutput(BaseModel):
    """Validated structured output from the Reviewer Agent."""

    decision: ReviewDecisionType = Field(
        ...,
        description="Action decision: auto_send or needs_human_approval",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence in review decision and safety check (0.0 to 1.0)",
    )
    policy_violations: List[str] = Field(
        default_factory=list,
        description="List of detected policy violations (e.g., asking for credentials)",
    )
    missing_information: List[str] = Field(
        default_factory=list,
        description="Missing information that prevents immediate automated resolution",
    )
    reasoning: str = Field(
        ...,
        description="Safety and quality audit reasoning",
    )
    suggested_edits: Optional[str] = Field(
        default=None,
        description="Optional proposed edits if manual modification is suggested",
    )


# API Request and Response Schemas
class TicketCreate(BaseModel):
    """Schema for submitting a new IT support ticket."""

    customer_name: str = Field(..., min_length=2, max_length=100, example="Sarah Connor")
    customer_email: EmailStr = Field(..., example="sarah.connor@example.com")
    subject: str = Field(..., min_length=3, max_length=255, example="Cannot connect to corporate VPN")
    description: str = Field(
        ...,
        min_length=5,
        example="Getting an authentication gateway error when connecting to GlobalProtect VPN from home.",
    )


class AgentLogResponse(BaseModel):
    """Schema representing an agent audit log entry."""

    id: int
    ticket_id: int
    agent_name: str
    input_data: str
    output_data: str
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class ApprovalResponse(BaseModel):
    """Schema representing a ticket human approval record."""

    id: int
    ticket_id: int
    status: str
    reviewer_notes: Optional[str] = None
    edited_response: Optional[str] = None
    decided_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketResponse(BaseModel):
    """Schema representing a ticket summary."""

    id: int
    customer_name: str
    customer_email: str
    subject: str
    description: str
    category: Optional[str] = None
    priority: Optional[str] = None
    status: str
    classifier_confidence: Optional[float] = None
    resolver_confidence: Optional[float] = None
    review_status: Optional[str] = None
    draft_resolution: Optional[str] = None
    final_resolution: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TicketDetailResponse(TicketResponse):
    """Schema representing detailed ticket info with full agent trace."""

    agent_logs: List[AgentLogResponse] = []
    approvals: List[ApprovalResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ApprovalActionRequest(BaseModel):
    """Schema for human approval/rejection actions."""

    edited_response: Optional[str] = Field(
        default=None,
        description="Optional human-edited final resolution text",
    )
    reviewer_notes: Optional[str] = Field(
        default=None,
        description="Reasoning or notes recorded by the human reviewer",
    )
