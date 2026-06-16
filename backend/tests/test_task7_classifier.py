"""
Task 7 — Tests for app/services/classifier.py and /api/v1/classify endpoint
"""
from __future__ import annotations
import os
import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport
import anthropic

# Bootstrap env
for k, v in {
    "SUPABASE_URL":         "https://test.supabase.co",
    "SUPABASE_KEY":         "test-key",
    "SLACK_BOT_TOKEN":      "xoxb-test",
    "SLACK_SIGNING_SECRET": "test-secret",
    "ANTHROPIC_API_KEY":    "test-anthropic",
    "INTERNAL_API_KEY":     "test-internal",
}.items():
    os.environ.setdefault(k, v)

# Patch scheduler so APScheduler doesn't start in tests
import app.jobs.scheduler as _sched
_sched.start_scheduler = lambda: None
_sched.stop_scheduler = lambda: None

from app.main import app  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.services.classifier import (
    classify_signal,
    _parse_claude_response,
    ClassificationResult,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear get_settings LRU cache each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ===========================================================================
# parse_claude_response helper tests
# ===========================================================================

def test_parse_claude_response_valid_json():
    raw = '{"signal_type": "rcm_hiring_spike", "tier": "worth_knowing", "confidence_score": 0.85, "title": "Hiring Spike", "summary": "Multiple roles open", "why_relevant": "Opportunity to pitch automation"}'
    parsed = _parse_claude_response(raw)
    assert parsed["signal_type"] == "rcm_hiring_spike"
    assert parsed["tier"] == "worth_knowing"
    assert parsed["confidence_score"] == 0.85
    assert parsed["title"] == "Hiring Spike"


def test_parse_claude_response_markdown_fenced():
    raw = 'Some introduction text\n```json\n{"signal_type": "epic_go_live", "tier": "urgent", "confidence_score": 0.95, "title": "Epic Go Live", "summary": "System launched", "why_relevant": "RCM assistance needed"}\n```\nSome trailing text.'
    parsed = _parse_claude_response(raw)
    assert parsed["signal_type"] == "epic_go_live"
    assert parsed["tier"] == "urgent"
    assert parsed["confidence_score"] == 0.95


def test_parse_claude_response_bare_markdown_fenced():
    raw = '```\n{"signal_type": "leadership_change", "tier": "urgent", "confidence_score": 0.9, "title": "Leader change", "summary": "CRO hired", "why_relevant": "Pitch opportunity"}\n```'
    parsed = _parse_claude_response(raw)
    assert parsed["signal_type"] == "leadership_change"
    assert parsed["tier"] == "urgent"


def test_parse_claude_response_unknown_values():
    raw = '{"signal_type": "super_special_unheard_of", "tier": "super_urgent", "confidence_score": 0.9, "title": "Bad signal", "summary": "Test", "why_relevant": "None"}'
    parsed = _parse_claude_response(raw)
    assert parsed["signal_type"] == "filtered_out"
    assert parsed["tier"] == "filtered_out"


def test_parse_claude_response_clamping():
    raw_high = '{"signal_type": "epic_go_live", "tier": "urgent", "confidence_score": 1.5, "title": "Epic", "summary": "Sys", "why_relevant": "Rel"}'
    parsed_high = _parse_claude_response(raw_high)
    assert parsed_high["confidence_score"] == 1.0

    raw_low = '{"signal_type": "epic_go_live", "tier": "urgent", "confidence_score": -0.5, "title": "Epic", "summary": "Sys", "why_relevant": "Rel"}'
    parsed_low = _parse_claude_response(raw_low)
    assert parsed_low["confidence_score"] == 0.0


# ===========================================================================
# classify_signal() unit tests
# ===========================================================================

@pytest.mark.asyncio
async def test_classify_signal_rules_engine_match():
    # Rules engine matches leadership change pattern in first 200 chars
    text = "CRO John Smith departs NewYork-Presbyterian health system today."
    res = await classify_signal(article_text=text, hospital_name="NewYork-Presbyterian")
    assert res.classification_source == "rules_engine"
    assert res.signal_type == "leadership_change"
    assert res.tier == "urgent"
    assert "leadership_change" in res.rule_name


@pytest.mark.asyncio
async def test_classify_signal_claude_match():
    text = "Adonis is announcing a brand new software feature for healthcare analytics."
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = '{"signal_type": "rcm_hiring_spike", "tier": "worth_knowing", "confidence_score": 0.75, "title": "Adonis Feature", "summary": "AI platform launch", "why_relevant": "automation opportunity"}'
    mock_response.content = [mock_content]
    mock_response.usage.input_tokens = 200
    mock_response.usage.output_tokens = 100
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client):
        res = await classify_signal(
            article_text=text,
            hospital_name="UMass Memorial",
            source_name="Press Release",
            signal_type_hint="some_hint"
        )

    assert res.classification_source == "claude_api"
    assert res.signal_type == "rcm_hiring_spike"
    assert res.tier == "worth_knowing"
    assert res.confidence_score == 0.75
    assert res.tokens_used == 300
    assert res.model_used == "claude-sonnet-4-20250514"
    mock_client.messages.create.assert_called_once()


@pytest.mark.asyncio
async def test_classify_signal_low_confidence_filters_out():
    text = "Some random text."
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = '{"signal_type": "financial_event", "tier": "worth_knowing", "confidence_score": 0.35, "title": "Low Conf", "summary": "Unsure", "why_relevant": "Unknown"}'
    mock_response.content = [mock_content]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client):
        res = await classify_signal(article_text=text, hospital_name="UMass Memorial")

    assert res.classification_source == "claude_api"
    assert res.signal_type == "filtered_out"
    assert res.tier == "filtered_out"
    assert res.confidence_score == 0.35
    assert res.why_relevant == "Filtered: confidence below threshold."


