"""Classifier agent node for assigning ticket category, priority, and confidence."""

import json
import logging
from typing import Dict, Any
from app.config import get_settings
import app.db
from app.models import AgentLog, Ticket
from app.schemas import ClassifierOutput
from app.llm import get_llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert IT Service Desk Triage Classifier Agent.
Analyze the user's support ticket and classify it accurately.

Return ONLY a JSON object adhering to this schema:
{
  "category": "network" | "access" | "hardware" | "software" | "other",
  "priority": "low" | "medium" | "high" | "critical",
  "confidence": <float between 0.0 and 1.0>,
  "reasoning": "<concise explanation for category and priority choice>"
}

Rules:
1. Category must be one of: network, access, hardware, software, other.
2. Priority must be one of: low, medium, high, critical.
   - critical: severe business disruption, total outages, security incidents, ransomware, executive blocker.
   - high: major blocker for workflow with no immediate workaround.
   - medium: standard technical defect or request with workaround.
   - low: general cosmetic inquiry, information request.
3. Be realistic and objective with confidence.
"""


def classifier_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node: Classifies ticket category, priority, and confidence.

    Args:
        state: Shared LangGraph state dictionary.

    Returns:
        Updated state fields for category, priority, and classifier confidence.
    """
    ticket_id = state.get("ticket_id")
    subject = state.get("subject", "")
    description = state.get("description", "")
    customer_name = state.get("customer_name", "Employee")

    prompt = f"""Support Ticket to Classify:
Customer: {customer_name}
Subject: {subject}
Description: {description}
"""

    llm = get_llm_client()
    input_log = {
        "ticket_id": ticket_id,
        "subject": subject,
        "description": description,
    }

    try:
        raw_json = llm.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT, max_retries=2)
        output = ClassifierOutput(**raw_json)
    except Exception as exc:
        logger.error("Classifier Agent failed to obtain valid schema: %s. Using fallback.", exc)
        output = ClassifierOutput(
            category="other",
            priority="medium",
            confidence=0.50,
            reasoning=f"Fallback classification triggered due to validation error: {str(exc)}",
        )

    output_dict = output.model_dump()

    # Persist agent audit log to database
    if ticket_id:
        db = state.get("db")
        should_close = False
        if db is None:
            db = app.db.SessionLocal()
            should_close = True

        try:
            log_entry = AgentLog(
                ticket_id=ticket_id,
                agent_name="classifier",
                input_data=json.dumps(input_log),
                output_data=json.dumps(output_dict),
            )
            db.add(log_entry)

            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                ticket.category = output.category
                ticket.priority = output.priority
                ticket.classifier_confidence = output.confidence
            db.commit()
        except Exception as db_exc:
            db.rollback()
            logger.error("Failed to persist classifier audit log: %s", db_exc)
        finally:
            if should_close:
                db.close()

    return {
        "category": output.category,
        "priority": output.priority,
        "classifier_confidence": output.confidence,
        "classifier_reasoning": output.reasoning,
    }
