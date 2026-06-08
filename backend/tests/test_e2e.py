"""
Task 18 — End-to-end integration test suite.
Contains test_rules_engine_coverage() (unit/local) and test_full_pipeline() (integration).
"""
from __future__ import annotations
import os
import uuid
import pytest
import asyncio
from dotenv import load_dotenv
from httpx import AsyncClient, ASGITransport

# Force load real settings from .env file before importing FastAPI app
# This overrides any placeholder values in os.environ set by other tests during full test suite runs.
load_dotenv(override=True)

from app.main import app
from app.core.config import get_settings
from app.core.database import get_supabase
from app.services.rules_engine import classify_with_rules


def has_real_keys() -> bool:
    """Check if we have real API credentials to run the integration pipeline."""
    url = os.environ.get("SUPABASE_URL", "")
    key = os.environ.get("SUPABASE_KEY", "")
    anthropic = os.environ.get("ANTHROPIC_API_KEY", "")

    if not url or "test.supabase.co" in url or "placeholder" in url.lower():
        return False
    if not key or "test-key" in key or "placeholder" in key.lower():
        return False
    if not anthropic or "test-anthropic" in anthropic or "placeholder" in anthropic.lower():
        return False
    return True


# ===========================================================================
# Rules Engine Coverage Tests
# ===========================================================================

def test_rules_engine_coverage():
    """Verify that all 8 deterministic rules match correct headlines, and guards fire."""
    
    # 1. leadership_change
    res1 = classify_with_rules(
        title="John Smith appointed Chief Revenue Officer",
        text="He will oversee the financial recovery of the health system."
    )
    assert res1.matched is True
    assert res1.signal_type == "leadership_change"
    assert res1.tier == "urgent"
    assert res1.rule_name == "leadership_change"

    # Negative guard cro croissant
    res1_neg = classify_with_rules(
        title="We are serving cro croissant in the cafeteria today",
        text="Breakfast menu update."
    )
    assert res1_neg.matched is False

    # 2. post_golive_friction
    res2 = classify_with_rules(
        title="Hospital billing problems follow EMR implementation",
        text="Physicians are frustrated with the post go-live claims delays."
    )
    assert res2.matched is True
    assert res2.signal_type == "post_golive_friction"
    assert res2.tier == "urgent"
    assert res2.rule_name == "post_golive_friction"

    # 3. epic_go_live
    res3 = classify_with_rules(
        title="Community Health launches new Epic EMR cutover",
        text="The new electronic health record system went live today."
    )
    assert res3.matched is True
    assert res3.signal_type == "epic_go_live"
    assert res3.tier == "urgent"
    assert res3.rule_name == "epic_go_live"

    # 4. ma_acquisition
    res4 = classify_with_rules(
        title="Ascension completes acquisition of local clinic network",
        text="The merger will expand their regional operations."
    )
    assert res4.matched is True
    assert res4.signal_type == "ma_acquisition"
    assert res4.tier == "urgent"
    assert res4.rule_name == "ma_acquisition"

    # Negative guards: talent/customer acquisition
    res4_neg1 = classify_with_rules(title="Director of Talent Acquisition joins network")
    assert res4_neg1.matched is False

    res4_neg2 = classify_with_rules(title="Marketing focus on customer acquisition models")
    assert res4_neg2.matched is False

    # 5. restructuring
    res5 = classify_with_rules(
        title="Staff layoffs announced due to deficit",
        text="The workforce reduction will trim department headcount."
    )
    assert res5.matched is True
    assert res5.signal_type == "restructuring"
    assert res5.tier == "urgent"
    assert res5.rule_name == "restructuring"

    # Negative guard: restructuring debt
    res5_neg = classify_with_rules(title="Ascension restructuring loan debt and bonds")
    assert res5_neg.matched is False

    # 6. rcm_hiring_spike
    res6 = classify_with_rules(
        title="Hospital is recruiting billing specialists and coders",
        text="Multiple open positions in the revenue cycle management department."
    )
    assert res6.matched is True
    assert res6.signal_type == "rcm_hiring_spike"
    assert res6.tier == "worth_knowing"
    assert res6.rule_name == "rcm_hiring_spike"

    # 7. vendor_change
    res7 = classify_with_rules(
        title="Health network selects new vendor for software",
        text="They chose to switch platforms for claim scrubbing."
    )
    assert res7.matched is True
    assert res7.signal_type == "vendor_change"
    assert res7.tier == "worth_knowing"
    assert res7.rule_name == "vendor_change"

    # 8. financial_event
    res8 = classify_with_rules(
        title="Regional healthcare unit posts annual operating deficit",
        text="The net loss is attributed to declining revenue."
    )
    assert res8.matched is True
    assert res8.signal_type == "financial_event"
    assert res8.tier == "worth_knowing"
    assert res8.rule_name == "financial_event"


