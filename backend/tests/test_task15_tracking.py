"""
Task 15 — Tests for UTM tracking, digest view logging/upserting, and engagement analytics.
"""
from __future__ import annotations
import os
import pytest
import uuid
from datetime import datetime, timezone, timedelta
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
from app.services.slack_service import format_weekly_digest
from app.services.digest_service import send_weekly_digest_to_all_aes


class FluentTableMock:
    """Supports mock chaining: .select().eq().execute(), plus insert/update simulation"""
    def __init__(self, table_name, db_data):
        self.table_name = table_name
        self.db_data = db_data  # List of dictionaries
        self._filters = []
        self._order = None
        self._limit = None
        self._is_single = False
        self._is_insert = False
        self._is_update = False
        self._insert_res = []
        self._update_payload = {}

    def select(self, *args, **kwargs):
        return self

    def eq(self, field, value):
        self._filters.append(("eq", field, value))
        return self

    def neq(self, field, value):
        self._filters.append(("neq", field, value))
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

    def single(self):
        self._is_single = True
        return self

    def insert(self, payload):
        self._is_insert = True
        if isinstance(payload, dict):
            new_row = {**payload}
            if "id" not in new_row:
                new_row["id"] = str(uuid.uuid4())
            self.db_data.append(new_row)
            self._insert_res = [new_row]
        elif isinstance(payload, list):
            self._insert_res = []
            for p in payload:
                new_row = {**p}
                if "id" not in new_row:
                    new_row["id"] = str(uuid.uuid4())
                self.db_data.append(new_row)
                self._insert_res.append(new_row)
        return self

    def update(self, payload):
        self._is_update = True
        self._update_payload = payload
        return self

    def execute(self):
        if self._is_insert:
            resp = MagicMock()
            resp.data = self._insert_res
            resp.count = len(self._insert_res)
            return resp

        if self._is_update:
            filtered = list(self.db_data)
            for op, field, val in self._filters:
                if op == "eq":
                    filtered = [r for r in filtered if r.get(field) == val]
                elif op == "in":
                    filtered = [r for r in filtered if r.get(field) in val]
            
            for row in filtered:
                row.update(self._update_payload)
            
            resp = MagicMock()
            resp.data = filtered
            resp.count = len(filtered)
            return resp

        # Filter standard select
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

        # Order
        if self._order:
            field, desc = self._order
            filtered.sort(key=lambda x: str(x.get(field) or ""), reverse=desc)

        # Limit
        if self._limit:
            filtered = filtered[:self._limit]

        resp = MagicMock()
        if self._is_single:
            resp.data = filtered[0] if filtered else None
        else:
            resp.data = filtered
        resp.count = len(filtered)
        return resp


FAKE_AE = {
    "id":            "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
    "name":          "Michael",
    "slack_user_id": "PLACEHOLDER_MICHAEL",
    "is_admin":      False,
    "created_at":    "2026-05-20T10:00:00+00:00"
}

FAKE_ADMIN = {
    "id":            "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
    "name":          "Danielle",
    "slack_user_id": "PLACEHOLDER_DANIELLE",
    "is_admin":      True,
    "created_at":    "2026-05-20T10:00:00+00:00"
}

FAKE_SIGNAL = {
    "id": "sig-001",
    "hospital_id": "hosp-001",
    "tier": "worth_knowing",
    "title": "Vendor change at NYP",
    "summary": "New EHR system signed.",
    "source_url": "https://example.com/article",
    "source_name": "Modern Healthcare",
    "published_date": "2026-05-20",
    "included_in_digest": False
}


# ===========================================================================
# UTM tracking formatting unit tests
# ===========================================================================

