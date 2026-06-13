"""
Agent run logging services.
Writes agent scraping execution logs and stats directly to Supabase.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from typing import Optional
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


def start_run(run_id: str) -> dict:
    """
    Logs the beginning of an agent scraper run.
    """
    supabase = get_supabase()
    payload = {
        "id": run_id,
        "run_at": datetime.now(timezone.utc).isoformat(),
        "hospitals_checked": 0,
        "signals_found": 0,
        "signals_new": 0,
        "rules_engine_hits": 0,
        "errors": None,
        "duration_ms": None,
    }
    try:
        res = supabase.table("agent_runs").insert(payload).execute()
        if res.data:
            logger.info(f"Agent run started: {run_id}")
            return res.data[0]
    except Exception as e:
        logger.error(f"Failed to insert starting log for run {run_id}: {e}")
    return payload


def update_run(
    run_id: str,
    hospitals_checked: Optional[int] = None,
    signals_found: Optional[int] = None,
    signals_new: Optional[int] = None,
    rules_engine_hits: Optional[int] = None,
    errors: Optional[list[str]] = None,
) -> dict:
    """
    Updates progress stats for an active agent run.
    """
    supabase = get_supabase()
    payload = {}

    if hospitals_checked is not None:
        payload["hospitals_checked"] = hospitals_checked
    if signals_found is not None:
        payload["signals_found"] = signals_found
    if signals_new is not None:
        payload["signals_new"] = signals_new
    if rules_engine_hits is not None:
        payload["rules_engine_hits"] = rules_engine_hits
    if errors is not None:
        payload["errors"] = {"errors": errors}

    if not payload:
        try:
            res = supabase.table("agent_runs").select("*").eq("id", run_id).execute()
            return res.data[0] if res.data else {}
        except Exception as e:
            logger.error(f"Failed to fetch run {run_id}: {e}")
            return {}

    try:
        res = supabase.table("agent_runs").update(payload).eq("id", run_id).execute()
        if res.data:
            return res.data[0]
    except Exception as e:
        logger.error(f"Failed to update progress for run {run_id}: {e}")
    return {}


def complete_run(
    run_id: str,
    hospitals_checked: int,
    signals_found: int,
    signals_new: int,
    rules_engine_hits: int,
    duration_ms: int,
    errors: Optional[list[str]] = None,
) -> dict:
    """
    Finalizes an agent run with complete statistics and duration.
    """
    supabase = get_supabase()
    payload = {
        "hospitals_checked": hospitals_checked,
        "signals_found": signals_found,
        "signals_new": signals_new,
        "rules_engine_hits": rules_engine_hits,
        "duration_ms": duration_ms,
        "errors": {"errors": errors} if errors else None,
    }
    try:
        res = supabase.table("agent_runs").update(payload).eq("id", run_id).execute()
        if res.data:
            logger.info(f"Agent run completed: {run_id} in {duration_ms}ms")
            return res.data[0]
    except Exception as e:
        logger.error(f"Failed to complete log for run {run_id}: {e}")
    return payload
