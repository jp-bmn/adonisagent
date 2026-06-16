"""
Agent run tracking endpoints.
Task 12: Full implementation.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, Response

from app.core.auth import get_admin_user
from app.core.database import get_supabase
from app.core.cache import ttl_cache
from app.models.schemas import AgentRun, StatusResponse

router = APIRouter(tags=["runs"])
logger = logging.getLogger(__name__)


def get_next_scraper_run(now: datetime) -> datetime:
    """
    Calculates the next scheduled scraper run (Mon/Wed/Fri at 11:00 UTC).
    """
    now_utc = now.astimezone(timezone.utc)
    target_hour = 11
    target_minute = 0
    target_days = {0, 2, 4}  # Mon, Wed, Fri

    for i in range(8):  # Check today and next 7 days
        candidate = now_utc + timedelta(days=i)
        if candidate.weekday() in target_days:
            run_time = candidate.replace(
                hour=target_hour, minute=target_minute, second=0, microsecond=0
            )
            if run_time > now_utc:
                return run_time
    return now_utc


@router.get("/runs", response_model=list[AgentRun])
async def list_runs(
    response: Response,
    limit: int = Query(default=20, le=100),
    offset: int = Query(default=0),
    user: dict = Depends(get_admin_user),
):
    """
    GET /api/v1/runs (admin only)
    Returns a paginated list of agent runs, sorted by run_at DESC.
    """
    supabase = get_supabase()
    try:
        # Get exact count for pagination header
        count_res = supabase.table("agent_runs").select("id", count="exact").execute()
        total_count = count_res.count or 0
        response.headers["X-Total-Count"] = str(total_count)

        res = (
            supabase.table("agent_runs")
            .select("*")
            .order("run_at", desc=True)
            .range(offset, offset + limit - 1)
            .execute()
        )
        return res.data or []
    except Exception as e:
        logger.error(f"Failed to fetch runs: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve runs")


@router.get("/runs/latest", response_model=Optional[AgentRun])
@ttl_cache(60.0)
async def latest_run():
    """
    GET /api/v1/runs/latest (public)
    Returns the single most recent agent run or null if none exist.
    """
    supabase = get_supabase()
    try:
        res = (
            supabase.table("agent_runs")
            .select("*")
            .order("run_at", desc=True)
            .limit(1)
            .execute()
        )
        if res.data:
            return res.data[0]
        return None
    except Exception as e:
        logger.error(f"Failed to fetch latest run: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve latest run")


@router.get("/status", response_model=StatusResponse)
@ttl_cache(60.0)
async def system_status():
    """
    GET /api/v1/status (public)
    Returns api_version, last_scraper_run, next_scraper_run, and summary metrics.
    """
    supabase = get_supabase()
    try:
        # 1. Get last scraper run
        last_run_res = (
            supabase.table("agent_runs")
            .select("run_at")
            .order("run_at", desc=True)
            .limit(1)
            .execute()
        )
        last_scraper_run = None
        if last_run_res.data:
            last_scraper_run = last_run_res.data[0]["run_at"]

        # 2. Get next scraper run
        next_scraper_run = get_next_scraper_run(datetime.now(timezone.utc)).isoformat()

        # 3. Get total signals stored
        signals_count_res = supabase.table("signals").select("id", count="exact").execute()
        total_signals_stored = signals_count_res.count or 0

        # 4. Get total hospitals monitored
        hospitals_count_res = supabase.table("hospitals").select("id", count="exact").execute()
        total_hospitals_monitored = hospitals_count_res.count or 5

        # 5. Get pending review signals count
        pending_count_res = (
            supabase.table("signals")
            .select("id", count="exact")
            .eq("review_status", "pending")
            .execute()
        )
        pending_review_count = pending_count_res.count or 0

        # 6. Calculate calendar week stats for KPIs comparing this week vs last week
        now = datetime.now(timezone.utc)
        # Find Monday of this week (00:00:00 UTC)
        monday_this_week = (now - timedelta(days=now.weekday())).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
        last_monday = monday_this_week - timedelta(days=7)

        monday_this_week_iso = monday_this_week.isoformat()
        last_monday_iso = last_monday.isoformat()

        # Count this week's urgent signals (since Monday of this week)
        urgent_this_week = (
            supabase.table("signals")
            .select("id", count="exact")
            .eq("tier", "urgent")
            .gte("created_at", monday_this_week_iso)
            .or_("review_status.is.null,review_status.neq.dismissed")
            .execute()
        )
        urgent_count = urgent_this_week.count or 0

        # Count this week's worth_knowing signals (since Monday of this week)
        worth_this_week = (
            supabase.table("signals")
            .select("id", count="exact")
            .eq("tier", "worth_knowing")
            .gte("created_at", monday_this_week_iso)
            .or_("review_status.is.null,review_status.neq.dismissed")
            .execute()
        )
        worth_knowing_count = worth_this_week.count or 0

        # Count last week's urgent signals (between last Monday and this Monday)
        urgent_last_week = (
            supabase.table("signals")
            .select("id", count="exact")
            .eq("tier", "urgent")
            .gte("created_at", last_monday_iso)
            .lt("created_at", monday_this_week_iso)
            .or_("review_status.is.null,review_status.neq.dismissed")
            .execute()
        )
        urgent_prev = urgent_last_week.count or 0

        # Count last week's worth_knowing signals (between last Monday and this Monday)
        worth_last_week = (
            supabase.table("signals")
            .select("id", count="exact")
            .eq("tier", "worth_knowing")
            .gte("created_at", last_monday_iso)
            .lt("created_at", monday_this_week_iso)
            .or_("review_status.is.null,review_status.neq.dismissed")
            .execute()
        )
        worth_prev = worth_last_week.count or 0

        # Calculate deltas & directions
        urgent_delta = urgent_count - urgent_prev
        urgent_delta_direction = "up" if urgent_delta > 0 else "down" if urgent_delta < 0 else "flat"

        worth_knowing_delta = worth_knowing_count - worth_prev
        worth_knowing_delta_direction = "up" if worth_knowing_delta > 0 else "down" if worth_knowing_delta < 0 else "flat"

        return {
            "api_version": "1.0.0",
            "last_scraper_run": last_scraper_run,
            "next_scraper_run": next_scraper_run,
            "total_signals_stored": total_signals_stored,
            "total_hospitals_monitored": total_hospitals_monitored,
            "pending_review_count": pending_review_count,
            "urgent_count": urgent_count,
            "urgent_delta": urgent_delta,
            "urgent_delta_direction": urgent_delta_direction,
            "worth_knowing_count": worth_knowing_count,
            "worth_knowing_delta": worth_knowing_delta,
            "worth_knowing_delta_direction": worth_knowing_delta_direction,
        }
    except Exception as e:
        logger.error(f"Failed to get system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch system status")
