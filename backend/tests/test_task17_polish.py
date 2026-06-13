"""
Task 17 — Tests for TTL caching and list pagination headers (X-Total-Count).
"""
from __future__ import annotations
import os
import pytest
import uuid
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
from app.core.auth import get_admin_user


class FluentTableMock:
    """Supports mock chaining: .select().eq().execute(), plus count properties"""
    def __init__(self, table_name, db_data):
        self.table_name = table_name
        self.db_data = db_data  # List of dictionaries
        self._filters = []
        self._order = None
        self._limit = None
        self._is_single = False

    def select(self, *args, **kwargs):
        return self

    def eq(self, field, value):
        self._filters.append(("eq", field, value))
        return self

    def neq(self, field, value):
        self._filters.append(("neq", field, value))
        return self

    def or_(self, filter_str):
        self._filters.append(("or", None, filter_str))
        return self

    def gte(self, field, value):
        self._filters.append(("gte", field, value))
        return self

    def in_(self, field, values):
        self._filters.append(("in", field, values))
        return self

    def order(self, field, desc=False):
        self._order = (field, desc)
        return self

    def limit(self, limit):
        self._limit = limit
        return self

    def range(self, start, end):
        return self

    def single(self):
        self._is_single = True
        return self

    def execute(self):
        filtered = list(self.db_data)
        for op, field, val in self._filters:
            if op == "eq":
                filtered = [r for r in filtered if r.get(field) == val]
            elif op == "neq":
                filtered = [r for r in filtered if r.get(field) != val]
            elif op == "gte":
                filtered = [r for r in filtered if r.get(field) is not None and r.get(field) >= val]
            elif op == "in":
                filtered = [r for r in filtered if r.get(field) in val]
            elif op == "or":
                new_filtered = []
                for r in filtered:
                    match = False
                    for cond in val.split(','):
                        if cond == "review_status.is.null":
                            if r.get("review_status") is None:
                                match = True
                        elif cond == "review_status.neq.dismissed":
                            if r.get("review_status") != "dismissed":
                                match = True
                        elif cond == "review_status.eq.pending":
                            if r.get("review_status") == "pending":
                                match = True
                        else:
                            match = True
                    if match:
                        new_filtered.append(r)
                filtered = new_filtered

        if self._order:
            field, desc = self._order
            filtered.sort(key=lambda x: str(x.get(field) or ""), reverse=desc)

        if self._limit:
            filtered = filtered[:self._limit]

        resp = MagicMock()
        if self._is_single:
            resp.data = filtered[0] if filtered else None
        else:
            resp.data = filtered
        resp.count = len(filtered)
        return resp


FAKE_ADMIN = {
    "id":            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "name":          "Danielle",
    "is_admin":      True,
    "created_at":    "2026-05-20T10:00:00+00:00"
}

FAKE_SIGNAL = {
    "id": "sig-001",
    "hospital_id": "h-1",
    "tier": "worth_knowing",
    "title": "Vendor change at NYP",
    "summary": "New EHR system signed.",
    "source_url": "https://example.com/article",
    "source_name": "Modern Healthcare",
    "published_date": "2026-05-20",
    "review_status": "pending"
}


# ===========================================================================
# TTL caching tests
# ===========================================================================

@pytest.mark.asyncio
async def test_status_response_caching():
    """Verify that GET /status caches results and returns cached results on repeat calls."""
    db = {
        "agent_runs": [{"id": str(uuid.uuid4()), "run_at": "2026-06-06T12:00:00Z"}],
        "signals": [FAKE_SIGNAL] * 10,  # 10 signals
        "hospitals": [{"id": "h-1"}] * 5,  # 5 hospitals
    }
    
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: FluentTableMock(name, db.get(name, []))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.runs.get_supabase", return_value=mock_sb):
            # 1. First call (populates cache)
            res1 = await client.get("/api/v1/status")
            assert res1.status_code == 200
            assert res1.json()["total_signals_stored"] == 10
            
            # Change the simulated DB state
            db["signals"] = [FAKE_SIGNAL] * 20
            
            # 2. Second call (should return cached data)
            res2 = await client.get("/api/v1/status")
            assert res2.status_code == 200
            assert res2.json()["total_signals_stored"] == 10  # Still cached!

            # Clear cache explicitly
            from app.api.endpoints.runs import system_status
            system_status.cache_clear()
            
            # 3. Third call (should fetch new data)
            res3 = await client.get("/api/v1/status")
            assert res3.status_code == 200
            assert res3.json()["total_signals_stored"] == 20  # Updated!


@pytest.mark.asyncio
async def test_latest_run_response_caching():
    """Verify that GET /runs/latest caches results and returns cached results on repeat calls."""
    run_id1 = str(uuid.uuid4())
    run_id2 = str(uuid.uuid4())
    db = {
        "agent_runs": [{
            "id": run_id1,
            "run_at": "2026-06-06T12:00:00Z",
            "hospitals_checked": 0,
            "signals_found": 0,
            "signals_new": 0,
            "rules_engine_hits": 0
        }]
    }
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: FluentTableMock(name, db.get(name, []))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.runs.get_supabase", return_value=mock_sb):
            # 1. First call (populates cache)
            res1 = await client.get("/api/v1/runs/latest")
            assert res1.status_code == 200
            assert res1.json()["id"] == run_id1

            # Change DB state
            db["agent_runs"] = [{
                "id": run_id2,
                "run_at": "2026-06-06T13:00:00Z",
                "hospitals_checked": 0,
                "signals_found": 0,
                "signals_new": 0,
                "rules_engine_hits": 0
            }]

            # 2. Second call (should return cached data)
            res2 = await client.get("/api/v1/runs/latest")
            assert res2.status_code == 200
            assert res2.json()["id"] == run_id1

            # Clear cache explicitly
            from app.api.endpoints.runs import latest_run
            latest_run.cache_clear()

            # 3. Third call (should fetch new data)
            res3 = await client.get("/api/v1/runs/latest")
            assert res3.status_code == 200
            assert res3.json()["id"] == run_id2



# ===========================================================================
# Pagination header tests
# ===========================================================================

@pytest.mark.asyncio
async def test_list_runs_pagination_header():
    """Verify list_runs sets the X-Total-Count header."""
    app.dependency_overrides[get_admin_user] = lambda: FAKE_ADMIN

    db = {
        "ae_users": [FAKE_ADMIN],
        "agent_runs": [{
            "id": str(uuid.uuid4()),
            "run_at": "2026-06-06T12:00:00Z",
            "hospitals_checked": 0,
            "signals_found": 0,
            "signals_new": 0,
            "rules_engine_hits": 0
        }] * 42  # 42 valid runs
    }
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: FluentTableMock(name, db.get(name, []))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.runs.get_supabase", return_value=mock_sb), \
             patch("app.core.auth.get_supabase", return_value=mock_sb):
            response = await client.get("/api/v1/runs")
            assert response.status_code == 200
            assert response.headers["X-Total-Count"] == "42"

    app.dependency_overrides.clear()