@pytest.mark.asyncio
async def test_classify_signal_anthropic_status_error():
    text = "Some text."
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.status_code = 400
    # anthropic.APIStatusError takes a message, response, and body
    mock_client.messages.create.side_effect = anthropic.APIStatusError(
        message="Bad Request",
        response=mock_response,
        body={"error": "details"}
    )

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client):
        res = await classify_signal(article_text=text, hospital_name="UMass Memorial")

    assert res.classification_source == "error"
    assert res.signal_type == "filtered_out"
    assert res.tier == "filtered_out"
    assert res.confidence_score == 0.0
    assert "API error: 400" in res.summary


@pytest.mark.asyncio
async def test_classify_signal_anthropic_connection_error():
    text = "Some text."
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = anthropic.APIConnectionError(
        request=MagicMock()
    )

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client):
        res = await classify_signal(article_text=text, hospital_name="UMass Memorial")

    assert res.classification_source == "error"
    assert res.signal_type == "filtered_out"
    assert res.tier == "filtered_out"
    assert "connection error" in res.summary


@pytest.mark.asyncio
async def test_classify_signal_json_parse_error():
    text = "Some text."
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = "This is not JSON at all."
    mock_response.content = [mock_content]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client):
        res = await classify_signal(article_text=text, hospital_name="UMass Memorial")

    assert res.classification_source == "error"
    assert res.signal_type == "filtered_out"
    assert "response parse error" in res.summary


# ===========================================================================
# Endpoint POST /api/v1/classify tests
# ===========================================================================

@pytest.mark.asyncio
async def test_classify_endpoint_success():
    payload = {
        "article_text": "CRO John Smith departs NewYork-Presbyterian health system today.",
        "hospital_name": "NewYork-Presbyterian",
        "source_name": "Modern Healthcare",
        "signal_type_hint": "leadership_change"
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/classify", json=payload)
        
    assert response.status_code == 200
    data = response.json()
    assert data["signal_type"] == "leadership_change"
    assert data["tier"] == "urgent"
    assert data["classification_source"] == "rules_engine"
    assert "why_relevant" in data


@pytest.mark.asyncio
async def test_classify_endpoint_calls_claude():
    payload = {
        "article_text": "Adonis is announcing a brand new software feature for healthcare analytics.",
        "hospital_name": "UMass Memorial",
        "source_name": "Press Release"
    }
    
    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_content = MagicMock()
    mock_content.text = '{"signal_type": "thought_leadership", "tier": "worth_knowing", "confidence_score": 0.85, "title": "AI thought", "summary": "Executive thoughts", "why_relevant": "rel"}'
    mock_response.content = [mock_content]
    mock_response.usage.input_tokens = 100
    mock_response.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_response

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/classify", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert data["signal_type"] == "thought_leadership"
    assert data["tier"] == "worth_knowing"
    assert data["classification_source"] == "claude_api"
    assert data["confidence_score"] == 0.85


@pytest.mark.asyncio
async def test_classify_endpoint_empty_fields_returns_422():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Empty article_text
        response = await client.post("/api/v1/classify", json={
            "article_text": "",
            "hospital_name": "UMass Memorial",
            "source_name": ""
        })
        assert response.status_code == 422
        assert "article_text must not be empty" in response.json()["detail"]

        # Empty hospital_name
        response = await client.post("/api/v1/classify", json={
            "article_text": "Some text",
            "hospital_name": "",
            "source_name": ""
        })
        assert response.status_code == 422
        assert "hospital_name must not be empty" in response.json()["detail"]


@pytest.mark.asyncio
async def test_classify_signal_strict_relevance_negative_cases():
    # 1. Startup strategizing around Epic's push should be filtered_out
    text1 = "How five AI startups are strategizing around Epic's big push"
    mock_client = MagicMock()
    mock_response1 = MagicMock()
    mock_content1 = MagicMock()
    mock_content1.text = '{"signal_type": "filtered_out", "tier": "filtered_out", "confidence_score": 0.35, "title": "Epic startup strategy", "summary": "Startups competing/working with Epic", "why_relevant": "Not a go-live"}'
    mock_response1.content = [mock_content1]
    mock_response1.usage.input_tokens = 100
    mock_response1.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_response1

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client):
        res1 = await classify_signal(article_text=text1, hospital_name="UMass Memorial")
    assert res1.signal_type == "filtered_out"
    assert res1.tier == "filtered_out"
    assert res1.confidence_score < 0.50

    # 2. Layoff tracker page should be filtered_out
    text2 = "Fierce Healthcare Layoff Tracker"
    mock_response2 = MagicMock()
    mock_content2 = MagicMock()
    mock_content2.text = '{"signal_type": "filtered_out", "tier": "filtered_out", "confidence_score": 0.20, "title": "Layoff Tracker", "summary": "Generic tracker of layoffs", "why_relevant": "Generic industry report"}'
    mock_response2.content = [mock_content2]
    mock_response2.usage.input_tokens = 100
    mock_response2.usage.output_tokens = 50
    mock_client.messages.create.return_value = mock_response2

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client):
        res2 = await classify_signal(article_text=text2, hospital_name="UMass Memorial")
    assert res2.signal_type == "filtered_out"
    assert res2.tier == "filtered_out"
    assert res2.confidence_score < 0.50

