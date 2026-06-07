"""
Task 4 — Tests for app/services/slack_service.py

All Slack API calls are mocked — no real token required.
Tests cover: send_dm, format_weekly_digest, send_urgent_alert, rate limiter.
"""
from __future__ import annotations
import os
import time
import pytest
from unittest.mock import MagicMock, patch

# Bootstrap env before any app imports
for k, v in {
    "SUPABASE_URL":         "https://test.supabase.co",
    "SUPABASE_KEY":         "test-key",
    "SLACK_BOT_TOKEN":      "xoxb-test-token",
    "SLACK_SIGNING_SECRET": "test-secret",
    "ANTHROPIC_API_KEY":    "test-anthropic",
    "INTERNAL_API_KEY":     "test-internal",
}.items():
    os.environ.setdefault(k, v)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_slack_response(ts: str = "1234567890.123456") -> MagicMock:
    """Build a mock Slack API response."""
    mock = MagicMock()
    mock.data = {"ok": True, "ts": ts, "channel": "D0TEST123"}
    mock.__getitem__ = lambda self, key: self.data[key]
    mock.get = lambda key, default=None: mock.data.get(key, default)
    return mock


FAKE_SIGNAL_URGENT = {
    "id":            "sig-001",
    "hospital_id":   "hosp-001",
    "hospital_name": "NewYork-Presbyterian",
    "title":         "CRO John Smith departs NYP",
    "summary":       "Chief Revenue Officer announces departure after 5 years.",
    "tier":          "urgent",
    "signal_type":   "leadership_change",
    "source_name":   "Modern Healthcare",
    "source_url":    "https://modernhealthcare.com/test",
    "published_date": "2026-06-02",
}

FAKE_SIGNAL_WORTH = {
    "id":            "sig-002",
    "hospital_name": "UMass Memorial",
    "title":         "UMass posts 14 RCM openings",
    "summary":       "Spike in revenue cycle hiring.",
    "tier":          "worth_knowing",
    "signal_type":   "rcm_hiring_spike",
    "source_name":   "LinkedIn",
    "source_url":    "https://linkedin.com/jobs/test",
    "published_date": "2026-06-01",
}

FAKE_AE = {"id": "ae-001", "name": "Michael"}


# ---------------------------------------------------------------------------
# send_dm
# ---------------------------------------------------------------------------

