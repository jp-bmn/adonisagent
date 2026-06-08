"""
Task 10 — Tests for territory filtering, /me, /ae-users, and assignment endpoints
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

FAKE_HOSPITAL = {
    "id":            "11111111-1111-1111-1111-111111111111",
    "name":          "NewYork-Presbyterian",
    "website_url":   "https://nyp.org",
    "division_note": None,
    "created_at":    "2026-06-06T12:00:00+00:00",
}

OTHER_HOSP_ID = "22222222-2222-2222-2222-222222222222"
OTHER_AE_ID = "cccccccc-cccc-cccc-cccc-cccccccccccc"


# ===========================================================================
# GET /me
# ===========================================================================

@pytest.mark.asyncio
async def test_get_me_admin():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_ADMIN)
        if name == "hospital_ae_assignments":
            return FluentChain([])
        return FluentChain([])
        
    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.users.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_ADMIN["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/me", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == FAKE_ADMIN["id"]
    assert data["is_admin"] is True
    assert data["hospitals"] == []
    assert data["new_signals_this_week"] == 0


@pytest.mark.asyncio
async def test_get_me_ae():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospitals": FAKE_HOSPITAL}])
        if name == "signals":
            return FluentChain([], count=5)
        return FluentChain([])
        
    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.users.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/me", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == FAKE_AE["id"]
    assert data["is_admin"] is False
    assert len(data["hospitals"]) == 1
    assert data["hospitals"][0]["id"] == FAKE_HOSPITAL["id"]
    assert data["new_signals_this_week"] == 5


# ===========================================================================
# GET /ae-users
# ===========================================================================

@pytest.mark.asyncio
async def test_ae_users_admin_only():
    mock_sb = MagicMock()
    mock_sb.table.return_value = FluentChain(FAKE_AE)
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/ae-users", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_ae_users_success():
    mock_sb = MagicMock()
    
    auth_chain = FluentChain(FAKE_ADMIN)
    aes_chain = FluentChain([FAKE_AE])
    assignments_chain = FluentChain([{"ae_id": FAKE_AE["id"], "hospitals": FAKE_HOSPITAL}])
    signals_chain = FluentChain([{"hospital_id": FAKE_HOSPITAL["id"]}])
    
    def table_side(name):
        if name == "ae_users":
            m = MagicMock()
            def eq_side(k, v):
                if k == "id":
                    return auth_chain
                if k == "is_admin":
                    return aes_chain
                return FluentChain([])
            m.select.return_value.eq.side_effect = eq_side
            return m
        if name == "hospital_ae_assignments":
            return assignments_chain
        if name == "signals":
            return signals_chain
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.users.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_ADMIN["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/ae-users", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == FAKE_AE["id"]
    assert len(data[0]["hospitals"]) == 1
    assert data[0]["new_signals_this_week"] == 1


# ===========================================================================
# POST /hospital-ae-assignments
# ===========================================================================

@pytest.mark.asyncio
async def test_create_assignment_not_found_hosp():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_ADMIN)
        if name == "hospitals":
            return FluentChain([])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.users.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_ADMIN["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/hospital-ae-assignments",
                json={"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"]},
                headers=headers
            )
    assert response.status_code == 404
    assert "Hospital" in response.json()["detail"]


@pytest.mark.asyncio
async def test_create_assignment_duplicate_conflict():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            m = MagicMock()
            m.select.return_value.eq.side_effect = lambda k, v: FluentChain(FAKE_ADMIN) if v == FAKE_ADMIN["id"] else FluentChain(FAKE_AE)
            return m
        if name == "hospitals":
            return FluentChain([FAKE_HOSPITAL])
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"]}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.users.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_ADMIN["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                "/api/v1/hospital-ae-assignments",
                json={"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"]},
                headers=headers
            )
    assert response.status_code == 409


# ===========================================================================
# Hospitals list filtering
# ===========================================================================

@pytest.mark.asyncio
async def test_list_hospitals_admin_sees_all():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_ADMIN)
        if name == "hospitals":
            return FluentChain([FAKE_HOSPITAL])
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"], "ae_users": FAKE_AE}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.hospitals.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_ADMIN["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/hospitals", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == FAKE_HOSPITAL["id"]
    assert len(data[0]["ae_users"]) == 1


@pytest.mark.asyncio
async def test_list_hospitals_ae_sees_only_assigned():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospitals":
            return FluentChain([
                FAKE_HOSPITAL,
                {"id": OTHER_HOSP_ID, "name": "Other Hospital", "website_url": None, "division_note": None, "created_at": "2026-06-06T12:00:00+00:00"}
            ])
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"], "ae_users": FAKE_AE}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.hospitals.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/hospitals", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == FAKE_HOSPITAL["id"]


# ===========================================================================
# Single Hospital Signals Access
# ===========================================================================

@pytest.mark.asyncio
async def test_get_hospital_signals_ae_access_denied():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospitals":
            return FluentChain([FAKE_HOSPITAL])
        if name == "hospital_ae_assignments":
            return FluentChain([])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.hospitals.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/hospitals/{FAKE_HOSPITAL['id']}/signals", headers=headers)
            
    assert response.status_code == 403
    assert "Access denied" in response.json()["detail"]


# ===========================================================================
# Signals List Filtering & Pending Review
# ===========================================================================

@pytest.mark.asyncio
async def test_signals_list_ae_access_another_denied():
    mock_sb = MagicMock()
    mock_sb.table.return_value = FluentChain(FAKE_AE)
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/signals?ae_id={OTHER_AE_ID}", headers=headers)
            
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_pending_review_signals_filtered_for_ae():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"]}])
        if name == "signals":
            return FluentChain([
                {"id": "sig-1", "hospital_id": FAKE_HOSPITAL["id"], "tier": "urgent", "review_status": "pending", "hospitals": {"name": "NYP"}}
            ])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.signals.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/v1/signals/pending-review", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == "sig-1"
