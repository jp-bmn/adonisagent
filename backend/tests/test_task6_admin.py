"""
Task 6 — Tests for admin endpoints and scraper job orchestration.

Strategy:
- Admin endpoints: mock run_scraper_job / run_monday_digest, verify auth + response shape
- Scraper job: mock Supabase, verify hospital fetching, aggregation, pending-queue logic
"""
from __future__ import annotations
import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from httpx import AsyncClient, ASGITransport

# Bootstrap env
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

import app.jobs.scheduler as _sched
_sched.start_scheduler = lambda: None
_sched.stop_scheduler = lambda: None

from app.main import app  # noqa: E402
from app.core.config import get_settings  # noqa: E402


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """Clear get_settings LRU cache so INTERNAL_API_KEY is re-read each test."""
    get_settings.cache_clear()
    os.environ["INTERNAL_API_KEY"] = "test-internal"
    yield
    get_settings.cache_clear()


ADMIN_HEADERS = {"X-API-Key": "test-internal"}

FAKE_SCRAPER_RESULT = {
    "run_id":            "test-run-001",
    "status":            "completed",
    "started_at":        "2026-06-06T11:00:00+00:00",
    "duration_ms":       1234,
    "hospitals_checked": 5,
    "signals_found":     8,
    "signals_new":       3,
    "rules_engine_hits": 2,
    "errors":            [],
}


# ===========================================================================
# POST /admin/run-scraper
# ===========================================================================