def test_format_weekly_digest_utm_tracking():
    # 1. No digest_id
    fallback_text, blocks = format_weekly_digest(
        ae_user=FAKE_AE,
        signals=[FAKE_SIGNAL],
        week_label="June 2–6",
        dashboard_url="https://dashboard.adonis.com/feed"
    )
    button_block = [b for b in blocks if b.get("type") == "actions"][0]
    button_url = button_block["elements"][0]["url"]
    assert button_url == "https://dashboard.adonis.com/feed"

    # 2. With digest_id
    d_id = "11111111-1111-1111-1111-111111111111"
    fallback_text, blocks = format_weekly_digest(
        ae_user=FAKE_AE,
        signals=[FAKE_SIGNAL],
        week_label="June 2–6",
        dashboard_url="https://dashboard.adonis.com/feed",
        digest_id=d_id
    )
    button_block = [b for b in blocks if b.get("type") == "actions"][0]
    button_url = button_block["elements"][0]["url"]
    expected_param = f"digest_id={d_id}&ae_id={FAKE_AE['id']}&utm_source=slack&utm_medium=digest"
    assert expected_param in button_url
    assert button_url.startswith("https://dashboard.adonis.com/feed?")


# ===========================================================================
# Digest sending logic unit tests
# ===========================================================================

@pytest.mark.asyncio
async def test_send_weekly_digest_generates_uuid():
    mock_digests_table = MagicMock()
    mock_digests_table.insert.return_value.execute.return_value.data = [{
        "id": "temp-digest-id",
        "ae_id": FAKE_AE["id"],
        "sent_at": "2026-06-06T10:00:00+00:00"
    }]

    def table_side(name):
        if name == "ae_users":
            return FluentTableMock(name, [FAKE_AE])
        if name == "hospital_ae_assignments":
            return FluentTableMock(name, [{"hospital_id": "hosp-001", "ae_id": FAKE_AE["id"]}])
        if name == "signals":
            return FluentTableMock(name, [FAKE_SIGNAL])
        if name == "digests":
            return mock_digests_table
        return FluentTableMock(name, [])

    mock_sb = MagicMock()
    mock_sb.table.side_effect = table_side

    with patch("app.services.digest_service.get_supabase", return_value=mock_sb), \
         patch("app.services.digest_service.format_weekly_digest", return_value=("fallback", [])) as mock_format, \
         patch("app.services.digest_service.send_dm", return_value={"ts": "slack-ts-123"}):
        
        res = await send_weekly_digest_to_all_aes()
        
        assert mock_format.call_count == 1
        args, kwargs = mock_format.call_args
        digest_id = kwargs.get("digest_id")
        assert digest_id is not None
        assert uuid.UUID(digest_id)

        # Verify insert got the generated UUID
        insert_args = mock_digests_table.insert.call_args[0][0]
        assert insert_args["id"] == digest_id


# ===========================================================================
# POST /digest-view endpoint integration tests
# ===========================================================================

@pytest.mark.asyncio
async def test_record_digest_view_invalid_uuid():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/digest-view",
            json={
                "digest_id": "not-a-uuid",
                "ae_id": str(uuid.uuid4()),
                "utm_source": "slack"
            }
        )
        assert response.status_code == 200
        assert response.json() == {"recorded": False}

        response = await client.post(
            "/api/v1/digest-view",
            json={
                "ae_id": str(uuid.uuid4()),
                "utm_source": "slack"
            }
        )
        assert response.status_code == 200
        assert response.json() == {"recorded": False}


@pytest.mark.asyncio
async def test_record_digest_view_nonexistent_digest():
    db = {"digests": []}
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: FluentTableMock(name, db.get(name, []))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.views.get_supabase", return_value=mock_sb):
            response = await client.post(
                "/api/v1/digest-view",
                json={
                    "digest_id": str(uuid.uuid4()),
                    "ae_id": str(uuid.uuid4()),
                    "utm_source": "slack"
                }
            )
            assert response.status_code == 200
            assert response.json() == {"recorded": False}