def test_send_dm_calls_chat_post_message():
    """send_dm() calls client.chat_postMessage with correct args."""
    mock_response = make_slack_response()

    with patch("app.services.slack_service.get_slack_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from app.services.slack_service import send_dm
        result = send_dm(slack_user_id="U0TEST123", text="Hello from Adonis")

    mock_client.chat_postMessage.assert_called_once()
    call_kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert call_kwargs["channel"] == "U0TEST123"
    assert call_kwargs["text"] == "Hello from Adonis"
    assert "blocks" not in call_kwargs


def test_send_dm_with_blocks_passes_blocks():
    """send_dm() with blocks= passes them to Slack API."""
    mock_response = make_slack_response()
    blocks = [{"type": "section", "text": {"type": "mrkdwn", "text": "test"}}]

    with patch("app.services.slack_service.get_slack_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from app.services.slack_service import send_dm
        send_dm(slack_user_id="U0TEST123", text="fallback", blocks=blocks)

    call_kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert call_kwargs["blocks"] == blocks


def test_send_dm_returns_response_dict():
    """send_dm() returns a dict containing the Slack ts."""
    mock_response = make_slack_response(ts="9999999999.000001")

    with patch("app.services.slack_service.get_slack_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from app.services.slack_service import send_dm
        result = send_dm(slack_user_id="U0TEST123", text="hello")

    assert result["ts"] == "9999999999.000001"
    assert result["ok"] is True


# ---------------------------------------------------------------------------
# format_weekly_digest
# ---------------------------------------------------------------------------

def test_format_weekly_digest_returns_fallback_and_blocks():
    """format_weekly_digest returns (str, list) with correct types."""
    from app.services.slack_service import format_weekly_digest
    signals = [FAKE_SIGNAL_URGENT, FAKE_SIGNAL_WORTH]
    fallback, blocks = format_weekly_digest(ae_user=FAKE_AE, signals=signals, week_label="June 2–6")

    assert isinstance(fallback, str)
    assert isinstance(blocks, list)
    assert len(blocks) > 0


def test_format_weekly_digest_fallback_includes_ae_name():
    """Fallback text includes the AE's name."""
    from app.services.slack_service import format_weekly_digest
    fallback, _ = format_weekly_digest(ae_user=FAKE_AE, signals=[FAKE_SIGNAL_URGENT])
    assert "Michael" in fallback


def test_format_weekly_digest_signal_counts():
    """Fallback text reflects correct signal count."""
    from app.services.slack_service import format_weekly_digest
    fallback, _ = format_weekly_digest(ae_user=FAKE_AE, signals=[FAKE_SIGNAL_URGENT, FAKE_SIGNAL_WORTH])
    assert "2 signal" in fallback


def test_format_weekly_digest_urgent_before_worth_knowing():
    """Urgent signals appear before worth_knowing in the blocks list."""
    from app.services.slack_service import format_weekly_digest
    _, blocks = format_weekly_digest(ae_user=FAKE_AE, signals=[FAKE_SIGNAL_WORTH, FAKE_SIGNAL_URGENT])

    # Find positions of the tier header blocks
    block_texts = []
    for b in blocks:
        if b.get("type") == "section":
            text = b.get("text", {}).get("text", "")
            block_texts.append(text)

    # "Urgent" header should appear before "Worth Knowing" header
    urgent_pos = next((i for i, t in enumerate(block_texts) if "Urgent" in t), None)
    worth_pos  = next((i for i, t in enumerate(block_texts) if "Worth Knowing" in t), None)
    assert urgent_pos is not None
    assert worth_pos is not None
    assert urgent_pos < worth_pos


def test_format_weekly_digest_empty_signals():
    """format_weekly_digest handles an empty signal list without error."""
    from app.services.slack_service import format_weekly_digest
    fallback, blocks = format_weekly_digest(ae_user=FAKE_AE, signals=[])
    assert "0 signal" in fallback
    assert isinstance(blocks, list)


def test_format_weekly_digest_has_dashboard_button():
    """The blocks include a primary button linking to the dashboard."""
    from app.services.slack_service import format_weekly_digest
    _, blocks = format_weekly_digest(ae_user=FAKE_AE, signals=[FAKE_SIGNAL_URGENT])

    action_blocks = [b for b in blocks if b.get("type") == "actions"]
    assert len(action_blocks) >= 1
    button = action_blocks[0]["elements"][0]
    assert button["type"] == "button"
    assert button["style"] == "primary"


def test_format_weekly_digest_contains_hospital_names():
    """Signal hospital names appear in the block text."""
    from app.services.slack_service import format_weekly_digest
    _, blocks = format_weekly_digest(ae_user=FAKE_AE, signals=[FAKE_SIGNAL_URGENT])

    all_text = " ".join(
        b.get("text", {}).get("text", "")
        for b in blocks if b.get("type") == "section"
    )
    assert "NewYork-Presbyterian" in all_text
    assert "CRO John Smith" in all_text


# ---------------------------------------------------------------------------
# send_urgent_alert
# ---------------------------------------------------------------------------

def test_send_urgent_alert_sends_dm():
    """send_urgent_alert() calls send_dm with blocks."""
    mock_response = make_slack_response()

    with patch("app.services.slack_service.get_slack_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from app.services.slack_service import send_urgent_alert
        result = send_urgent_alert(
            signal=FAKE_SIGNAL_URGENT,
            hospital_name="NewYork-Presbyterian",
            ae_slack_user_id="U0TEST123",
        )

    assert mock_client.chat_postMessage.called
    call_kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert call_kwargs["channel"] == "U0TEST123"
    # Should have blocks (rich formatting)
    assert "blocks" in call_kwargs
    assert len(call_kwargs["blocks"]) > 0


def test_send_urgent_alert_fallback_contains_hospital():
    """send_urgent_alert fallback text includes hospital name."""
    mock_response = make_slack_response()

    with patch("app.services.slack_service.get_slack_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from app.services.slack_service import send_urgent_alert
        send_urgent_alert(
            signal=FAKE_SIGNAL_URGENT,
            hospital_name="NewYork-Presbyterian",
            ae_slack_user_id="U0TEST123",
        )

    call_kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert "NewYork-Presbyterian" in call_kwargs["text"]


def test_send_urgent_alert_header_block_contains_hospital():
    """The header block in the urgent alert includes the hospital name."""
    mock_response = make_slack_response()

    with patch("app.services.slack_service.get_slack_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.chat_postMessage.return_value = mock_response
        mock_client_fn.return_value = mock_client

        from app.services.slack_service import send_urgent_alert
        send_urgent_alert(
            signal=FAKE_SIGNAL_URGENT,
            hospital_name="Ascension",
            ae_slack_user_id="U0TEST456",
        )

    blocks = mock_client.chat_postMessage.call_args.kwargs["blocks"]
    header = next(b for b in blocks if b["type"] == "header")
    assert "Ascension" in header["text"]["text"]


# ---------------------------------------------------------------------------
# Rate limiter
# ---------------------------------------------------------------------------

def test_rate_limiter_does_not_block_under_limit():
    """SlackRateLimiter allows 10 calls without sleeping."""
    from app.services.slack_service import SlackRateLimiter
    limiter = SlackRateLimiter(max_per_minute=10)
    start = time.monotonic()
    for _ in range(10):
        limiter.wait_if_needed()
    elapsed = time.monotonic() - start
    # Should take < 1 second for 10 calls under the limit
    assert elapsed < 1.0


def test_rate_limiter_tracks_request_count():
    """SlackRateLimiter internal deque grows correctly."""
    from app.services.slack_service import SlackRateLimiter
    limiter = SlackRateLimiter(max_per_minute=100)
    for _ in range(5):
        limiter.wait_if_needed()
    assert len(limiter._timestamps) == 5
