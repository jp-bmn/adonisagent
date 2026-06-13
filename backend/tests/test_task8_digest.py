"""
Task 8 — Tests for app/services/digest_service.py and /api/v1/digests endpoints
"""
from __future__ import annotations
import os
import pytest
from datetime import date
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import AsyncClient, ASGITransport

# Bootstrap env before any app imports
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
from app.services.digest_service import (
    format_week_range,
    resolve_slack_user_id,
    get_digest_signals_for_ae,
    send_weekly_digest_to_all_aes,
    check_review_queue_and_notify,
)


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear get_settings LRU cache each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


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


# ===========================================================================
# Helper unit tests
# ===========================================================================

def test_format_week_range():
    assert format_week_range(date(2026, 6, 1), date(2026, 6, 7)) == "June 1–7"
    assert format_week_range(date(2026, 5, 29), date(2026, 6, 4)) == "May 29 – June 4"


def test_resolve_slack_user_id_real():
    ae = {"name": "Michael", "slack_user_id": "U12345"}
    assert resolve_slack_user_id(ae) == "U12345"


def test_resolve_slack_user_id_placeholder_resolved():
    ae = {"name": "Michael", "slack_user_id": "PLACEHOLDER_MICHAEL"}
    with patch("app.services.digest_service.get_settings") as mock_settings:
        mock_settings.return_value.slack_user_id_michael = "U_MICHAEL_REAL"
        assert resolve_slack_user_id(ae) == "U_MICHAEL_REAL"


def test_resolve_slack_user_id_placeholder_unresolved():
    ae = {"name": "Michael", "slack_user_id": "PLACEHOLDER_MICHAEL"}
    with patch("app.services.digest_service.get_settings") as mock_settings:
        mock_settings.return_value.slack_user_id_michael = "PLACEHOLDER_MICHAEL"
        assert resolve_slack_user_id(ae) is None


# ===========================================================================
# get_digest_signals_for_ae() unit tests
# ===========================================================================

@pytest.mark.asyncio
async def test_get_digest_signals_no_assignments():
    mock_sb = MagicMock()
    mock_sb.table.return_value = FluentChain([])
    with patch("app.services.digest_service.get_supabase", return_value=mock_sb):
        res = await get_digest_signals_for_ae("ae-uuid")
    assert res == []


@pytest.mark.asyncio
async def test_get_digest_signals_filters():
    mock_sb = MagicMock()
    
    assignments = [{"hospital_id": "hosp-1"}]
    signals = [
        {"id": "s1", "hospital_id": "hosp-1", "tier": "urgent", "review_status": None, "hospitals": {"name": "NYP"}},
        {"id": "s2", "hospital_id": "hosp-1", "tier": "worth_knowing", "review_status": "approved", "hospitals": {"name": "UMass"}},
        {"id": "s3", "hospital_id": "hosp-1", "tier": "worth_knowing", "review_status": "dismissed"},
        {"id": "s4", "hospital_id": "hosp-1", "tier": "filtered_out", "review_status": None},
        {"id": "s5", "hospital_id": "hosp-1", "tier": "urgent", "review_status": "pending"},
    ]

    def table_side(name):
        if name == "hospital_ae_assignments":
            return FluentChain(assignments)
        if name == "signals":
            return FluentChain(signals)
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    with patch("app.services.digest_service.get_supabase", return_value=mock_sb):
        res = await get_digest_signals_for_ae("ae-uuid")

    assert len(res) == 2
    assert {s["id"] for s in res} == {"s1", "s2"}
    assert res[0]["hospital_name"] == "NYP"
    assert res[1]["hospital_name"] == "UMass"


# ===========================================================================
# send_weekly_digest_to_all_aes() unit tests
# ===========================================================================

