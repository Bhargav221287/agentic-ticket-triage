"""Plain Python tools for knowledge retrieval, ticket similarity, and SLA rules."""

import os
import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import Ticket


def _tokenize(text: str) -> set[str]:
    """Tokenize and normalize text into unique lowercase alphanumeric terms."""
    return set(re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower()))


def search_kb(query: str, kb_dir: str = "kb", top_k: int = 3) -> List[Dict[str, Any]]:
    """Search markdown knowledge base articles by relevance to the query.

    Args:
        query: Search terms or ticket description.
        kb_dir: Directory containing knowledge base markdown files.
        top_k: Maximum number of articles to return.

    Returns:
        List of dictionaries with title, file_path, category, tags, snippet, and score.
    """
    if not os.path.exists(kb_dir):
        return []

    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    results: List[Dict[str, Any]] = []

    for filename in os.listdir(kb_dir):
        if not filename.endswith(".md"):
            continue

        file_path = os.path.join(kb_dir, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            continue

        # Extract title and metadata
        title = filename.replace("_", " ").replace(".md", "").title()
        category = "General"
        tags = ""

        for line in content.splitlines()[:10]:
            if line.startswith("# "):
                title = line.replace("# ", "").strip()
            elif "**Category:**" in line:
                category = line.split("**Category:**")[1].strip()
            elif "**Tags:**" in line:
                tags = line.split("**Tags:**")[1].strip()

        article_tokens = _tokenize(content + " " + title + " " + tags)
        if not article_tokens:
            continue

        # Calculate Jaccard / token overlap relevance score
        overlap = query_tokens.intersection(article_tokens)
        score = len(overlap) / (len(query_tokens) + 1e-6)

        # Boost score if tags or title match directly
        tag_tokens = _tokenize(tags + " " + title)
        tag_overlap = query_tokens.intersection(tag_tokens)
        score += len(tag_overlap) * 0.25

        if score > 0:
            # Create a concise snippet
            snippet_lines = [
                line.strip() for line in content.splitlines()
                if line.strip() and not line.startswith("#") and not line.startswith("**")
            ]
            snippet = " ".join(snippet_lines[:4])[:300] + "..." if snippet_lines else ""

            results.append({
                "filename": filename,
                "file_path": file_path,
                "title": title,
                "category": category,
                "tags": tags,
                "snippet": snippet,
                "content": content[:1500],  # Trimmed content for agent context
                "score": round(score, 3),
            })

    # Sort descending by relevance score
    results.sort(key=lambda x: x["score"], reverse=True)
    return results[:top_k]


def find_similar_tickets(
    db: Session,
    query: str,
    category: Optional[str] = None,
    limit: int = 3,
) -> List[Dict[str, Any]]:
    """Search previously resolved or closed tickets for relevant historical precedents.

    Args:
        db: SQLAlchemy database session.
        query: Query string to match against ticket subject and description.
        category: Optional category filter to narrow search.
        limit: Maximum number of similar tickets to return.

    Returns:
        List of dictionaries with ticket id, subject, category, priority, resolution, and score.
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    ticket_query = db.query(Ticket).filter(
        Ticket.final_resolution.isnot(None),
        Ticket.final_resolution != "",
    )

    if category:
        ticket_query = ticket_query.filter(Ticket.category == category)

    candidate_tickets = ticket_query.all()
    if not candidate_tickets and category:
        # Fallback to searching all resolved tickets regardless of category
        candidate_tickets = db.query(Ticket).filter(
            Ticket.final_resolution.isnot(None),
            Ticket.final_resolution != "",
        ).all()

    scored_tickets: List[Dict[str, Any]] = []
    for ticket in candidate_tickets:
        text = f"{ticket.subject} {ticket.description} {ticket.category or ''}"
        doc_tokens = _tokenize(text)
        if not doc_tokens:
            continue

        overlap = query_tokens.intersection(doc_tokens)
        score = len(overlap) / (len(query_tokens) + 1e-6)

        if score > 0.05:  # Relevance threshold
            scored_tickets.append({
                "ticket_id": ticket.id,
                "subject": ticket.subject,
                "category": ticket.category,
                "priority": ticket.priority,
                "status": ticket.status,
                "final_resolution": ticket.final_resolution,
                "score": round(score, 3),
            })

    scored_tickets.sort(key=lambda x: x["score"], reverse=True)
    return scored_tickets[:limit]


def get_priority_rules(priority: str) -> Dict[str, Any]:
    """Retrieve operational SLA and human approval rules for a given ticket priority.

    Args:
        priority: One of 'low', 'medium', 'high', 'critical'.

    Returns:
        Dictionary containing SLA response target, escalation path, and human-in-the-loop requirement.
    """
    normalized_priority = priority.lower().strip() if priority else "medium"

    rules = {
        "critical": {
            "priority": "critical",
            "sla_response_minutes": 15,
            "sla_resolution_hours": 2,
            "requires_human_approval": True,
            "auto_send_allowed": False,
            "escalation_target": "Tier 3 Infrastructure / Security Incident Team",
            "description": "Total outage, widespread security breach, or high-impact service degradation.",
        },
        "high": {
            "priority": "high",
            "sla_response_minutes": 60,
            "sla_resolution_hours": 8,
            "requires_human_approval": False,  # Conditioned on agent confidence >= 0.70
            "auto_send_allowed": True,
            "escalation_target": "Tier 2 Systems Engineering",
            "description": "Significant impairment to core workflow for key team or individual without workaround.",
        },
        "medium": {
            "priority": "medium",
            "sla_response_minutes": 240,
            "sla_resolution_hours": 24,
            "requires_human_approval": False,
            "auto_send_allowed": True,
            "escalation_target": "Tier 1 Service Desk",
            "description": "Routine IT issue or application malfunction with known temporary workaround.",
        },
        "low": {
            "priority": "low",
            "sla_response_minutes": 480,
            "sla_resolution_hours": 72,
            "requires_human_approval": False,
            "auto_send_allowed": True,
            "escalation_target": "Tier 1 Service Desk / Self-Service",
            "description": "General inquiry, cosmetic request, or non-urgent peripheral preference.",
        },
    }

    return rules.get(
        normalized_priority,
        {
            "priority": "medium",
            "sla_response_minutes": 240,
            "sla_resolution_hours": 24,
            "requires_human_approval": False,
            "auto_send_allowed": True,
            "escalation_target": "Tier 1 Service Desk",
            "description": "Default priority handling.",
        },
    )
