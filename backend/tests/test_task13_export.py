"""
Task 13 — Tests for HubSpot-compatible CSV export endpoints, notes generation, and permissions.
"""
from __future__ import annotations
import csv
import io
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

FAKE_CONTACTS = [
    {
        "id": "c1",
        "hospital_id": FAKE_HOSPITAL["id"],
        "full_name": "Jane Smith",
        "role": "Director of RCM",
        "prior_employer": "Mount Sinai",
        "linkedin_url": "https://linkedin.com/in/janesmith",
        "linkedin_verified": True,
        "is_active": True,
        "hospitals": {
            "name": FAKE_HOSPITAL["name"],
            "website_url": FAKE_HOSPITAL["website_url"]
        }
    },
    {
        "id": "c2",
        "hospital_id": FAKE_HOSPITAL["id"],
        "full_name": "John Jacob Astor",
        "role": "Analyst",
        "prior_employer": None,
        "linkedin_url": "https://linkedin.com/in/johnastor",
        "linkedin_verified": False,
        "is_active": True,
        "hospitals": {
            "name": FAKE_HOSPITAL["name"],
            "website_url": FAKE_HOSPITAL["website_url"]
        }
    }
]


@pytest.fixture(autouse=True)
def clear_settings_cache():
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


# ===========================================================================
# CSV Export Permission and Filter Tests
# ===========================================================================

@pytest.mark.asyncio
async def test_export_csv_requires_auth():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        res = await client.get("/api/v1/export/csv")
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_export_csv_ae_denied_another():
    mock_sb = MagicMock()
    mock_sb.table.return_value = FluentChain(FAKE_AE)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.core.auth.get_supabase", return_value=mock_sb):
            res = await client.get(
                f"/api/v1/export/csv?ae_id={OTHER_AE_ID}",
                headers={"X-User-Id": FAKE_AE["id"]}
            )
            assert res.status_code == 403


@pytest.mark.asyncio
async def test_export_csv_ae_denied_hospital():
    mock_sb = MagicMock()
    
    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"]}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.core.auth.get_supabase", return_value=mock_sb), \
             patch("app.api.endpoints.export.get_supabase", return_value=mock_sb):
            res = await client.get(
                f"/api/v1/export/csv?hospital_id={OTHER_HOSP_ID}",
                headers={"X-User-Id": FAKE_AE["id"]}
            )
            assert res.status_code == 403


@pytest.mark.asyncio
async def test_export_csv_ae_success():
    mock_sb = MagicMock()

    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"]}])
        if name == "contacts":
            return FluentChain(FAKE_CONTACTS)
        if name == "signals":
            return FluentChain([{"summary": "restructuring"}, {"summary": "hiring RCM"}])
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.core.auth.get_supabase", return_value=mock_sb), \
             patch("app.api.endpoints.export.get_supabase", return_value=mock_sb):
            res = await client.get(
                "/api/v1/export/csv",
                headers={"X-User-Id": FAKE_AE["id"]}
            )
            assert res.status_code == 200
            assert res.headers["Content-Disposition"] == "attachment; filename=contacts_export.csv"
            assert res.headers["Content-Type"].startswith("text/csv")
            
            # Read CSV content
            csv_data = list(csv.reader(io.StringIO(res.text)))
            assert len(csv_data) == 3  # Header + 2 rows
            assert csv_data[0] == [
                "First Name",
                "Last Name",
                "Job Title",
                "Company Name",
                "Website URL",
                "LinkedIn Biodata URL",
                "Notes"
            ]
            
            # First row check (verified LinkedIn, split name, recent signals included)
            assert csv_data[1][0] == "Jane"
            assert csv_data[1][1] == "Smith"
            assert csv_data[1][2] == "Director of RCM"
            assert csv_data[1][3] == FAKE_HOSPITAL["name"]
            assert csv_data[1][4] == FAKE_HOSPITAL["website_url"]
            assert csv_data[1][5] == "https://linkedin.com/in/janesmith"
            assert "Prior employer: Mount Sinai." in csv_data[1][6]
            assert "Recent signals: restructuring; hiring RCM" in csv_data[1][6]

            # Second row check (unverified LinkedIn -> blank, name split Jacob Astor)
            assert csv_data[2][0] == "John"
            assert csv_data[2][1] == "Jacob Astor"
            assert csv_data[2][5] == ""
            assert "Prior employer: ." in csv_data[2][6]


@pytest.mark.asyncio
async def test_export_csv_without_signals():
    mock_sb = MagicMock()

    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"]}])
        if name == "contacts":
            return FluentChain(FAKE_CONTACTS)
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.core.auth.get_supabase", return_value=mock_sb), \
             patch("app.api.endpoints.export.get_supabase", return_value=mock_sb):
            res = await client.get(
                "/api/v1/export/csv?include_signals=false",
                headers={"X-User-Id": FAKE_AE["id"]}
            )
            assert res.status_code == 200
            csv_data = list(csv.reader(io.StringIO(res.text)))
            
            # Verify recent signals segment is omitted
            assert csv_data[1][6] == "Prior employer: Mount Sinai."
            assert csv_data[2][6] == "Prior employer: ."


@pytest.mark.asyncio
async def test_contacts_count_endpoint():
    mock_sb = MagicMock()

    def table_side(name):
        if name == "ae_users":
            return FluentChain(FAKE_AE)
        if name == "hospital_ae_assignments":
            return FluentChain([{"hospital_id": FAKE_HOSPITAL["id"]}])
        if name == "contacts":
            return FluentChain([], count=10)
        return FluentChain([])

    mock_sb.table.side_effect = table_side

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.core.auth.get_supabase", return_value=mock_sb), \
             patch("app.api.endpoints.export.get_supabase", return_value=mock_sb):
            res = await client.get(
                "/api/v1/export/contacts-count",
                headers={"X-User-Id": FAKE_AE["id"]}
            )
            assert res.status_code == 200
            data = res.json()
            assert data["count"] == 10
