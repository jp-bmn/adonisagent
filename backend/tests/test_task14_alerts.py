"""
Task 14 — Tests for immediate urgent alerts, same-day deduplication, and background task integration.
"""
from __future__ import annotations
import os
import pytest
from datetime import datetime, timezone, timedelta
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

from app.main import app  # noqa: E402
from app.core.config import get_settings  # noqa: E402
from app.services.alert_service import send_urgent_alert_for_signal  # noqa: E402


class FluentChain:
    """Supports mock chaining: .select().eq().execute()"""
    def __init__(self, data, count=None):
        self._resp = MagicMock()
        self._resp.data = data
        self._resp.count = count if count is not None else (len(data) if isinstance(data, list) else 0)

    def __getattr__(self, name):
        if name == "execute":
            return lambda: self._resp
        return lambda *a, **kw: self

    def execute(self):
        return self._resp


FAKE_AE = {
    "id":            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "name":          "Michael",
    "slack_user_id": "PLACEHOLDER_MICHAEL",
    "is_admin":      False,
}

FAKE_HOSPITAL = {
    "id":            "11111111-1111-1111-1111-111111111111",
    "name":          "NewYork-Presbyterian",
}

FAKE_URGENT_SIGNAL = {
    "id":                "sig-urgent-001",
    "hospital_id":       FAKE_HOSPITAL["id"],
    "signal_type":       "leadership_change",
    "tier":              "urgent",
    "confidence_score":  0.95,
    "review_status":     None,
    "title":             "CRO departs NYP",
    "summary":           "Chief Revenue Officer John Smith leaves New York-Presbyterian.",
    "source_url":        "https://example.com/article",
    "source_name":       "Modern Healthcare",
    "published_date":    "2026-05-20",
    "created_at":        "2026-05-20T10:00:00+00:00",
    "urgent_sent":        False,
    "hospitals": {
        "name": FAKE_HOSPITAL["name"]
    }
}


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ===========================================================================
# Alert Service Unit Tests
# ===========================================================================

def test_alert_service_non_urgent_signal():
    mock_sb = MagicMock()
    non_urgent = {**FAKE_URGENT_SIGNAL, "tier": "worth_knowing"}
    mock_sb.table.return_value.select.return_value.eq.return_value.execute.return_value.data = [non_urgent]

    with patch("app.services.alert_service.get_supabase", return_value=mock_sb):
        res = send_urgent_alert_for_signal("sig-urgent-001")
        assert res is False


def test_alert_service_deduplication():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "signals":
            m = MagicMock()
            m.select.return_value.eq.return_value.execute.return_value.data = [FAKE_URGENT_SIGNAL]
            m.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value.data = [{"id": "other-sig"}]
            return m
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    with patch("app.services.alert_service.get_supabase", return_value=mock_sb):
        res = send_urgent_alert_for_signal("sig-urgent-001")
        assert res is False


def test_alert_service_success():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "signals":
            m = MagicMock()
            m.select.return_value.eq.return_value.execute.return_value.data = [FAKE_URGENT_SIGNAL]
            m.select.return_value.eq.return_value.eq.return_value.gte.return_value.execute.return_value.data = []
            m.update.return_value.eq.return_value.execute.return_value.data = [{**FAKE_URGENT_SIGNAL, "urgent_sent": True}]
            return m
        if name == "hospital_ae_assignments":
            return FluentChain([{"ae_id": FAKE_AE["id"]}])
        if name == "ae_users":
            return FluentChain([{"name": "Michael", "slack_user_id": "U12345"}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    with patch("app.services.alert_service.get_supabase", return_value=mock_sb), \
         patch("app.services.alert_service.send_urgent_alert") as mock_alert, \
         patch("app.services.alert_service.send_dm") as mock_dm:
        
        res = send_urgent_alert_for_signal("sig-urgent-001")
        assert res is True
        assert mock_alert.call_count == 1
        assert mock_dm.call_count == 1  # Danielle notification


# ===========================================================================
# Endpoint Integration Test
# ===========================================================================

@pytest.mark.asyncio
async def test_create_signal_triggers_background_alert():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospitals":
            return FluentChain([FAKE_HOSPITAL])
        if name == "signals":
            return FluentChain([FAKE_URGENT_SIGNAL])
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.core.auth.get_supabase", return_value=mock_sb), \
             patch("app.api.endpoints.signals.get_supabase", return_value=mock_sb), \
             patch("app.services.alert_service.send_urgent_alert_for_signal") as mock_alert_task:
            
            headers = {"X-User-Id": FAKE_AE["id"]}
            response = await client.post(
                "/api/v1/signals",
                json={
                    "hospital_id": FAKE_HOSPITAL["id"],
                    "signal_type": "leadership_change",
                    "tier": "urgent",
                    "confidence_score": 0.95,
                    "title": "New CEO at hospital"
                },
                headers=headers
            )
            assert response.status_code == 201
            assert mock_alert_task.call_count == 1
