"""
Scraper job orchestration — Task 6 full implementation.

run_scraper_job()   — Mon/Wed/Fri 11:00 UTC: fetch hospitals, run per-hospital
                       scrape, aggregate results, return summary JSON.
run_monday_digest() — Monday only: scrape first, then check pending review queue,
                       then send weekly digest (or block with Danielle DM).
run_hospital_scrape() — STUB. Michael's pipeline replaces this with a real
                         scraper per hospital. For now returns signals that
                         arrived via POST /signals/batch in the last 24h.

Run logger calls are lightweight inline Supabase inserts here.
Task 12 will refactor into a proper run_logger service with full tracking.
"""
from __future__ import annotations

import asyncio
import logging
import time
import uuid
from datetime import datetime, timezone, timedelta
from typing import Optional

from app.core.database import get_supabase
from app.services.run_logger import start_run, update_run, complete_run

logger = logging.getLogger(__name__)

# Stored between runs so /status can report the last run timestamp
_last_run_summary: Optional[dict] = None
_last_run_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Per-hospital scrape (STUB — replaced by Michael's pipeline)
# ---------------------------------------------------------------------------

async def run_hospital_scrape(hospital_id: str, hospital_name: str) -> dict:
    """
    STUB: Michael's hospital-specific scrapers post directly via
    POST /api/v1/signals/batch. This function counts new signals
    that arrived via that endpoint in the last 24 hours as a proxy.

    Returns:
        {"signals_found": int, "signals_new": int, "rules_engine_hits": int}
    """
    await asyncio.sleep(0)  # yield to event loop

    supabase = get_supabase()
    cutoff = (datetime.now(timezone.utc) - timedelta(hours=24)).isoformat()

    try:
        result = (
            supabase.table("signals")
            .select("id, signal_type, tier", count="exact")
            .eq("hospital_id", hospital_id)
            .gte("created_at", cutoff)
            .execute()
        )
        signals = result.data or []
        rules_hits = sum(
            1 for s in signals
            if s.get("signal_type") not in ("filtered_out", None)
        )
        return {
            "signals_found": len(signals),
            "signals_new":   len(signals),
            "rules_engine_hits": rules_hits,
        }
    except Exception as e:
        logger.error(f"Failed to count signals for hospital {hospital_name}: {e}")
        return {"signals_found": 0, "signals_new": 0, "rules_engine_hits": 0}


# ---------------------------------------------------------------------------
# Main scraper orchestration
# ---------------------------------------------------------------------------

async def run_scraper_job() -> dict:
    """
    Main scraper job. Called Mon/Wed/Fri 11:00 UTC by APScheduler.
    Also callable directly via POST /admin/run-scraper.

    Flow:
    1. Log run start to agent_runs table (lightweight)
    2. Fetch all hospitals from Supabase
    3. Run per-hospital scrape concurrently
    4. Aggregate totals
    5. Update run record with results

    Returns:
        Summary dict with hospitals_checked, signals_found, signals_new,
        rules_engine_hits, duration_ms, run_id.
    """
    global _last_run_summary, _last_run_at

    start_time = time.time()
    run_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()
    supabase = get_supabase()

    logger.info(f"Scraper run starting | run_id={run_id}")

    # ── Log run start ────────────────────────────────────────────────────────
    try:
        start_run(run_id)
    except Exception as e:
        logger.warning(f"Could not log run start: {e}")

    # ── Fetch hospitals ──────────────────────────────────────────────────────
    try:
        hospitals_res = supabase.table("hospitals").select("id, name").execute()
        hospitals = hospitals_res.data or []
    except Exception as e:
        logger.error(f"Failed to fetch hospitals: {e}")
        hospitals = []

    totals = {
        "hospitals_checked": 0,
        "signals_found":     0,
        "signals_new":       0,
        "rules_engine_hits": 0,
    }
    errors: list[str] = []

    # ── Per-hospital scrape (concurrent) ─────────────────────────────────────
    async def _scrape_one(hospital: dict):
        try:
            result = await run_hospital_scrape(hospital["id"], hospital["name"])
            totals["hospitals_checked"] += 1
            totals["signals_found"]     += result.get("signals_found", 0)
            totals["signals_new"]       += result.get("signals_new", 0)
            totals["rules_engine_hits"] += result.get("rules_engine_hits", 0)
            logger.info(
                f"Scraped {hospital['name']}: "
                f"found={result['signals_found']} new={result['signals_new']}"
            )
            update_run(
                run_id=run_id,
                hospitals_checked=totals["hospitals_checked"],
                signals_found=totals["signals_found"],
                signals_new=totals["signals_new"],
                rules_engine_hits=totals["rules_engine_hits"],
            )
        except Exception as e:
            err = f"Hospital {hospital['name']}: {e}"
            errors.append(err)
            logger.error(f"Scrape failed — {err}")
            update_run(
                run_id=run_id,
                hospitals_checked=totals["hospitals_checked"],
                signals_found=totals["signals_found"],
                signals_new=totals["signals_new"],
                rules_engine_hits=totals["rules_engine_hits"],
                errors=errors,
            )

    await asyncio.gather(*[_scrape_one(h) for h in hospitals])

    duration_ms = int((time.time() - start_time) * 1000)

    summary = {
        "run_id":            run_id,
        "status":            "completed" if not errors else "completed_with_errors",
        "started_at":        started_at,
        "duration_ms":       duration_ms,
        **totals,
        "errors":            errors,
    }

    # ── Update run record ────────────────────────────────────────────────────
    try:
        complete_run(
            run_id=run_id,
            hospitals_checked=totals["hospitals_checked"],
            signals_found=totals["signals_found"],
            signals_new=totals["signals_new"],
            rules_engine_hits=totals["rules_engine_hits"],
            duration_ms=duration_ms,
            errors=errors if errors else None,
        )
    except Exception as e:
        logger.warning(f"Could not update run record: {e}")

    _last_run_summary = summary
    _last_run_at      = datetime.now(timezone.utc)

    logger.info(
        f"Scraper run complete | run_id={run_id} | "
        f"hospitals={totals['hospitals_checked']} signals_new={totals['signals_new']} "
        f"duration={duration_ms}ms"
    )
    return summary


# ---------------------------------------------------------------------------
# Monday digest orchestration
# ---------------------------------------------------------------------------

async def run_monday_digest() -> dict:
    """
    Monday job: scrape first, check review queue, then send digest or block.

    Flow:
    1. Run full scraper job
    2. Count signals with review_status='pending'
    3. If pending > 0:  DM Danielle with count → block digest (human-in-loop)
    4. If pending == 0: call send_weekly_digest_to_all_aes() (Task 8 hook)

    Returns:
        Status dict including scraper results and digest outcome.
    """
    logger.info("Monday digest job starting")

    # 1. Scrape
    scraper_result = await run_scraper_job()

    supabase = get_supabase()

    # 2. Check pending review queue
    try:
        pending_res = (
            supabase.table("signals")
            .select("id", count="exact")
            .eq("review_status", "pending")
            .execute()
        )
        pending_count = pending_res.count or 0
    except Exception as e:
        logger.error(f"Failed to check pending count: {e}")
        pending_count = 0

    # 3. Block if review queue has items — DM Danielle (Luminai Human-in-the-Loop)
    if pending_count > 0:
        logger.warning(f"Digest BLOCKED — {pending_count} signals pending review")
        _notify_danielle_pending(pending_count)
        return {
            "status":        "blocked_by_review_queue",
            "pending_count": pending_count,
            "scraper":       scraper_result,
        }

    # 4. Send digest (Task 8 hook — no-op stub until digest_service is built)
    try:
        from app.services.digest_service import send_weekly_digest_to_all_aes  # type: ignore
        await send_weekly_digest_to_all_aes()
        digest_status = "sent"
    except ImportError:
        # digest_service not yet built (Task 8) — log and continue
        logger.info("digest_service not available yet (Task 8) — skipping digest send")
        digest_status = "pending_task_8"

    logger.info(f"Monday digest complete | digest_status={digest_status}")
    return {
        "status":  "digest_sent" if digest_status == "sent" else "scraper_complete_digest_pending",
        "scraper": scraper_result,
    }


def _notify_danielle_pending(pending_count: int) -> None:
    """DM Danielle when the review queue is blocking the Monday digest."""
    try:
        from app.services.slack_service import send_dm
        from app.core.config import get_settings
        settings = get_settings()
        danielle_id = settings.slack_user_id_danielle

        if not danielle_id or danielle_id.startswith("PLACEHOLDER"):
            logger.warning("SLACK_USER_ID_DANIELLE not configured — skipping DM")
            return

        send_dm(
            slack_user_id=danielle_id,
            text=(
                f"⚠️ Weekly digest is BLOCKED — {pending_count} signal"
                f"{'s' if pending_count != 1 else ''} need your review before the digest can send.\n"
                f"Please review at the dashboard."
            ),
        )
        logger.info(f"Notified Danielle of {pending_count} pending signals")
    except Exception as e:
        logger.error(f"Failed to notify Danielle of pending signals: {e}")


# ---------------------------------------------------------------------------
# Status helpers for /api/v1/status
# ---------------------------------------------------------------------------

def get_last_run_summary() -> Optional[dict]:
    return _last_run_summary


def get_last_run_at() -> Optional[datetime]:
    return _last_run_at
