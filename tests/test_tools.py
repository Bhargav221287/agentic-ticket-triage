"""Tests for plain Python tools: search_kb, find_similar_tickets, and get_priority_rules."""

from app.tools import search_kb, find_similar_tickets, get_priority_rules
from app.models import Ticket


def test_search_kb_finds_vpn_article():
    """Verify search_kb retrieves the VPN troubleshooting article for VPN queries."""
    results = search_kb("GlobalProtect VPN connection failed to gateway", top_k=2)
    assert len(results) > 0
    top_result = results[0]
    assert "vpn" in top_result["filename"].lower()
    assert top_result["score"] > 0
    assert "GlobalProtect" in top_result["title"]


def test_search_kb_empty_query():
    """Verify search_kb handles empty query strings gracefully."""
    results = search_kb("", top_k=3)
    assert results == []


def test_search_kb_nonexistent_directory():
    """Verify search_kb handles missing kb directories gracefully."""
    results = search_kb("VPN issue", kb_dir="nonexistent_folder_xyz")
    assert results == []


def test_find_similar_tickets(db_session):
    """Verify find_similar_tickets retrieves historical resolved tickets matching query."""
    # Seed sample resolved tickets in test DB
    t1 = Ticket(
        customer_name="Alice",
        customer_email="alice@example.com",
        subject="VPN client gateway error",
        description="GlobalProtect gateway error 403 after password reset.",
        category="network",
        priority="high",
        status="resolved",
        final_resolution="Refreshed portal settings in GlobalProtect client.",
    )
    t2 = Ticket(
        customer_name="Bob",
        customer_email="bob@example.com",
        subject="Broken office chair",
        description="Wheel fell off ergonomic office chair.",
        category="hardware",
        priority="low",
        status="resolved",
        final_resolution="Replaced chair wheel from spare parts depot.",
    )
    db_session.add_all([t1, t2])
    db_session.commit()

    similar = find_similar_tickets(
        db=db_session,
        query="GlobalProtect VPN connection error",
        category="network",
        limit=2,
    )

    assert len(similar) >= 1
    assert similar[0]["ticket_id"] == t1.id
    assert "GlobalProtect" in similar[0]["final_resolution"]


def test_get_priority_rules():
    """Verify priority rules return correct SLAs and human-in-the-loop requirements."""
    crit_rules = get_priority_rules("critical")
    assert crit_rules["sla_response_minutes"] == 15
    assert crit_rules["requires_human_approval"] is True
    assert crit_rules["auto_send_allowed"] is False

    high_rules = get_priority_rules("high")
    assert high_rules["sla_response_minutes"] == 60

    low_rules = get_priority_rules("low")
    assert low_rules["sla_response_minutes"] == 480
    assert low_rules["auto_send_allowed"] is True

    default_rules = get_priority_rules("unknown_priority")
    assert default_rules["priority"] == "medium"
