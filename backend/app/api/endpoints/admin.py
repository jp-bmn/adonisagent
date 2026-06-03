"""
Admin endpoints — protected by INTERNAL_API_KEY.
Task 6: run-scraper, send-digest
"""
from fastapi import APIRouter, Depends
from app.core.auth import check_admin_api_key
import logging

router = APIRouter(prefix="/admin", tags=["admin"])
logger = logging.getLogger(__name__)


@router.post("/run-scraper")
async def trigger_scraper(_: None = Depends(check_admin_api_key)):
    """
    POST /api/v1/admin/run-scraper
    Triggers run_scraper_job(). Full implementation in Task 6.
    """
    # TODO (Task 6): from app.jobs.scraper_job import run_scraper_job; return await run_scraper_job()
    return {
        "message": "scraper trigger — implementation pending Task 6",
        "hospitals_checked": 0,
        "signals_found": 0,
        "signals_new": 0,
        "rules_engine_hits": 0,
    }


@router.post("/send-digest")
async def trigger_digest(_: None = Depends(check_admin_api_key)):
    """
    POST /api/v1/admin/send-digest
    Triggers run_monday_digest(). Full implementation in Task 6 & 8.
    """
    # TODO (Task 6 & 8): from app.jobs.scraper_job import run_monday_digest; return await run_monday_digest()
    return {"message": "digest trigger — implementation pending Task 6 & 8", "status": "pending"}