@pytest.mark.asyncio
async def test_send_weekly_digest_success():
    mock_sb = MagicMock()
    aes = [{"id": "ae-1", "name": "Michael", "slack_user_id": "PLACEHOLDER_MICHAEL"}]
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(aes)
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": "h-1"}])
        if name == "signals":
            return FluentChain([{"id": "s1", "hospital_id": "h-1", "tier": "urgent", "review_status": None, "hospitals": {"name": "NYP"}}])
        if name == "digests":
            return FluentChain([{"id": "digest-1"}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    mock_slack_res = {"ok": True, "ts": "slack-ts-123"}

    with patch("app.services.digest_service.get_supabase", return_value=mock_sb), \
         patch("app.services.digest_service.send_dm", return_value=mock_slack_res) as mock_send_dm:
        summary = await send_weekly_digest_to_all_aes()

    assert summary["sent_count"] == 1
    assert summary["signals_digested"] == 1
    assert summary["digests_created"][0]["ae_name"] == "Michael"
    assert mock_send_dm.call_count == 0  # placeholder slack id resolved to None, simulated instead


@pytest.mark.asyncio
async def test_send_weekly_digest_real_slack():
    mock_sb = MagicMock()
    aes = [{"id": "ae-1", "name": "Michael", "slack_user_id": "U12345"}]
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(aes)
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": "h-1"}])
        if name == "signals":
            return FluentChain([{"id": "s1", "hospital_id": "h-1", "tier": "urgent", "review_status": None, "hospitals": {"name": "NYP"}}])
        if name == "digests":
            return FluentChain([{"id": "digest-1"}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    mock_slack_res = {"ok": True, "ts": "slack-ts-123"}

    with patch("app.services.digest_service.get_supabase", return_value=mock_sb), \
         patch("app.services.digest_service.send_dm", return_value=mock_slack_res) as mock_send_dm:
        summary = await send_weekly_digest_to_all_aes()

    assert summary["sent_count"] == 1
    assert summary["signals_digested"] == 1
    assert mock_send_dm.call_count == 1


# ===========================================================================
# check_review_queue_and_notify() unit tests
# ===========================================================================

@pytest.mark.asyncio
async def test_check_review_queue_and_notify_blocks():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "signals":
            return FluentChain([], count=3)
        if name == "ae_users":
            return FluentChain(
                [{"id": "danielle-id", "name": "Danielle Ferdon", "slack_user_id": "U_DANIELLE", "is_admin": True}]
            )
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.services.digest_service.get_supabase", return_value=mock_sb), \
         patch("app.services.digest_service.send_dm") as mock_send_dm:
        count = await check_review_queue_and_notify()

    assert count == 3
    mock_send_dm.assert_called_once()
    assert "review" in mock_send_dm.call_args[1]["text"].lower()


# ===========================================================================
# Endpoint GET & POST /digests tests
# ===========================================================================

@pytest.mark.asyncio
async def test_get_digests_admin_receives_all():
    user_admin = {"id": "admin-id", "name": "Danielle", "is_admin": True}
    mock_sb = MagicMock()
    
    def auth_table_side(name):
        if name == "ae_users":
            return FluentChain(user_admin)
        if name == "digests":
            return FluentChain([
                {"id": "00000000-0000-0000-0000-000000000001", "ae_id": "00000000-0000-0000-0000-000000000002", "sent_at": "2026-06-06T12:00:00+00:00", "slack_message_ts": "1", "week_start": "2026-06-01", "week_end": "2026-06-07"},
                {"id": "00000000-0000-0000-0000-000000000003", "ae_id": "00000000-0000-0000-0000-000000000004", "sent_at": "2026-06-06T13:00:00+00:00", "slack_message_ts": "2", "week_start": "2026-06-01", "week_end": "2026-06-07"},
            ])
        return FluentChain([])
        
    mock_sb.table.side_effect = auth_table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.digests.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": "admin-id"}
        
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/digests", headers=headers)
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


@pytest.mark.asyncio
async def test_get_digests_ae_sees_only_own():
    user_ae = {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "name": "Michael", "is_admin": False}
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(user_ae)
        if name == "digests":
            return FluentChain([{"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbc", "ae_id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "sent_at": "2026-06-06T12:00:00+00:00", "slack_message_ts": "1", "week_start": "2026-06-01", "week_end": "2026-06-07"}])
        return FluentChain([])
        
    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.digests.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/digests", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbc"


@pytest.mark.asyncio
async def test_post_digest_send_admin_only():
    user_ae = {"id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb", "name": "Michael", "is_admin": False}
    mock_sb = MagicMock()
    mock_sb.table.return_value = FluentChain(user_ae)
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/digests/send", headers=headers)
            
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_post_digest_send_success():
    user_admin = {"id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa", "name": "Danielle", "is_admin": True}
    mock_sb = MagicMock()
    mock_sb.table.return_value = FluentChain(user_admin)
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.digests.send_weekly_digest_to_all_aes", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = {"sent_count": 1, "signals_digested": 2}
        headers = {"X-User-Id": "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/digests/send", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert data["sent_count"] == 1
    assert data["signals_digested"] == 2
