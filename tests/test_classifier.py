"""Tests for the Classifier Agent output validation, retry handling, and fallback."""

import json
from app.agents.classifier import classifier_agent
from app.schemas import ClassifierOutput
from app.llm import MockLLMClient, set_llm_client


def test_classifier_valid_output(mock_llm):
    """Test standard valid JSON classification from Classifier Agent."""
    mock_llm.set_responses([
        json.dumps({
            "category": "network",
            "priority": "high",
            "confidence": 0.95,
            "reasoning": "VPN gateway authentication errors fall under network infrastructure.",
        })
    ])

    state = {
        "ticket_id": None,
        "customer_name": "Test User",
        "subject": "VPN Gateway Timeout",
        "description": "Cannot connect to corporate VPN gateway from home office.",
    }

    result = classifier_agent(state)

    assert result["category"] == "network"
    assert result["priority"] == "high"
    assert result["classifier_confidence"] == 0.95
    assert "VPN gateway" in result["classifier_reasoning"]


def test_classifier_retry_on_invalid_json(mock_llm):
    """Test that Classifier retries when LLM initially returns malformed JSON."""
    mock_llm.set_responses([
        "Sorry, as an AI I am thinking... Here is not JSON",  # 1st attempt: invalid
        json.dumps({  # 2nd attempt: valid
            "category": "access",
            "priority": "medium",
            "confidence": 0.88,
            "reasoning": "Account lockout issue.",
        }),
    ])

    state = {
        "ticket_id": None,
        "customer_name": "Test User",
        "subject": "Password reset needed",
        "description": "Locked out of my laptop account.",
    }

    result = classifier_agent(state)

    assert result["category"] == "access"
    assert result["priority"] == "medium"
    assert result["classifier_confidence"] == 0.88


def test_classifier_fallback_on_complete_failure(mock_llm):
    """Test that Classifier gracefully defaults to fallback schema when all attempts fail."""
    mock_llm.set_responses([
        "Malformed response 1",
        "Malformed response 2",
        "Malformed response 3",
    ])

    state = {
        "ticket_id": None,
        "customer_name": "Test User",
        "subject": "Unknown error",
        "description": "Something broke.",
    }

    result = classifier_agent(state)

    assert result["category"] == "other"
    assert result["priority"] == "medium"
    assert result["classifier_confidence"] == 0.50
    assert "Fallback classification" in result["classifier_reasoning"]
