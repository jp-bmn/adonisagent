"""
Agent run tracking endpoints.
Task 12: Full implementation.
"""
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_admin_user
import logging

router = APIRouter(tags=["runs"])
logger = logging.getLogger(__name__)


@router.get("/runs")
async def list_runs(
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    user: dict = Depends(get_admin_user),
):
    """GET /api/v1/runs (admin only) — Task 12"""
    return {"message": "runs list — implementation pending Task 12"}


@router.get("/runs/latest")
async def latest_run():
    """GET /api/v1/runs/latest (public) — Task 12"""
    return {"message": "latest run — implementation pending Task 12"}


@router.get("/status")
async def system_status():
    """
    GET /api/v1/status (public)
    Returns api_version, last_scraper_run, next_scraper_run, totals.
    Full implementation in Task 12.
    """
    return {
        "api_version": "1.0.0",
        "last_scraper_run": None,
        "next_scraper_run": None,
        "total_signals_stored": 0,
        "total_hospitals_monitored": 5,
        "pending_review_count": 0,
        "message": "full implementation pending Task 12",
    }