@pytest.mark.asyncio
async def test_record_digest_view_success_new_and_upsert():
    digest_uuid = str(uuid.uuid4())
    ae_uuid = str(uuid.uuid4())

    db = {
        "digests": [{"id": digest_uuid}],
        "ae_users": [{"id": ae_uuid}],
        "digest_views": []
    }
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: FluentTableMock(name, db.get(name, []))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.views.get_supabase", return_value=mock_sb):
            # 1. New View
            response = await client.post(
                "/api/v1/digest-view",
                json={
                    "digest_id": digest_uuid,
                    "ae_id": ae_uuid,
                    "utm_source": "slack"
                }
            )
            assert response.status_code == 200
            assert response.json() == {"recorded": True}
            assert len(db["digest_views"]) == 1
            assert db["digest_views"][0]["digest_id"] == digest_uuid
            assert db["digest_views"][0]["ae_id"] == ae_uuid

            # 2. View Upsert/Update
            response = await client.post(
                "/api/v1/digest-view",
                json={
                    "digest_id": digest_uuid,
                    "ae_id": ae_uuid,
                    "utm_source": "slack-updated"
                }
            )
            assert response.status_code == 200
            assert response.json() == {"recorded": True}
            assert len(db["digest_views"]) == 1  # Deduplicated!
            assert db["digest_views"][0]["utm_source"] == "slack-updated"


# ===========================================================================
# GET /ae-users last_viewed_digest tests
# ===========================================================================

@pytest.mark.asyncio
async def test_get_ae_users_last_viewed_digest():
    db = {
        "ae_users": [FAKE_ADMIN, FAKE_AE],
        "hospital_ae_assignments": [],
        "signals": [],
        "digest_views": [
            {
                "id": "v-1",
                "ae_id": FAKE_AE["id"],
                "viewed_at": "2026-06-06T15:00:00+00:00"
            }
        ]
    }
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: FluentTableMock(name, db.get(name, []))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.users.get_supabase", return_value=mock_sb), \
             patch("app.core.auth.get_supabase", return_value=mock_sb):
            
            headers = {"X-User-Id": FAKE_ADMIN["id"]}
            response = await client.get("/api/v1/ae-users", headers=headers)
            assert response.status_code == 200
            users_list = response.json()
            assert len(users_list) == 1
            assert users_list[0]["last_viewed_digest"].replace("+00:00", "Z") == "2026-06-06T15:00:00Z"


# ===========================================================================
# GET /digest-analytics metrics tests
# ===========================================================================

@pytest.mark.asyncio
async def test_get_digest_analytics():
    digest_sent_time = "2026-06-06T12:00:00+00:00"
    digest_view_time = "2026-06-06T12:30:00+00:00"

    db = {
        "ae_users": [FAKE_ADMIN, FAKE_AE],
        "digests": [
            {
                "id": "d-123",
                "ae_id": FAKE_AE["id"],
                "sent_at": digest_sent_time,
                "week_start": "2026-06-01",
                "week_end": "2026-06-07",
                "ae_users": {
                    "name": FAKE_AE["name"]
                }
            }
        ],
        "digest_views": [
            {
                "id": "v-123",
                "digest_id": "d-123",
                "ae_id": FAKE_AE["id"],
                "viewed_at": digest_view_time,
                "utm_source": "slack"
            }
        ]
    }
    mock_sb = MagicMock()
    mock_sb.table.side_effect = lambda name: FluentTableMock(name, db.get(name, []))

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        with patch("app.api.endpoints.users.get_supabase", return_value=mock_sb), \
             patch("app.core.auth.get_supabase", return_value=mock_sb):
            
            headers = {"X-User-Id": FAKE_ADMIN["id"]}
            response = await client.get("/api/v1/digest-analytics", headers=headers)
            assert response.status_code == 200
            analytics = response.json()
            assert len(analytics) == 1
            item = analytics[0]
            assert item["digest_id"] == "d-123"
            assert item["ae_name"] == FAKE_AE["name"]
            assert item["opened"] is True
            assert item["view_count"] == 1
            assert item["first_viewed_at"] == digest_view_time
            assert abs(item["time_to_open_minutes"] - 30.0) < 0.01
