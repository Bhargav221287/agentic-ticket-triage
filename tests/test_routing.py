"""Tests for LangGraph routing logic: critical priority, low confidence, and safety policies."""

import json
from app.graph import build_ticket_triage_graph, route_review_decision
from app.llm import MockLLMClient, set_llm_client


def test_routing_function_unit_checks():
    """Verify route_review_decision pure logic for diverse state conditions."""
    # Critical priority -> human approval
    crit_state = {
        "priority": "critical",
        "classifier_confidence": 0.95,
        "resolver_confidence": 0.95,
        "review_confidence": 0.95,
        "review_status": "auto_send",
        "policy_violations": [],
    }
    assert route_review_decision(crit_state) == "human_approval_queue"

    # Low classifier confidence -> human approval
    low_conf_state = {
        "priority": "medium",
        "classifier_confidence": 0.65,
        "resolver_confidence": 0.90,
        "review_confidence": 0.90,
        "review_status": "auto_send",
        "policy_violations": [],
    }
    assert route_review_decision(low_conf_state) == "human_approval_queue"

    # Policy violation present -> human approval
    violation_state = {
        "priority": "low",
        "classifier_confidence": 0.90,
        "resolver_confidence": 0.90,
        "review_confidence": 0.90,
        "review_status": "auto_send",
        "policy_violations": ["Draft asked for password"],
    }
    assert route_review_decision(violation_state) == "human_approval_queue"

    # Clean high confidence non-critical -> auto dispatch
    clean_state = {
        "priority": "medium",
        "classifier_confidence": 0.85,
        "resolver_confidence": 0.85,
        "review_confidence": 0.85,
        "review_status": "auto_send",
        "policy_violations": [],
    }
    assert route_review_decision(clean_state) == "auto_dispatch"


def test_critical_priority_graph_execution(mock_llm):
    """Verify full graph execution with critical priority routes to pending_approval."""
    mock_llm.set_responses([
        # Classifier response
        json.dumps({
            "category": "network",
            "priority": "critical",
            "confidence": 0.95,
            "reasoning": "Core datacenter firewall outage.",
        }),
        # Resolver response
        json.dumps({
            "draft_resolution": "Failover to secondary cluster initiated.",
            "confidence": 0.92,
            "reasoning": "Standard emergency SOP.",
            "sources_used": ["vpn_troubleshooting.md"],
        }),
        # Reviewer response (even if model suggests auto_send)
        json.dumps({
            "decision": "auto_send",
            "confidence": 0.90,
            "policy_violations": [],
            "missing_information": [],
            "reasoning": "Looks valid.",
            "suggested_edits": None,
        }),
    ])

    graph = build_ticket_triage_graph()
    initial_state = {
        "ticket_id": None,
        "customer_name": "Ops Lead",
        "customer_email": "ops@example.com",
        "subject": "Datacenter switch down",
        "description": "Entire secondary subnet unreachable.",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["priority"] == "critical"
    assert final_state["review_status"] == "needs_human_approval"
    assert final_state["status"] == "pending_approval"
    assert final_state.get("final_response") is None


def test_low_confidence_graph_execution(mock_llm):
    """Verify that classifier confidence < 0.70 forces routing to pending_approval."""
    mock_llm.set_responses([
        # Classifier response with low confidence (0.58)
        json.dumps({
            "category": "other",
            "priority": "low",
            "confidence": 0.58,
            "reasoning": "Vague description.",
        }),
        # Resolver response
        json.dumps({
            "draft_resolution": "Could you provide more details?",
            "confidence": 0.80,
            "reasoning": "Requested more context.",
            "sources_used": [],
        }),
        # Reviewer response
        json.dumps({
            "decision": "auto_send",
            "confidence": 0.85,
            "policy_violations": [],
            "missing_information": [],
            "reasoning": "Draft is polite.",
            "suggested_edits": None,
        }),
    ])

    graph = build_ticket_triage_graph()
    initial_state = {
        "ticket_id": None,
        "customer_name": "User",
        "customer_email": "user@example.com",
        "subject": "Weird issue",
        "description": "It is not working today.",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["status"] == "pending_approval"
    assert final_state["review_status"] == "needs_human_approval"


def test_clean_ticket_auto_resolves(mock_llm):
    """Verify that a high-confidence, standard ticket auto-resolves directly."""
    mock_llm.set_responses([
        # Classifier response
        json.dumps({
            "category": "software",
            "priority": "medium",
            "confidence": 0.92,
            "reasoning": "Zoom camera permission.",
        }),
        # Resolver response
        json.dumps({
            "draft_resolution": "Open System Settings > Privacy > Camera and enable Zoom.",
            "confidence": 0.90,
            "reasoning": "Resolved using Zoom KB.",
            "sources_used": ["slack_zoom_collaboration.md"],
        }),
        # Reviewer response
        json.dumps({
            "decision": "auto_send",
            "confidence": 0.94,
            "policy_violations": [],
            "missing_information": [],
            "reasoning": "Safe, accurate, and adheres to company policy.",
            "suggested_edits": None,
        }),
    ])

    graph = build_ticket_triage_graph()
    initial_state = {
        "ticket_id": None,
        "customer_name": "Jane",
        "customer_email": "jane@example.com",
        "subject": "Zoom camera black screen",
        "description": "Zoom cannot access webcam on macOS.",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["status"] == "resolved"
    assert final_state["review_status"] == "auto_send"
    assert final_state["final_response"] is not None
    assert "System Settings" in final_state["final_response"]


def test_policy_violation_forces_human_approval(mock_llm):
    """Verify that a draft requesting user passwords triggers policy violation and human approval."""
    mock_llm.set_responses([
        # Classifier response
        json.dumps({
            "category": "access",
            "priority": "medium",
            "confidence": 0.88,
            "reasoning": "Password lockout.",
        }),
        # Resolver response with forbidden password request
        json.dumps({
            "draft_resolution": "Please send me your password so I can log into Active Directory and reset it.",
            "confidence": 0.85,
            "reasoning": "Manual unlock attempt.",
            "sources_used": ["password_reset_policy.md"],
        }),
        # Reviewer response
        json.dumps({
            "decision": "needs_human_approval",
            "confidence": 0.96,
            "policy_violations": ["Forbidden credential request detected"],
            "missing_information": [],
            "reasoning": "Violation: Agents must never request passwords.",
            "suggested_edits": "Direct user to SSPR portal.",
        }),
    ])

    graph = build_ticket_triage_graph()
    initial_state = {
        "ticket_id": None,
        "customer_name": "Tom",
        "customer_email": "tom@example.com",
        "subject": "Account locked",
        "description": "I need help resetting my password.",
    }

    final_state = graph.invoke(initial_state)

    assert final_state["status"] == "pending_approval"
    assert len(final_state["policy_violations"]) > 0
    assert any("password" in v.lower() for v in final_state["policy_violations"])
