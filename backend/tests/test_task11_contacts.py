"""
Task 11 — Tests for contact storage endpoints
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
}

FAKE_CONTACT = {
    "id":                "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "hospital_id":       "11111111-1111-1111-1111-111111111111",
    "full_name":         "John Doe",
    "role":              "Director of RCM",
    "prior_employer":    "Other Hosp",
    "linkedin_url":      "https://linkedin.com/in/johndoe",
    "linkedin_verified": False,
    "is_active":         True,
    "created_at":        "2026-06-06T12:00:00+00:00",
    "updated_at":        "2026-06-06T12:00:00+00:00",
}


# ===========================================================================
# GET /contacts
# ===========================================================================

@pytest.mark.asyncio
async def test_list_contacts_ae_assigned_success():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"]}])
        if name == "contacts":
            return FluentChain([FAKE_CONTACT])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.contacts.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/contacts?hospital_id={FAKE_HOSPITAL['id']}", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["full_name"] == "John Doe"


@pytest.mark.asyncio
async def test_list_contacts_ae_access_denied():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospital_ae_assignments":
            return FluentChain([])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.contacts.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get(f"/api/v1/contacts?hospital_id={FAKE_HOSPITAL['id']}", headers=headers)
            
    assert response.status_code == 403


# ===========================================================================
# POST /contacts
# ===========================================================================

@pytest.mark.asyncio
async def test_create_contact_duplicate_name_conflict():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospitals":
            return FluentChain([FAKE_HOSPITAL])
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"]}])
        if name == "contacts":
            return FluentChain([FAKE_CONTACT])
        return FluentChain([])

    mock_sb.table.side_effect = table_side
    
    payload = {
        "hospital_id": FAKE_HOSPITAL["id"],
        "full_name": "John Doe",
        "role": "Director of RCM",
        "linkedin_url": "https://linkedin.com/in/johndoe",
        "linkedin_verified": False
    }

    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.contacts.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/contacts", json=payload, headers=headers)
            
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_create_contact_success():
    mock_sb = MagicMock()
    
    class ContactsFluentChain:
        def __init__(self):
            self._is_insert = False
            
        def insert(self, *a, **kw):
            self._is_insert = True
            return self
            
        def __getattr__(self, name):
            if name == "execute":
                return self.execute
            return lambda *a, **kw: self
            
        def execute(self):
            resp = MagicMock()
            if self._is_insert:
                resp.data = [FAKE_CONTACT]
            else:
                resp.data = []
            return resp

    def signals_table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospitals":
            return FluentChain([FAKE_HOSPITAL])
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"]}])
        if name == "contacts":
            return ContactsFluentChain()
        return FluentChain([])

    mock_sb.table.side_effect = signals_table_side

    payload = {
        "hospital_id": FAKE_HOSPITAL["id"],
        "full_name": "John Doe",
        "role": "Director of RCM",
    }

    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.contacts.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/contacts", json=payload, headers=headers)
            
    assert response.status_code == 201
    data = response.json()
    assert data["full_name"] == "John Doe"
    assert data["id"] == FAKE_CONTACT["id"]


# ===========================================================================
# PATCH /contacts/{contact_id}
# ===========================================================================

@pytest.mark.asyncio
async def test_update_contact_success():
    mock_sb = MagicMock()
    updated = {**FAKE_CONTACT, "role": "VP of RCM"}
    
    class UpdateFluentChain:
        def __init__(self):
            self._is_update = False
            
        def update(self, *a, **kw):
            self._is_update = True
            return self
            
        def __getattr__(self, name):
            if name == "execute":
                return self.execute
            return lambda *a, **kw: self
            
        def execute(self):
            resp = MagicMock()
            if self._is_update:
                resp.data = [updated]
            else:
                resp.data = [FAKE_CONTACT]
            return resp

    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "contacts":
            return UpdateFluentChain()
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"]}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.contacts.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.patch(
                f"/api/v1/contacts/{FAKE_CONTACT['id']}",
                json={"role": "VP of RCM"},
                headers=headers
            )
            
    assert response.status_code == 200
    data = response.json()
    assert data["role"] == "VP of RCM"


# ===========================================================================
# POST /contacts/{contact_id}/verify-linkedin
# ===========================================================================

@pytest.mark.asyncio
async def test_verify_linkedin_success():
    mock_sb = MagicMock()
    verified = {**FAKE_CONTACT, "linkedin_url": "https://linkedin.com/in/verified", "linkedin_verified": True}
    
    class VerifyFluentChain:
        def __init__(self):
            self._is_verify = False
            
        def update(self, *a, **kw):
            self._is_verify = True
            return self
            
        def __getattr__(self, name):
            if name == "execute":
                return self.execute
            return lambda *a, **kw: self
            
        def execute(self):
            resp = MagicMock()
            if self._is_verify:
                resp.data = [verified]
            else:
                resp.data = [FAKE_CONTACT]
            return resp

    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "contacts":
            return VerifyFluentChain()
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"], "ae_id": FAKE_AE["id"]}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.contacts.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post(
                f"/api/v1/contacts/{FAKE_CONTACT['id']}/verify-linkedin",
                json={"linkedin_url": "https://linkedin.com/in/verified"},
                headers=headers
            )
            
    assert response.status_code == 200
    data = response.json()
    assert data["linkedin_verified"] is True
    assert data["linkedin_url"] == "https://linkedin.com/in/verified"


# ===========================================================================
# DELETE /contacts/{contact_id}
# ===========================================================================

@pytest.mark.asyncio
async def test_delete_contact_admin_only_forbidden():
    mock_sb = MagicMock()
    mock_sb.table.return_value = FluentChain(FAKE_AE)
    
    with patch("app.core.auth.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_AE["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/v1/contacts/{FAKE_CONTACT['id']}", headers=headers)
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_delete_contact_success():
    mock_sb = MagicMock()
    deleted = {**FAKE_CONTACT, "is_active": False}
    
    class DeleteFluentChain:
        def __init__(self):
            self._is_delete = False
            
        def update(self, *a, **kw):
            self._is_delete = True
            return self
            
        def __getattr__(self, name):
            if name == "execute":
                return self.execute
            return lambda *a, **kw: self
            
        def execute(self):
            resp = MagicMock()
            if self._is_delete:
                resp.data = [deleted]
            else:
                resp.data = [FAKE_CONTACT]
            return resp

    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_ADMIN)
        if name == "contacts":
            return DeleteFluentChain()
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    with patch("app.core.auth.get_supabase", return_value=mock_sb), \
         patch("app.api.endpoints.contacts.get_supabase", return_value=mock_sb):
        headers = {"X-User-Id": FAKE_ADMIN["id"]}
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.delete(f"/api/v1/contacts/{FAKE_CONTACT['id']}", headers=headers)
            
    assert response.status_code == 200
    data = response.json()
    assert data["is_active"] is False
