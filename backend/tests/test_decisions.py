"""
Tests for the backend alignment changes:
1. Batch ingest tier promotions (rcm_hiring_spike and vendor_change default to urgent).
2. Co-pilot API endpoint (POST /api/v1/copilot).
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
}.items():
    os.environ.setdefault(k, v)

# Patch scheduler so APScheduler doesn't start in tests
import app.jobs.scheduler as _sched
_sched.start_scheduler = lambda: None
_sched.stop_scheduler = lambda: None

from app.main import app
from app.api.endpoints.ingest import _infer_tier


class FluentChain:
    def __init__(self, data):
        self._resp = MagicMock()
        self._resp.data = data

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


def test_batch_ingest_promoted_tiers():
    """Verify rcm_hiring_spike and vendor_change infer urgent tier in batch ingestion."""
    assert _infer_tier("rcm_hiring_spike", []) == "urgent"
    assert _infer_tier("vendor_change", []) == "urgent"
    # Verify standard worth_knowing types still work
    assert _infer_tier("financial_event", []) == "worth_knowing"
    # Verify other urgent types still work
    assert _infer_tier("leadership_change", []) == "urgent"


@pytest.mark.asyncio
async def test_copilot_endpoint_requires_auth():
    """POST /api/v1/copilot without X-User-Id returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/copilot",
            json={
                "user_id": str(uuid.uuid4()),
                "message": "Hello Co-pilot",
            }
        )
    assert response.status_code == 401


@pytest.mark.asyncio
@patch("app.core.auth.get_supabase")
async def test_copilot_endpoint_success(mock_get_supabase):
    """POST /api/v1/copilot returns the mocked response when authorized."""
    # Mock database lookup for AE user auth check
    mock_sb = MagicMock()
    mock_get_supabase.return_value = mock_sb
    mock_sb.table.return_value.select.return_value.eq.return_value.single.return_value = FluentChain(FAKE_AE)

    user_uuid = uuid.uuid4()
    hospital_uuid = uuid.uuid4()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/copilot",
            headers={"X-User-Id": FAKE_AE["id"]},
            json={
                "user_id": str(user_uuid),
                "message": "What is the status of Ascension?",
                "context_hospital_id": str(hospital_uuid),
            }
        )

    assert response.status_code == 200
    data = response.json()
    assert "Co-pilot stub" in data["reply"]
    assert data["sources"] == []
