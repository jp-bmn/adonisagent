"""
Task 3 — Tests for hospital and signal API endpoints.

Strategy: patch get_supabase at the source (app.core.database) with autouse
so the lru_cache singleton is bypassed for every test. Individual tests
configure the mock's table() side_effect to return FluentChain objects.
"""
from __future__ import annotations
import os
import pytest
from unittest.mock import MagicMock, patch
from httpx import AsyncClient, ASGITransport

# ------------------------------------------------------------------
# Env setup — must happen before app is imported
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# Fake data
# ------------------------------------------------------------------

FAKE_HOSPITAL_NYP = {
    "id":           "11111111-1111-1111-1111-111111111111",
    "name":         "NewYork-Presbyterian",
    "website_url":  "https://nyp.org",
    "division_note": None,
    "created_at":   "2026-01-01T00:00:00+00:00",
}
FAKE_HOSPITAL_UMASS = {
    "id":           "22222222-2222-2222-2222-222222222222",
    "name":         "UMass Memorial",
    "website_url":  "https://umassmemorial.org",
    "division_note": None,
    "created_at":   "2026-01-01T00:00:00+00:00",
}
FAKE_USER_ADMIN = {
    "id":            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "name":          "Danielle Ferdon",
    "slack_user_id": "PLACEHOLDER_DANIELLE",
    "is_admin":      True,
    "created_at":    "2026-01-01T00:00:00+00:00",
}
FAKE_USER_AE = {
    "id":            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "name":          "Michael",
    "slack_user_id": "PLACEHOLDER_MICHAEL",
    "is_admin":      False,
    "created_at":    "2026-01-01T00:00:00+00:00",
}
FAKE_SIGNAL = {
    "id":                "cccccccc-cccc-cccc-cccc-cccccccccccc",
    "hospital_id":       FAKE_HOSPITAL_NYP["id"],
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
    "included_in_digest": False,
    "urgent_sent":        False,
}
FAKE_PENDING_SIGNAL = {
    **FAKE_SIGNAL,
    "id":               "dddddddd-dddd-dddd-dddd-dddddddddddd",
    "confidence_score": 0.55,
    "review_status":    "pending",
    "hospitals":        {"name": "NewYork-Presbyterian"},
}


# ------------------------------------------------------------------
# FluentChain — chainable Supabase query builder mock
# ------------------------------------------------------------------

class _Response:
    def __init__(self, data, count=None):
        self.data = data
        self.count = count if count is not None else (len(data) if isinstance(data, list) else 0)


class FluentChain:
    """
    Supports arbitrary chaining: .select().eq().order().limit().execute()
    Every method returns self except execute() which returns the _Response.
    """
    def __init__(self, data, count=None):
        self._resp = _Response(data, count)

    def __getattr__(self, name):
        if name == "execute":
            return lambda: self._resp
        return lambda *a, **kw: self

    def execute(self):
        return self._resp


def chain(data, count=None) -> FluentChain:
    return FluentChain(data, count)


# ------------------------------------------------------------------
# Shared supabase mock fixture (autouse per test)
# ------------------------------------------------------------------

@pytest.fixture
def supabase_mock():
    """
    Provides a fresh MagicMock Supabase client for each test.
    Patches get_supabase everywhere it's used so lru_cache is bypassed.
    """
    mock = MagicMock()
    with patch("app.core.database.get_supabase", return_value=mock), \
         patch("app.core.auth.get_supabase", return_value=mock), \
         patch("app.api.endpoints.hospitals.get_supabase", return_value=mock), \
         patch("app.api.endpoints.signals.get_supabase", return_value=mock):
        yield mock


def make_user_table(user_data):
    """
    Returns a FluentChain that handles the auth user lookup:
    supabase.table("ae_users").select("*").eq("id", ...).single().execute()
    """
    return chain(user_data)


# ------------------------------------------------------------------
# Helper: authenticated async client
# ------------------------------------------------------------------

async def authed_client(user: dict):
    return AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        headers={"X-User-Id": user["id"]},
    )


# ==================================================================
# GET /api/v1/hospitals
# ==================================================================