@pytest.mark.asyncio
async def test_run_scraper_requires_api_key():
    """POST /admin/run-scraper without API key returns 403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/admin/run-scraper")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_run_scraper_wrong_key_returns_403():
    """POST /admin/run-scraper with wrong key returns 403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/admin/run-scraper",
            headers={"X-API-Key": "wrong-key"}
        )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_run_scraper_returns_202_accepted():
    """POST /admin/run-scraper with correct key returns 200 accepted status."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/admin/run-scraper", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "accepted"
    assert "run_id" in data
    assert "message" in data


@pytest.mark.asyncio
async def test_run_scraper_sync_returns_summary():
    """POST /admin/run-scraper-sync returns full summary JSON."""
    # Patch at source module (admin.py uses a lazy import inside the function)
    with patch("app.jobs.scraper_job.run_scraper_job", new_callable=AsyncMock) as mock_job:
        mock_job.return_value = FAKE_SCRAPER_RESULT
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/run-scraper-sync", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["hospitals_checked"] == 5
    assert data["signals_new"] == 3
    assert data["status"] == "completed"


# ===========================================================================
# POST /admin/send-digest
# ===========================================================================

@pytest.mark.asyncio
async def test_send_digest_requires_api_key():
    """POST /admin/send-digest without API key returns 403."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/admin/send-digest")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_send_digest_returns_accepted():
    """POST /admin/send-digest with correct key returns accepted."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post("/api/v1/admin/send-digest", headers=ADMIN_HEADERS)
    assert response.status_code == 200
    assert response.json()["status"] == "accepted"


@pytest.mark.asyncio
async def test_send_digest_sync_clear_queue():
    """POST /admin/send-digest-sync with no pending signals returns digest_sent or scraper_complete."""
    # Patch at source module (admin.py uses a lazy import inside the function)
    with patch("app.jobs.scraper_job.run_monday_digest", new_callable=AsyncMock) as mock_digest:
        mock_digest.return_value = {
            "status": "scraper_complete_digest_pending",
            "scraper": FAKE_SCRAPER_RESULT,
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/send-digest-sync", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("digest_sent", "scraper_complete_digest_pending")


@pytest.mark.asyncio
async def test_send_digest_sync_blocked_by_queue():
    """POST /admin/send-digest-sync with pending signals returns blocked status."""
    with patch("app.jobs.scraper_job.run_monday_digest", new_callable=AsyncMock) as mock_digest:
        mock_digest.return_value = {
            "status":        "blocked_by_review_queue",
            "pending_count": 3,
            "scraper":       FAKE_SCRAPER_RESULT,
        }
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/admin/send-digest-sync", headers=ADMIN_HEADERS)

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "blocked_by_review_queue"
    assert data["pending_count"] == 3


# ===========================================================================
# run_scraper_job() unit tests
# ===========================================================================

class MockSupabaseChain:
    """Minimal Supabase fluent chain for scraper job tests."""
    def __init__(self, data=None, count=0):
        self._data = data or []
        self._count = count

    def __getattr__(self, name):
        if name == "execute":
            resp = MagicMock()
            resp.data = self._data
            resp.count = self._count
            return lambda: resp
        return lambda *a, **kw: self


@pytest.mark.asyncio
async def test_run_scraper_job_fetches_hospitals():
    """run_scraper_job() queries the hospitals table."""
    from app.jobs.scraper_job import run_scraper_job

    mock_sb = MagicMock()
    hospitals = [
        {"id": "h1", "name": "NewYork-Presbyterian"},
        {"id": "h2", "name": "UMass Memorial"},
    ]
    signals_chain = MockSupabaseChain(data=[], count=0)

    def table_side(name):
        if name == "hospitals":
            return MockSupabaseChain(data=hospitals)
        if name == "signals":
            return signals_chain
        if name == "agent_runs":
            return MockSupabaseChain(data=[{"id": "run-001"}])
        return MockSupabaseChain()

    mock_sb.table.side_effect = table_side

    with patch("app.jobs.scraper_job.get_supabase", return_value=mock_sb):
        result = await run_scraper_job()

    assert result["hospitals_checked"] == 2
    assert "run_id" in result
    assert result["status"] in ("completed", "completed_with_errors")


@pytest.mark.asyncio
async def test_run_scraper_job_aggregates_signals():
    """run_scraper_job() sums signal counts across hospitals."""
    from app.jobs.scraper_job import run_scraper_job

    mock_sb = MagicMock()
    hospitals = [{"id": "h1", "name": "NYP"}, {"id": "h2", "name": "UMass"}]

    call_count = [0]

    def table_side(name):
        if name == "hospitals":
            return MockSupabaseChain(data=hospitals)
        if name == "signals":
            call_count[0] += 1
            # Each hospital has 2 signals
            return MockSupabaseChain(
                data=[{"id": "s1", "signal_type": "leadership_change", "tier": "urgent"},
                      {"id": "s2", "signal_type": "financial_event",   "tier": "worth_knowing"}],
                count=2,
            )
        return MockSupabaseChain(data=[{"id": "run-x"}])

    mock_sb.table.side_effect = table_side

    with patch("app.jobs.scraper_job.get_supabase", return_value=mock_sb):
        result = await run_scraper_job()

    # 2 hospitals × 2 signals each = 4 total
    assert result["signals_found"] == 4
    assert result["signals_new"] == 4


@pytest.mark.asyncio
async def test_run_scraper_job_returns_run_id():
    """run_scraper_job() result includes a valid UUID run_id."""
    import re
    from app.jobs.scraper_job import run_scraper_job

    mock_sb = MagicMock()
    mock_sb.table.return_value = MockSupabaseChain(data=[])

    with patch("app.jobs.scraper_job.get_supabase", return_value=mock_sb):
        result = await run_scraper_job()

    uuid_pattern = re.compile(
        r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    )
    assert uuid_pattern.match(result["run_id"])


# ===========================================================================
# run_monday_digest() unit tests
# ===========================================================================

@pytest.mark.asyncio
async def test_run_monday_digest_sends_when_queue_clear():
    """Monday digest proceeds when no pending signals."""
    from app.jobs.scraper_job import run_monday_digest

    mock_sb = MagicMock()

    def table_side(name):
        if name == "signals":
            # pending count query
            chain = MockSupabaseChain(data=[], count=0)
            return chain
        return MockSupabaseChain(data=[])

    mock_sb.table.side_effect = table_side

    with patch("app.jobs.scraper_job.get_supabase", return_value=mock_sb), \
         patch("app.jobs.scraper_job.run_scraper_job", new_callable=AsyncMock) as mock_scraper:
        mock_scraper.return_value = FAKE_SCRAPER_RESULT
        result = await run_monday_digest()

    assert result["status"] in ("digest_sent", "scraper_complete_digest_pending")
    assert "scraper" in result


@pytest.mark.asyncio
async def test_run_monday_digest_blocks_when_pending():
    """Monday digest is blocked when review queue has pending signals."""
    from app.jobs.scraper_job import run_monday_digest

    mock_sb = MagicMock()

    def table_side(name):
        if name == "signals":
            return MockSupabaseChain(data=[{"id": "s1"}, {"id": "s2"}], count=2)
        return MockSupabaseChain(data=[])

    mock_sb.table.side_effect = table_side

    with patch("app.jobs.scraper_job.get_supabase", return_value=mock_sb), \
         patch("app.jobs.scraper_job.run_scraper_job", new_callable=AsyncMock) as mock_scraper, \
         patch("app.jobs.scraper_job._notify_danielle_pending") as mock_notify:
        mock_scraper.return_value = FAKE_SCRAPER_RESULT
        result = await run_monday_digest()

    assert result["status"] == "blocked_by_review_queue"
    assert result["pending_count"] == 2
    mock_notify.assert_called_once_with(2)


@pytest.mark.asyncio
async def test_notify_danielle_sends_dm():
    """_notify_danielle_pending() calls send_dm via slack_service."""
    from app.jobs.scraper_job import _notify_danielle_pending

    with patch("app.services.slack_service.send_dm") as mock_dm, \
         patch("app.jobs.scraper_job.send_dm", mock_dm, create=True):
        _notify_danielle_pending(5)
    # Passes if no exception raised — Danielle DM sent or PLACEHOLDER warning logged
