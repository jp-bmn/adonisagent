"""
Admin endpoints — protected by INTERNAL_API_KEY.
Task 6 full implementation: real run_scraper_job() and run_monday_digest() calls.
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends, BackgroundTasks

from app.core.auth import check_admin_api_key

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.post("/run-scraper")
async def trigger_scraper(
    background_tasks: BackgroundTasks,
    _: None = Depends(check_admin_api_key),
):
    """
    POST /api/v1/admin/run-scraper
    Auth: X-API-Key: <INTERNAL_API_KEY>

    Triggers a full scraper run immediately (same job as the APScheduler cron).
    Runs in a BackgroundTask so the HTTP response returns immediately with a
    202 Accepted + run_id. Poll GET /status for results.

    Returns:
        {"status": "accepted", "run_id": str, "message": str}
    """
    from app.jobs.scraper_job import run_scraper_job
    import uuid

    run_id = str(uuid.uuid4())

    async def _run():
        try:
            await run_scraper_job()
        except Exception as e:
            logger.error(f"Admin-triggered scraper run failed: {e}")

    background_tasks.add_task(_run)

    logger.info(f"Admin-triggered scraper run queued | run_id={run_id}")
    return {
        "status":  "accepted",
        "run_id":  run_id,
        "message": "Scraper job queued. Check GET /api/v1/status for results.",
    }


@router.post("/run-scraper-sync")
async def trigger_scraper_sync(_: None = Depends(check_admin_api_key)):
    """
    POST /api/v1/admin/run-scraper-sync
    Auth: X-API-Key: <INTERNAL_API_KEY>

    Synchronous version — waits for the job to complete and returns full
    summary JSON. Use for testing and CI; use /run-scraper for production.
    """
    from app.jobs.scraper_job import run_scraper_job
    logger.info("Admin-triggered synchronous scraper run starting")
    result = await run_scraper_job()
    return result


@router.post("/send-digest")
async def trigger_digest(
    background_tasks: BackgroundTasks,
    _: None = Depends(check_admin_api_key),
):
    """
    POST /api/v1/admin/send-digest
    Auth: X-API-Key: <INTERNAL_API_KEY>

    Triggers the Monday digest flow immediately:
    - Scrapes hospitals
    - Checks pending review queue
    - If clear: sends digest to all AEs
    - If blocked: DMs Danielle with pending count

    Runs asynchronously. Returns 202 immediately.
    """
    from app.jobs.scraper_job import run_monday_digest

    async def _run():
        try:
            await run_monday_digest()
        except Exception as e:
            logger.error(f"Admin-triggered digest run failed: {e}")

    background_tasks.add_task(_run)

    logger.info("Admin-triggered digest run queued")
    return {
        "status":  "accepted",
        "message": "Digest job queued. Check Slack and GET /api/v1/status for results.",
    }


@router.post("/send-digest-sync")
async def trigger_digest_sync(_: None = Depends(check_admin_api_key)):
    """
    POST /api/v1/admin/send-digest-sync
    Synchronous version for testing — returns full digest result.
    """
    from app.jobs.scraper_job import run_monday_digest
    logger.info("Admin-triggered synchronous digest run starting")
    result = await run_monday_digest()
    return result