@pytest.mark.asyncio
async def test_list_hospitals_returns_hospitals_with_aes(supabase_mock):
    """GET /hospitals returns hospitals joined with their AE assignments."""
    hospitals_data  = [FAKE_HOSPITAL_NYP, FAKE_HOSPITAL_UMASS]
    assignments_data = [{
        "hospital_id": FAKE_HOSPITAL_NYP["id"],
        "ae_id":       FAKE_USER_AE["id"],
        "ae_users":    {"id": FAKE_USER_AE["id"], "name": "Michael", "is_admin": False},
    }]

    def table_side_effect(name):
        if name == "hospitals":            return chain(hospitals_data)
        if name == "hospital_ae_assignments": return chain(assignments_data)
        if name == "ae_users":             return make_user_table(FAKE_USER_ADMIN)
        return chain([])

    supabase_mock.table.side_effect = table_side_effect

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.get("/api/v1/hospitals")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    nyp = next(h for h in data if h["name"] == "NewYork-Presbyterian")
    assert len(nyp["ae_users"]) == 1
    assert nyp["ae_users"][0]["name"] == "Michael"


@pytest.mark.asyncio
async def test_list_hospitals_requires_auth():
    """GET /hospitals without X-User-Id returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/hospitals")
    assert response.status_code == 401


# ==================================================================
# GET /api/v1/hospitals/{id}/signals
# ==================================================================

@pytest.mark.asyncio
async def test_get_hospital_signals_returns_list(supabase_mock):
    """GET /hospitals/{id}/signals returns the signal list."""
    def table_side_effect(name):
        if name == "hospitals": return chain(FAKE_HOSPITAL_NYP)
        if name == "signals":   return chain([FAKE_SIGNAL])
        if name == "ae_users":  return make_user_table(FAKE_USER_ADMIN)
        return chain([])

    supabase_mock.table.side_effect = table_side_effect

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.get(f"/api/v1/hospitals/{FAKE_HOSPITAL_NYP['id']}/signals")

    assert response.status_code == 200
    assert response.json()[0]["signal_type"] == "leadership_change"


@pytest.mark.asyncio
async def test_get_hospital_signals_unknown_hospital_returns_404(supabase_mock):
    """GET /hospitals/{unknown}/signals returns 404."""
    not_found = chain(None)

    def table_side_effect(name):
        if name == "hospitals": return not_found
        if name == "ae_users":  return make_user_table(FAKE_USER_ADMIN)
        return chain([])

    supabase_mock.table.side_effect = table_side_effect

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.get("/api/v1/hospitals/00000000-0000-0000-0000-000000000000/signals")

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_hospital_signals_invalid_tier_returns_422(supabase_mock):
    """GET /hospitals/{id}/signals?tier=invalid returns 422."""
    def table_side_effect(name):
        if name == "hospitals": return chain(FAKE_HOSPITAL_NYP)
        if name == "ae_users":  return make_user_table(FAKE_USER_ADMIN)
        return chain([])

    supabase_mock.table.side_effect = table_side_effect

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.get(
            f"/api/v1/hospitals/{FAKE_HOSPITAL_NYP['id']}/signals?tier=invalid_tier"
        )

    assert response.status_code == 422


# ==================================================================
# GET /api/v1/signals
# ==================================================================

@pytest.mark.asyncio
async def test_list_signals_returns_all(supabase_mock):
    """GET /signals returns signals (dismissed excluded by default)."""
    def table_side_effect(name):
        if name == "signals":  return chain([FAKE_SIGNAL])
        if name == "ae_users": return make_user_table(FAKE_USER_ADMIN)
        return chain([])

    supabase_mock.table.side_effect = table_side_effect

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.get("/api/v1/signals")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_list_signals_requires_auth():
    """GET /signals without X-User-Id returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/signals")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_signals_invalid_tier_returns_422(supabase_mock):
    """GET /signals?tier=bad returns 422."""
    supabase_mock.table.return_value = make_user_table(FAKE_USER_ADMIN)

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.get("/api/v1/signals?tier=bad")

    assert response.status_code == 422


# ==================================================================
# POST /api/v1/signals
# ==================================================================

