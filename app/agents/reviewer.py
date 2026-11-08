"""Reviewer agent node for safety auditing, policy enforcement, and routing decisions."""

import json
import logging
from typing import Dict, Any, List
from app.config import get_settings
import app.db
from app.models import AgentLog, Ticket, Approval
from app.schemas import ReviewerOutput
from app.llm import get_llm_client

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an expert IT Service Desk Quality & Security Reviewer Agent.
You must rigorously inspect the drafted resolution before it can be sent to an employee.

Check for:
1. SECURITY & POLICY VIOLATIONS:
   - Does the draft ask the user to share or email passwords, MFA tokens, PINs, or credentials? (STRICTLY FORBIDDEN)
   - Does the draft reveal any internal passwords or secret keys? (STRICTLY FORBIDDEN)
2. COMPLETENESS & CLARITY:
   - Is critical information missing that would leave the user blocked?
3. SENSITIVITY:
   - Does the ticket involve critical incidents, malware outbreaks, or active security threats?

Return ONLY a JSON object adhering to this schema:
{
  "decision": "auto_send" | "needs_human_approval",
  "confidence": <float between 0.0 and 1.0>,
  "policy_violations": ["<list of any policy violations found>"],
  "missing_information": ["<list of any missing items>"],
  "reasoning": "<thorough explanation of quality and safety assessment>",
  "suggested_edits": "<optional replacement or edit suggestions if human intervention needed>"
}
"""

FORBIDDEN_PASSWORD_PATTERNS = [
    r"provide your password",
    r"send (?:me |us )?your password",
    r"enter your password here",
    r"share your password",
    r"tell (?:me |us )?your password",
    r"reveal your password",
    r"what is your password",
    r"your temporary password is",
]


def check_deterministic_policy_violations(text: str) -> List[str]:
    """Perform deterministic regex check for forbidden credential requests."""
    import re
    violations = []
    lower = text.lower()
    for pattern in FORBIDDEN_PASSWORD_PATTERNS:
        if re.search(pattern, lower):
            violations.append(f"Security Policy Violation: Draft asks for or exposes credentials (pattern: '{pattern}')")
    return violations


def reviewer_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """LangGraph node: Audits draft resolution, enforces policy rules, and decides routing.

    Args:
        state: Shared LangGraph state dictionary.

    Returns:
        Updated state fields including review decision, final resolution, and status.
    """
    settings = get_settings()
    ticket_id = state.get("ticket_id")
    subject = state.get("subject", "")
    description = state.get("description", "")
    category = state.get("category", "other")
    priority = state.get("priority", "medium")
    classifier_confidence = float(state.get("classifier_confidence") or 0.0)
    resolver_confidence = float(state.get("resolver_confidence") or 0.0)
    draft_resolution = state.get("draft_resolution", "")

    # 1. Deterministic heuristic policy check
    deterministic_violations = check_deterministic_policy_violations(draft_resolution)

    prompt = f"""Support Ticket Context:
Subject: {subject}
Description: {description}
Category: {category}
Priority: {priority}
Classifier Confidence: {classifier_confidence:.2f}

Proposed Draft Resolution:
{draft_resolution}
Resolver Confidence: {resolver_confidence:.2f}

Deterministic Policy Check Findings:
{json.dumps(deterministic_violations)}

Perform quality and security review.
"""

    llm = get_llm_client()
    input_log = {
        "ticket_id": ticket_id,
        "priority": priority,
        "classifier_confidence": classifier_confidence,
        "resolver_confidence": resolver_confidence,
        "draft_resolution": draft_resolution,
    }

    try:
        raw_json = llm.generate_json(prompt=prompt, system_prompt=SYSTEM_PROMPT, max_retries=2)
        output = ReviewerOutput(**raw_json)
    except Exception as exc:
        logger.error("Reviewer Agent failed to obtain valid schema: %s. Defaulting to human approval.", exc)
        output = ReviewerOutput(
            decision="needs_human_approval",
            confidence=0.50,
            policy_violations=["Reviewer LLM output validation error"],
            missing_information=[],
            reasoning=f"Automatic review failed due to schema error: {str(exc)}. Routing to human supervisor.",
            suggested_edits=None,
        )

    # Merge deterministic violations
    all_violations = list(set(output.policy_violations + deterministic_violations))

    # ENFORCE MANDATORY CONDITIONAL ROUTING RULES:
    # 1. Critical priority tickets ALWAYS require human approval
    # 2. Classifier or Resolver or Reviewer confidence < threshold (0.70) ALWAYS requires human approval
    # 3. Any policy violation ALWAYS requires human approval
    is_critical = (priority.lower() == "critical")
    is_low_confidence = (
        classifier_confidence < settings.confidence_threshold
        or resolver_confidence < settings.confidence_threshold
        or output.confidence < settings.confidence_threshold
    )
    has_violations = len(all_violations) > 0

    final_decision = output.decision
    escalation_reasons = []

    if is_critical:
        final_decision = "needs_human_approval"
        escalation_reasons.append("Critical priority requires mandatory human authorization.")

    if is_low_confidence:
        final_decision = "needs_human_approval"
        escalation_reasons.append(
            f"Confidence score below safety threshold of {settings.confidence_threshold:.2f} "
            f"(Classifier: {classifier_confidence:.2f}, Resolver: {resolver_confidence:.2f}, Reviewer: {output.confidence:.2f})."
        )

    if has_violations:
        final_decision = "needs_human_approval"
        escalation_reasons.append(f"Policy violations detected: {'; '.join(all_violations)}")

    reasoning_summary = output.reasoning
    if escalation_reasons:
        reasoning_summary += " | ESCALATION: " + " ".join(escalation_reasons)

    # Determine status and final response
    if final_decision == "auto_send":
        new_status = "resolved"
        final_response = draft_resolution
    else:
        new_status = "pending_approval"
        final_response = None

    output_dict = {
        "decision": final_decision,
        "confidence": output.confidence,
        "policy_violations": all_violations,
        "missing_information": output.missing_information,
        "reasoning": reasoning_summary,
        "suggested_edits": output.suggested_edits,
    }

    # Persist agent audit log, ticket state, and approval record
    if ticket_id:
        db = state.get("db")
        should_close = False
        if db is None:
            db = app.db.SessionLocal()
            should_close = True

        try:
            log_entry = AgentLog(
                ticket_id=ticket_id,
                agent_name="reviewer",
                input_data=json.dumps(input_log),
                output_data=json.dumps(output_dict),
            )
            db.add(log_entry)

            ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
            if ticket:
                ticket.status = new_status
                ticket.review_status = final_decision
                if new_status == "resolved":
                    ticket.final_resolution = final_response

                if new_status == "pending_approval":
                    # Create pending approval record
                    approval_record = Approval(
                        ticket_id=ticket.id,
                        status="pending",
                        reviewer_notes=reasoning_summary,
                    )
                    db.add(approval_record)

            db.commit()
        except Exception as db_exc:
            db.rollback()
            logger.error("Failed to persist reviewer audit log: %s", db_exc)
        finally:
            if should_close:
                db.close()

    return {
        "review_status": final_decision,
        "review_confidence": output.confidence,
        "policy_violations": all_violations,
        "missing_information": output.missing_information,
        "review_reasoning": reasoning_summary,
        "final_response": final_response,
        "status": new_status,
    }
