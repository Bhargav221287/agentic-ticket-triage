"""Resolver agent node for drafting IT resolutions using KB and historical tickets."""

import json
import logging
from typing import Dict, Any, List
from app.config import get_settings
import app.db
from app.models import AgentLog, Ticket
from app.schemas import ResolverOutput
from app.llm import get_llm_client
from app.tools import search_kb, find_similar_tickets, get_priority_rules

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert IT Tier-2 Resolution Agent.
Your role is to draft a helpful, professional, step-by-step resolution for the user's support ticket
using knowledge base articles and similar past tickets.

Return ONLY a JSON object adhering to this schema:
{
  "draft_resolution": "<Polite, detailed, step-by-step resolution addressed to the customer>",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<Summary of why this resolution was chosen and which steps apply>",
  "sources_used": ["<list of knowledge base article filenames or ticket IDs>"]
}

STRICT SECURITY RULES:
1. NEVER ask the customer to reveal, send, or email their password, PIN, or MFA token.
2. If the user requires a password reset or account unlock, ALWAYS direct them to the self-service portal:
   https://identity.internal.corp/sspr
3. Always maintain an empathetic, professional tone.
"""


def resolver_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node: Formulates a draft resolution using tools and LLM synthesis.

    Args:
        state: Shared LangGraph state dictionary.

    Returns:
        Updated state fields for draft resolution, confidence, reasoning, and sources.
    """
    settings = get_settings()
    ticket_id = state.get("ticket_id")
    subject = state.get("subject", "")
    description = state.get("description", "")
    customer_name = state.get("customer_name", "Employee")
    category = state.get("category", "other")
    priority = state.get("priority", "medium")

    # 1. Execute plain Python tools
    query = f"{subject} {description}"
    kb_results = search_kb(query=query, kb_dir=settings.kb_dir, top_k=3)

    db = state.get("db")
    should_close = False
    if db is None:
        db = app.db.SessionLocal()
        should_close = True

    try:
        similar_tickets = find_similar_tickets(
            db=db,
            query=query,
            category=category,
            limit=3,
        )
    finally:
        if should_close:
            db.close()

    priority_rules = get_priority_rules(priority)

    # 2. Format tool outputs for prompt context
    kb_context = "\n\n".join([
        f"--- Article: {item['filename']} ({item['title']}) ---\n{item['snippet']}\nFull content snippet:\n{item['content'][:600]}"
        for item in kb_results
    ]) if kb_results else "No relevant knowledge base articles found."

    similar_context = "\n\n".join([
        f"--- Past Ticket #{item['ticket_id']}: {item['subject']} (Category: {item['category']}) ---\nResolution: {item['final_resolution']}"
        for item in similar_tickets
    ]) if similar_tickets else "No past similar tickets found."

    prompt = f"""Support Ticket Details:
Customer Name: {customer_name}
Subject: {subject}
Description: {description}
Category: {category}
Priority: {priority} (SLA Response Target: {priority_rules.get('sla_response_minutes', 60)} minutes)

Relevant Knowledge Base Articles:
{kb_context}

Similar Past Resolved Tickets:
{similar_context}

Please formulate an actionable, professional draft resolution.
"""

    llm = get_llm_client()
    input_log = {
        "ticket_id": ticket_id,
        "subject": subject,
        "category": category,
        "priority": priority,
        "kb_sources": [k["filename"] for k in kb_results],
        "similar_ticket_ids": [s["ticket_id"] for s in similar_tickets],
    }

    try:
        raw_json = llm.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT, max_retries=2)
        output = ResolverOutput(**raw_json)
    except Exception as exc:
        logger.error("Resolver Agent failed to obtain valid schema: %s. Using fallback.", exc)
        default_sources = [k["filename"] for k in kb_results[:1]]
        output = ResolverOutput(
            draft_resolution=(
                f"Hello {customer_name},\n\nThank you for contacting IT Support regarding '{subject}'. "
                f"Our service desk is currently reviewing your ticket. In the meantime, please check our self-service "
                f"portal at https://identity.internal.corp or restart the affected application.\n\n"
                f"Best regards,\nIT Service Desk"
            ),
            confidence=0.50,
            reasoning=f"Fallback resolution generated due to validation error: {str(exc)}",
            sources_used=default_sources,
        )

    output_dict = output.model_dump()

    # Persist agent audit log and update ticket draft
    if ticket_id:
        db = state.get("db")
        should_close = False
        if db is None:
            db = app.db.SessionLocal()
            should_close = True

        try:
            log_entry = AgentLog(
                ticket_id=ticket_id,
                agent_name="resolver",
                input_data=json.dumps(input_log),
                output_data=json.dumps(output_dict),
            )
            db.add(log_entry)

            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                ticket.draft_resolution = output.draft_resolution
                ticket.resolver_confidence = output.confidence
            db.commit()
        except Exception as db_exc:
            db.rollback()
            logger.error("Failed to persist resolver audit log: %s", db_exc)
        finally:
            if should_close:
                db.close()

    return {
        "draft_resolution": output.draft_resolution,
        "resolver_confidence": output.confidence,
        "resolver_reasoning": output.reasoning,
        "sources_used": output.sources_used,
        "kb_results": kb_results,
        "similar_tickets": similar_tickets,
    }
