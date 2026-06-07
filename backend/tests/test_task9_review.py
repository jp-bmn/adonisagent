"""
Task 9 — Tests for signal review and approval endpoint
"""
from __future__ import annotations
import os
import pytest
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

from app.main import app  # noqa: E402
from app.core.config import get_settings  # noqa: E402


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


FAKE_USER_ADMIN = {
    "id":            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "name":          "Danielle Ferdon",
    "slack_user_id": "PLACEHOLDER_DANIELLE",
    "is_admin":      True,
}

FAKE_USER_AE = {
    "id":            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "name":          "Michael",
    "slack_user_id": "PLACEHOLDER_MICHAEL",
    "is_admin":      False,
}

FAKE_SIGNAL = {
    "id":                "cccccccc-cccc-cccc-cccc-cccccccccccc",
    "hospital_id":       "11111111-1111-1111-1111-111111111111",
    "signal_type":       "leadership_change",
    "tier":              "urgent",
    "confidence_score":  0.55,
    "review_status":     "pending",
    "title":             "CRO departs NYP",
    "summary":           "Chief Revenue Officer John Smith leaves New York-Presbyterian.",
    "source_url":        "https://example.com/article",
    "source_name":       "Modern Healthcare",
    "published_date":    "2026-05-20",
    "created_at":        "2026-05-20T10:00:00+00:00",
    "included_in_digest": False,
    "urgent_sent":        False,
}


@pytest.mark.asyncio
async def test_review_signal_requires_auth():
    """POST /signals/{id}/review without auth returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/signals/{FAKE_SIGNAL['id']}/review",
            json={"action": "approved", "reviewer_id": "admin-id"}
        )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_review_signal_requires_admin():
    """POST /signals/{id}/review by non-admin returns 403."""
    mock_sb = MagicMock()
    mock_sb.table.return_value = FluentChain(FAKE_USER_AE)

    with patch("app.core.auth.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_USER_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/signals/{FAKE_SIGNAL['id']}/review",
                json={"action": "approved", "reviewer_id": FAKE_USER_AE["id"]},
                headers=headers
            )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_review_signal_not_found():
    """POST /signals/{id}/review for non-existent signal returns 404."""
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_USER_ADMIN)
        if name == "signals":
            return FluentChain([])
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.signals.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_USER_ADMIN["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/signals/non-existent-id/review",
                json={"action": "approved", "reviewer_id": FAKE_USER_ADMIN["id"]},
                headers=headers
            )
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_review_signal_approve_success():
    """POST /signals/{id}/review approves signal successfully."""
    mock_sb = MagicMock()
    updated_signal = {**FAKE_SIGNAL, "review_status": "approved"}
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_USER_ADMIN)
        if name == "signals":
            # For select or update
            return FluentChain([updated_signal])
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.signals.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_USER_ADMIN["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/signals/{FAKE_SIGNAL['id']}/review",
                json={"action": "approved", "reviewer_id": FAKE_USER_ADMIN["id"]},
                headers=headers
            )
            
    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "approved"
    assert data["id"] == FAKE_SIGNAL["id"]


@pytest.mark.asyncio
async def test_review_signal_dismiss_success():
    """POST /signals/{id}/review dismisses signal successfully."""
    mock_sb = MagicMock()
    updated_signal = {**FAKE_SIGNAL, "review_status": "dismissed"}
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_USER_ADMIN)
        if name == "signals":
            return FluentChain([updated_signal])
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.signals.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_USER_ADMIN["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/signals/{FAKE_SIGNAL['id']}/review",
                json={"action": "dismissed", "reviewer_id": FAKE_USER_ADMIN["id"]},
                headers=headers
            )
            
    assert response.status_code == 200
    data = response.json()
    assert data["review_status"] == "dismissed"
