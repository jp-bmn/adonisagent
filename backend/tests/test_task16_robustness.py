"""
Task 16 — Tests for error handling, retry logic, and administrator notifications.
"""
from __future__ import annotations
import os
import pytest
import anthropic
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport

# Bootstrap env before any app imports
for k, v in {
    "SUPABASE_URL":         "https://test.supabase.co",
    "SUPABASE_KEY":         "test-key",
    "SLACK_BOT_TOKEN":      "xoxb-test",
    "SLACK_SIGNING_SECRET": "test-secret",
    "ANTHROPIC_API_KEY":    "test-anthropic",
    "INTERNAL_API_KEY":     "test-internal",
    "SLACK_USER_ID_DANIELLE": "U0TEST_DANIELLE",
}.items():
    os.environ.setdefault(k, v)

# Patch scheduler so APScheduler doesn't start in tests
import app.jobs.scheduler as _sched
_sched.start_scheduler = lambda: None
_sched.stop_scheduler = lambda: None

from app.main import app
from app.services.classifier import classify_signal, _classify_with_claude


# ===========================================================================
# Claude API Retry Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_classify_with_claude_retry_success():
    """Verify that when Claude API fails transiently, it retries and succeeds."""
    mock_client = MagicMock()
    
    # We want client.messages.create to fail twice (ConnectionError) and then succeed
    fake_response = MagicMock()
    fake_response.content = [MagicMock(text='{"signal_type": "epic_go_live", "tier": "urgent", "confidence_score": 0.95, "title": "Epic launch", "summary": "EHR live.", "why_relevant": "RCM sales opportunity."}')]
    fake_response.usage.input_tokens = 10
    fake_response.usage.output_tokens = 20

    call_count = 0

    def create_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise anthropic.APIConnectionError(message="Connection timed out", request=MagicMock())
        return fake_response

    mock_client.messages.create.side_effect = create_side_effect

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client), \
         patch("app.core.retry.asyncio.sleep") as mock_sleep:  # Mock sleep to run instantly
        
        result = await _classify_with_claude(
            article_text="Some text about hospital",
            hospital_name="Test Hospital",
            source_name="News",
            signal_type_hint=None
        )

        assert call_count == 3
        assert mock_sleep.call_count == 2
        assert result.signal_type == "epic_go_live"
        assert result.classification_source == "claude_api"


@pytest.mark.asyncio
async def test_classify_with_claude_all_retries_fail():
    """Verify that if all retries fail, it falls back to an error result in classify_signal."""
    mock_client = MagicMock()
    mock_client.messages.create.side_effect = anthropic.APIConnectionError(
        message="Connection timed out", request=MagicMock()
    )

    # Mock the rules engine to return no match (matched=False) so we escalate to Claude
    mock_rules_res = MagicMock(matched=False)

    with patch("app.services.classifier.get_anthropic_client", return_value=mock_client), \
         patch("app.services.classifier.classify_with_rules", return_value=mock_rules_res), \
         patch("app.core.retry.asyncio.sleep") as mock_sleep:
        
        result = await classify_signal(
            article_text="Some text about hospital",
            hospital_name="Test Hospital"
        )

        # It should retry 3 times (1 initial + 2 retries) before giving up
        assert mock_client.messages.create.call_count == 3
        assert mock_sleep.call_count == 2
        
        # Verify fallback error classification result
        assert result.signal_type == "filtered_out"
        assert result.classification_source == "error"
        assert "Claude connection error" in result.summary


# ===========================================================================
# Global Exception Handler Slack Notification Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_global_exception_handler_notifies_danielle():
    """Verify that an unhandled 500 exception sends a Slack alert to Danielle."""
    from app.core.auth import get_required_user
    from app.core.config import get_settings

    # Override the user authentication dependency to bypass database auth query
    app.dependency_overrides[get_required_user] = lambda: {
        "id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        "name": "Michael",
        "is_admin": True
    }

    try:
        mock_sb = MagicMock()
        mock_sb.table.side_effect = RuntimeError("Unhandled database failure")

        async with AsyncClient(transport=ASGITransport(app=app, raise_app_exceptions=False), base_url="http://test") as client:
            with patch("app.api.endpoints.hospitals.get_supabase", return_value=mock_sb), \
                 patch("app.services.slack_service.send_dm") as mock_send_dm:
                
                response = await client.get("/api/v1/hospitals")
                assert response.status_code == 500
                assert response.json()["error"] == "Internal server error"
                
                # Verify Slack message was sent to Danielle
                assert mock_send_dm.call_count == 1
                args, kwargs = mock_send_dm.call_args
                
                expected_id = get_settings().slack_user_id_danielle or "U0TEST_DANIELLE"
                assert kwargs.get("slack_user_id") == expected_id
                assert "Internal Server Error (500)" in kwargs.get("text")
                assert "Unhandled database failure" in kwargs.get("text")
    finally:
        # Clean up overrides under all conditions
        app.dependency_overrides.clear()