# ===========================================================================
# End-to-End Pipeline Integration Test
# ===========================================================================

@pytest.mark.integration
@pytest.mark.skipif(not has_real_keys(), reason="Missing real credentials in .env")
@pytest.mark.asyncio
async def test_full_pipeline():
    """Verify the entire end-to-end Adonis pipeline on the live DB."""
    
    settings = get_settings()
    supabase = get_supabase()

    # Track created records for cleanup
    created_signals = []
    created_digests = []
    created_runs = []

    # Verify seed data exists
    # 0. Retrieve users and NYP hospital from Supabase
    hosp_res = supabase.table("hospitals").select("id").eq("name", "NewYork-Presbyterian").execute()
    assert hosp_res.data, "Seed hospital 'NewYork-Presbyterian' must exist in DB."
    nyp_id = hosp_res.data[0]["id"]

    ae_res = supabase.table("ae_users").select("id, is_admin").execute()
    assert len(ae_res.data) >= 2, "Must have seeded users (Danielle admin and AEs)."
    
    admin_users = [u for u in ae_res.data if u["is_admin"]]
    ae_users = [u for u in ae_res.data if not u["is_admin"]]
    
    assert admin_users, "Seeded admin user (Danielle) must exist in DB."
    assert ae_users, "Seeded AEs (Michael/David/Jeff) must exist in DB."

    admin_id = admin_users[0]["id"]
    ae_id = ae_users[0]["id"]  # E.g., Michael
    
    admin_headers = {"X-User-Id": admin_id}
    ae_headers = {"X-User-Id": ae_id}
    internal_headers = {"X-API-Key": settings.internal_api_key}

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            
            # 1. Classification (Rules Engine)
            # POST /api/v1/classify with NYP CRO departure text
            classify_payload1 = {
                "article_text": "NewYork-Presbyterian announces Chief Revenue Officer John Smith departs health system.",
                "hospital_name": "NewYork-Presbyterian",
                "source_name": "Modern Healthcare"
            }
            res_class1 = await client.post("/api/v1/classify", json=classify_payload1)
            assert res_class1.status_code == 200
            data_class1 = res_class1.json()
            assert data_class1["tier"] == "urgent"
            assert data_class1["classification_source"] == "rules_engine"
            assert data_class1["signal_type"] == "leadership_change"

            # Create signal in DB
            signal_payload1 = {
                "hospital_id": nyp_id,
                "signal_type": data_class1["signal_type"],
                "tier": data_class1["tier"],
                "confidence_score": data_class1["confidence_score"],
                "title": data_class1["title"],
                "summary": data_class1["summary"],
                "source_name": "Modern Healthcare",
                "source_url": "https://example.com/e2e-nyp-cro-departure"
            }
            res_sig1 = await client.post("/api/v1/signals", json=signal_payload1, headers=admin_headers)
            assert res_sig1.status_code == 201
            sig1 = res_sig1.json()
            created_signals.append(sig1["id"])

            # 2. Confirm urgent_sent becomes True (poll background task alert)
            urgent_sent = False
            for _ in range(10):  # up to 20 seconds
                await asyncio.sleep(2)
                check_res = supabase.table("signals").select("urgent_sent").eq("id", sig1["id"]).execute()
                if check_res.data and check_res.data[0]["urgent_sent"]:
                    urgent_sent = True
                    break
            assert urgent_sent is True, "Background task failed to flag signal as urgent_sent=True"

            # 3. Classification (Claude)
            # POST /api/v1/classify with financial event that triggers negative guards (forcing Claude path)
            classify_payload2 = {
                "article_text": "NewYork-Presbyterian announced a restructuring of its bond debt today.",
                "hospital_name": "NewYork-Presbyterian",
                "source_name": "Modern Healthcare"
            }
            res_class2 = await client.post("/api/v1/classify", json=classify_payload2)
            assert res_class2.status_code == 200
            data_class2 = res_class2.json()
            assert data_class2["classification_source"] == "claude_api"
            assert data_class2["tier"] == "worth_knowing"
            assert data_class2["signal_type"] == "financial_event"

            # Create signal in DB
            signal_payload2 = {
                "hospital_id": nyp_id,
                "signal_type": data_class2["signal_type"],
                "tier": data_class2["tier"],
                "confidence_score": data_class2["confidence_score"],
                "title": data_class2["title"],
                "summary": data_class2["summary"],
                "source_name": "Modern Healthcare",
                "source_url": "https://example.com/e2e-nyp-financial-event"
            }
            res_sig2 = await client.post("/api/v1/signals", json=signal_payload2, headers=admin_headers)
            assert res_sig2.status_code == 201
            sig2 = res_sig2.json()
            created_signals.append(sig2["id"])

            # 4. Gating Low Confidence (review_status=pending)
            signal_payload3 = {
                "hospital_id": nyp_id,
                "signal_type": "rcm_hiring_spike",
                "tier": "worth_knowing",
                "confidence_score": 0.60,
                "title": "Low Confidence Hiring Surge",
                "summary": "Multiple RCM billing positions opened.",
                "source_name": "Modern Healthcare",
                "source_url": "https://example.com/e2e-low-conf"
            }
            res_sig3 = await client.post("/api/v1/signals", json=signal_payload3, headers=admin_headers)
            assert res_sig3.status_code == 201
            sig3 = res_sig3.json()
            assert sig3["review_status"] == "pending"
            created_signals.append(sig3["id"])

            # 5. Danielle reviews and approves signal
            review_payload = {
                "action": "approved",
                "reviewer_id": admin_id
            }
            res_rev = await client.post(f"/api/v1/signals/{sig3['id']}/review", json=review_payload, headers=admin_headers)
            assert res_rev.status_code == 200
            assert res_rev.json()["review_status"] == "approved"

            # 6. Synchronous Scraper Run (sets up Agent Run)
            res_scraper = await client.post("/api/v1/admin/run-scraper-sync", headers=internal_headers)
            assert res_scraper.status_code == 200
            run_summary = res_scraper.json()
            assert "run_id" in run_summary
            created_runs.append(run_summary["run_id"])

            # 7. Send digest (Admin manual trigger)
            res_digest = await client.post("/api/v1/digests/send", headers=admin_headers)
            assert res_digest.status_code == 200
            digest_summary = res_digest.json()
            
            # Map returned summary fields to match user prompt assertion terms:
            aes_messaged = digest_summary.get("sent_count", 0)
            signals_included = digest_summary.get("signals_digested", 0)
            assert aes_messaged >= 1, f"Expected aes_messaged >= 1, got {aes_messaged}"
            assert signals_included >= 1, f"Expected signals_included >= 1, got {signals_included}"
            
            digests_created = digest_summary.get("digests_created", [])
            assert digests_created, "Digests should be created and listed"
            digest_id = digests_created[0]["digest_id"]
            digest_ae_id = digests_created[0]["ae_id"]

            created_digests.append(digest_id)

            # 8. Check latest run
            res_run = await client.get("/api/v1/runs/latest")
            assert res_run.status_code == 200
            run_data = res_run.json()
            assert run_data["hospitals_checked"] == 5
            assert run_data["duration_ms"] > 0

            # 9. Record digest view (UTM tracking)
            view_payload = {
                "digest_id": digest_id,
                "ae_id": digest_ae_id,
                "utm_source": "slack"
            }
            res_view = await client.post("/api/v1/digest-view", json=view_payload)
            assert res_view.status_code == 200
            assert res_view.json()["recorded"] is True

            # 10. Check roster (Danielle admin view)
            res_roster = await client.get("/api/v1/ae-users", headers=admin_headers)
            assert res_roster.status_code == 200
            roster = res_roster.json()
            
            # Find the AE user who viewed the digest
            ae_user = next((u for u in roster if u["id"] == digest_ae_id), None)
            assert ae_user is not None, f"AE user {digest_ae_id} not found in roster."
            assert ae_user["last_viewed_digest"] is not None, "AE last_viewed_digest was not populated."

    finally:
        # DB cleanup: delete created entries in reverse dependency order
        # Failure in tests will still execute cleanup, preventing DB clutter
        for view_id in created_digests:
            try:
                supabase.table("digest_views").delete().eq("digest_id", view_id).execute()
            except Exception as e:
                print(f"Cleanup digest_views failed: {e}")
        for digest_id in created_digests:
            try:
                supabase.table("digests").delete().eq("id", digest_id).execute()
            except Exception as e:
                print(f"Cleanup digests failed: {e}")
        for signal_id in created_signals:
            try:
                supabase.table("signals").delete().eq("id", signal_id).execute()
            except Exception as e:
                print(f"Cleanup signals failed: {e}")
        for run_id in created_runs:
            try:
                supabase.table("agent_runs").delete().eq("id", run_id).execute()
            except Exception as e:
                print(f"Cleanup agent_runs failed: {e}")