@pytest.mark.asyncio
async def test_create_signal_high_confidence_no_review(supabase_mock):
    """POST /signals confidence >= 0.70 → review_status is null."""
    inserted = {**FAKE_SIGNAL, "review_status": None, "confidence_score": 0.95}

    def table_side_effect(name):
        if name == "hospitals": return chain(FAKE_HOSPITAL_NYP)
        if name == "signals":   return chain([inserted])
        if name == "ae_users":  return make_user_table(FAKE_USER_ADMIN)
        return chain([])

    supabase_mock.table.side_effect = table_side_effect

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.post("/api/v1/signals", json={
            "hospital_id":      FAKE_HOSPITAL_NYP["id"],
            "signal_type":      "leadership_change",
            "tier":             "urgent",
            "confidence_score": 0.95,
            "title":            "CRO departs NYP",
            "summary":          "Chief Revenue Officer leaves.",
            "source_url":       "https://example.com/article",
            "source_name":      "Modern Healthcare",
        })

    assert response.status_code == 201
    assert response.json()["review_status"] is None


@pytest.mark.asyncio
async def test_create_signal_low_confidence_sets_pending(supabase_mock):
    """POST /signals confidence < 0.70 → review_status = 'pending'."""
    inserted = {**FAKE_SIGNAL, "review_status": "pending", "confidence_score": 0.55}

    def table_side_effect(name):
        if name == "hospitals": return chain(FAKE_HOSPITAL_NYP)
        if name == "signals":   return chain([inserted])
        if name == "ae_users":  return make_user_table(FAKE_USER_ADMIN)
        return chain([])

    supabase_mock.table.side_effect = table_side_effect

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.post("/api/v1/signals", json={
            "hospital_id":      FAKE_HOSPITAL_NYP["id"],
            "signal_type":      "financial_event",
            "tier":             "worth_knowing",
            "confidence_score": 0.55,
            "title":            "NYP Q3 results",
            "summary":          "Q3 earnings reported.",
        })

    assert response.status_code == 201
    assert response.json()["review_status"] == "pending"


@pytest.mark.asyncio
async def test_create_signal_invalid_type_returns_422(supabase_mock):
    """POST /signals with invalid signal_type returns 422."""
    supabase_mock.table.return_value = make_user_table(FAKE_USER_ADMIN)

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.post("/api/v1/signals", json={
            "hospital_id":      FAKE_HOSPITAL_NYP["id"],
            "signal_type":      "not_a_real_type",
            "tier":             "urgent",
            "confidence_score": 0.9,
        })

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_signal_invalid_tier_returns_422(supabase_mock):
    """POST /signals with invalid tier returns 422."""
    supabase_mock.table.return_value = make_user_table(FAKE_USER_ADMIN)

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.post("/api/v1/signals", json={
            "hospital_id":      FAKE_HOSPITAL_NYP["id"],
            "signal_type":      "leadership_change",
            "tier":             "high",
            "confidence_score": 0.9,
        })

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_signal_unknown_hospital_returns_404(supabase_mock):
    """POST /signals with non-existent hospital_id returns 404."""
    def table_side_effect(name):
        if name == "hospitals": return chain(None)
        if name == "ae_users":  return make_user_table(FAKE_USER_ADMIN)
        return chain([])

    supabase_mock.table.side_effect = table_side_effect

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.post("/api/v1/signals", json={
            "hospital_id":      "00000000-0000-0000-0000-000000000000",
            "signal_type":      "leadership_change",
            "tier":             "urgent",
            "confidence_score": 0.9,
        })

    assert response.status_code == 404


# ==================================================================
# GET /api/v1/signals/pending-review
# ==================================================================

@pytest.mark.asyncio
async def test_pending_review_returns_lowest_confidence_first(supabase_mock):
    """GET /signals/pending-review returns signals ordered confidence ASC."""
    signal_a = {**FAKE_PENDING_SIGNAL, "id": "aaaa0001-0000-0000-0000-000000000000", "confidence_score": 0.30}
    signal_b = {**FAKE_PENDING_SIGNAL, "id": "bbbb0002-0000-0000-0000-000000000000", "confidence_score": 0.55}

    def table_side_effect(name):
        if name == "signals":  return chain([signal_a, signal_b])
        if name == "ae_users": return make_user_table(FAKE_USER_ADMIN)
        return chain([])

    supabase_mock.table.side_effect = table_side_effect

    async with await authed_client(FAKE_USER_ADMIN) as client:
        response = await client.get("/api/v1/signals/pending-review")

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["confidence_score"] < data[1]["confidence_score"]


@pytest.mark.asyncio
async def test_pending_review_requires_auth():
    """GET /signals/pending-review without auth returns 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/signals/pending-review")
    assert response.status_code == 401
