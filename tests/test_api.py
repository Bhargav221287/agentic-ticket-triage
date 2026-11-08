"""Integration tests for FastAPI REST API endpoints."""

import json
from app.models import Ticket


def test_health_and_root(client):
    """Test health check and root endpoints."""
    resp_root = client.get("/")
    assert resp_root.status_code == 200
    assert resp_root.json()["service"] == "Agentic Ticket Triage API"

    resp_health = client.get("/health")
    assert resp_health.status_code == 200
    assert resp_health.json()["status"] == "healthy"


def test_submit_ticket_creates_and_triages(client, mock_llm):
    """Test POST /tickets runs full multi-agent triage and creates ticket."""
    mock_llm.set_responses([
        json.dumps({
            "category": "network",
            "priority": "high",
            "confidence": 0.93,
            "reasoning": "VPN gateway issue.",
        }),
        json.dumps({
            "draft_resolution": "Refresh GlobalProtect connection in settings.",
            "confidence": 0.91,
            "reasoning": "Standard VPN fix.",
            "sources_used": ["vpn_troubleshooting.md"],
        }),
        json.dumps({
            "decision": "auto_send",
            "confidence": 0.95,
            "policy_violations": [],
            "missing_information": [],
            "reasoning": "Accurate and safe.",
            "suggested_edits": None,
        }),
    ])

    payload = {
        "customer_name": "Daniel Craig",
        "customer_email": "daniel.craig@example.com",
        "subject": "Cannot connect to VPN from home",
        "description": "GlobalProtect times out when trying to connect to the internal network gateway.",
    }

    response = client.post("/tickets", json=payload)
    assert response.status_code == 201

    data = response.json()
    assert data["id"] > 0
    assert data["customer_name"] == "Daniel Craig"
    assert data["category"] == "network"
    assert data["priority"] == "high"
    assert data["status"] == "resolved"
    assert "agent_logs" in data
    assert len(data["agent_logs"]) >= 3


def test_list_tickets_and_filtering(client, db_session):
    """Test GET /tickets and query filtering."""
    t1 = Ticket(
        customer_name="User A",
        customer_email="a@example.com",
        subject="Issue 1",
        description="Description 1",
        status="resolved",
        category="network",
        priority="low",
    )
    t2 = Ticket(
        customer_name="User B",
        customer_email="b@example.com",
        subject="Issue 2",
        description="Description 2",
        status="pending_approval",
        category="access",
        priority="critical",
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    # List all
    res_all = client.get("/tickets")
    assert res_all.status_code == 200
    assert len(res_all.json()) == 2

    # Filter by status
    res_pending = client.get("/tickets", params={"status": "pending_approval"})
    assert res_pending.status_code == 200
    data = res_pending.json()
    assert len(data) == 1
    assert data[0]["customer_name"] == "User B"

    # Filter by category
    res_network = client.get("/tickets", params={"category": "network"})
    assert res_network.status_code == 200
    assert len(res_network.json()) == 1


def test_get_ticket_by_id_and_not_found(client, db_session):
    """Test GET /tickets/{id} returns ticket details or 404."""
    ticket = Ticket(
        customer_name="Sam Fisher",
        customer_email="sam@example.com",
        subject="Need second monitor",
        description="Display setup request.",
        status="open",
    )
    db_session.add(ticket)
    db_session.commit()

    # Existing ticket
    resp = client.get(f"/tickets/{ticket.id}")
    assert resp.status_code == 200
    assert resp.json()["customer_name"] == "Sam Fisher"

    # Nonexistent ticket
    resp_404 = client.get("/tickets/999999")
    assert resp_404.status_code == 404
    assert "not found" in resp_404.json()["detail"].lower()
