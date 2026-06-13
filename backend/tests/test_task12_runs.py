"""
Task 12 — Tests for run logging, scraper orchestration integration, and runs/status endpoints.
"""
from __future__ import annotations
import os
import pytest
from datetime import datetime, timezone, timedelta
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
from app.services.run_logger import start_run, update_run, complete_run  # noqa: E402


class MockSupabaseChain:
    """Supports fluent mock chaining: .select().order().limit().execute()"""
    def __init__(self, data=None, count=None):
        self._data = data or []
        self._count = count if count is not None else len(self._data)

    def __getattr__(self, name):
        if name == "execute":
            resp = MagicMock()
            resp.data = self._data
            resp.count = self._count
            return lambda: resp
        return lambda *a, **kw: self


FAKE_ADMIN = {
    "id":            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "name":          "Danielle Ferdon",
    "slack_user_id": "PLACEHOLDER_DANIELLE",
    "is_admin":      True,
    "created_at":    "2026-06-06T12:00:00+00:00",
}

FAKE_AE = {
    "id":            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "name":          "Michael",
    "slack_user_id": "PLACEHOLDER_MICHAEL",
    "is_admin":      False,
    "created_at":    "2026-06-06T12:00:00+00:00",
}

FAKE_RUN = {
    "id": "11111111-1111-1111-1111-111111111111",
    "run_at": "2026-06-06T13:00:00+00:00",
    "hospitals_checked": 5,
    "signals_found": 10,
    "signals_new": 4,
    "rules_engine_hits": 3,
    "errors": None,
    "duration_ms": 5000,
}


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ===========================================================================
# Run Logger Service Tests
# ===========================================================================

def test_run_logger_start_run():
    mock_sb = MagicMock()
    mock_sb.table.return_value.insert.return_value.execute.return_value.data = [FAKE_RUN]

    with patch("app.services.run_logger.get_supabase", return_value=mock_sb):
        res = start_run("11111111-1111-1111-1111-111111111111")

    assert res["id"] == FAKE_RUN["id"]
    mock_sb.table.assert_called_with("agent_runs")


def test_run_logger_update_run():
    mock_sb = MagicMock()
    mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [FAKE_RUN]

    with patch("app.services.run_logger.get_supabase", return_value=mock_sb):
        res = update_run("11111111-1111-1111-1111-111111111111", hospitals_checked=3, errors=["err1"])

    assert res["id"] == FAKE_RUN["id"]
    mock_sb.table.assert_called_with("agent_runs")
    mock_sb.table.return_value.update.assert_called_with({
        "hospitals_checked": 3,
        "errors": {"errors": ["err1"]}
    })


def test_run_logger_complete_run():
    mock_sb = MagicMock()
    mock_sb.table.return_value.update.return_value.eq.return_value.execute.return_value.data = [FAKE_RUN]

    with patch("app.services.run_logger.get_supabase", return_value=mock_sb):
        res = complete_run(
            run_id="11111111-1111-1111-1111-111111111111",
            hospitals_checked=5,
            signals_found=10,
            signals_new=4,
            rules_engine_hits=3,
            duration_ms=5000,
            errors=["error_msg"]
        )

    assert res["id"] == FAKE_RUN["id"]
    mock_sb.table.assert_called_with("agent_runs")
    mock_sb.table.return_value.update.assert_called_with({
        "hospitals_checked": 5,
        "signals_found": 10,
        "signals_new": 4,
        "rules_engine_hits": 3,
        "duration_ms": 5000,
        "errors": {"errors": ["error_msg"]}
    })


# ===========================================================================
# Runs Endpoints Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_list_runs_requires_admin():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # No user header -> 401
        res = await client.get("/api/v1/runs")
        assert res.status_code == 401

        # Non-admin user header -> 403
        mock_sb = MagicMock()
        mock_sb.table.return_value = MockSupabaseChain(data=FAKE_AE)
        with patch("app.core.auth.get_supabase", return_value=mock_sb):
            res = await client.get("/api/v1/runs", headers={"X-User-Id": FAKE_AE["id"]})
            assert res.status_code == 403


@pytest.mark.asyncio
async def test_list_runs_admin_success():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return MockSupabaseChain(data=FAKE_ADMIN)
        if name == "agent_runs":
            return MockSupabaseChain(data=[FAKE_RUN])
        return MockSupabaseChain()
        
    mock_sb.table.side_effect = table_side

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.core.auth.get_supabase", return_value=mock_sb), \
             patch("app.api.endpoints.runs.get_supabase", return_value=mock_sb):
            res = await client.get("/api/v1/runs", headers={"X-User-Id": FAKE_ADMIN["id"]})
            assert res.status_code == 200
            data = res.json()
            assert len(data) == 1
            assert data[0]["id"] == FAKE_RUN["id"]


@pytest.mark.asyncio
async def test_latest_run_public_success():
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: MockSupabaseChain(data=[FAKE_RUN])

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.runs.get_supabase", return_value=mock_sb):
            res = await client.get("/api/v1/runs/latest")
            assert res.status_code == 200
            data = res.json()
            assert data["id"] == FAKE_RUN["id"]


@pytest.mark.asyncio
async def test_latest_run_empty():
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: MockSupabaseChain(data=[])

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.runs.get_supabase", return_value=mock_sb):
            res = await client.get("/api/v1/runs/latest")
            assert res.status_code == 200
            assert res.json() is None


@pytest.mark.asyncio
async def test_status_endpoint():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "agent_runs":
            return MockSupabaseChain(data=[{"run_at": "2026-06-06T13:00:00+00:00"}])
        if name == "signals":
            return MockSupabaseChain(data=[], count=42)
        if name == "hospitals":
            return MockSupabaseChain(data=[], count=5)
        return MockSupabaseChain()

    mock_sb.table.side_effect = table_side

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.runs.get_supabase", return_value=mock_sb):
            res = await client.get("/api/v1/status")
            assert res.status_code == 200
            data = res.json()
            assert data["api_version"] == "1.0.0"
            assert data["last_scraper_run"] == "2026-06-06T13:00:00+00:00"
            assert "next_scraper_run" in data
            assert data["total_signals_stored"] == 42
            assert data["total_hospitals_monitored"] == 5


# ===========================================================================
# Scraper job wiring validation
# ===========================================================================

@pytest.mark.asyncio
async def test_scraper_job_run_logger_wiring():
    from app.jobs.scraper_job import run_scraper_job

    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: MockSupabaseChain(
        data=[{"id": "hosp-1", "name": "Hospital 1"}] if name == "hospitals" else []
    )

    with patch("app.jobs.scraper_job.get_supabase", return_value=mock_sb), \
         patch("app.jobs.scraper_job.start_run") as mock_start, \
         patch("app.jobs.scraper_job.update_run") as mock_update, \
         patch("app.jobs.scraper_job.complete_run") as mock_complete:
        
        await run_scraper_job()
        
        assert mock_start.call_count == 1
        assert mock_update.call_count >= 1
        assert mock_complete.call_count == 1
