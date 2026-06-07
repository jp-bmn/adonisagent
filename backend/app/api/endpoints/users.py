"""
/me and AE user endpoints — Task 10 implementation.
Task 15 adds last_viewed_digest to ae-users response.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Response

from app.core.auth import get_required_user, get_admin_user
from app.core.database import get_supabase
from app.models.schemas import AEUserWithStats, HospitalAEAssignment
import re

def safe_parse_datetime(val: str) -> datetime:
    if not val:
        raise ValueError("Empty datetime string")
    s = val.replace("Z", "+00:00")
    if "." in s:
        base, rest = s.split(".", 1)
        match = re.match(r"^(\d+)(.*)$", rest)
        if match:
            frac, tz = match.groups()
            frac = (frac + "000000")[:6]
            s = f"{base}.{frac}{tz}"
    return datetime.fromisoformat(s)


router = APIRouter(tags=["users"])
logger = logging.getLogger(__name__)


@router.get("/me", response_model=AEUserWithStats)
async def get_me(user: dict = Depends(get_required_user)):
    """
    GET /api/v1/me
    Returns current user profile + assigned hospitals + new signals this week.
    """
    supabase = get_supabase()

    # 1. Fetch assigned hospitals
    assignments_res = (
        supabase.table("hospital_ae_assignments")
        .select("hospitals(*)")
        .eq("ae_id", user["id"])
        .execute()
    )
    hospitals = [a["hospitals"] for a in assignments_res.data if a.get("hospitals")]

    # 2. Count signals in last 7 days
    signals_count = 0
    if hospitals:
        seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
        hosp_ids = [h["id"] for h in hospitals]
        signals_res = (
            supabase.table("signals")
            .select("id", count="exact")
            .in_("hospital_id", hosp_ids)
            .gte("created_at", seven_days_ago)
            .neq("tier", "filtered_out")
            .neq("review_status", "dismissed")
            .execute()
        )
        signals_count = signals_res.count or 0

    # 3. Find the last viewed digest timestamp for this AE
    last_view = None
    views_res = (
        supabase.table("digest_views")
        .select("viewed_at")
        .eq("ae_id", user["id"])
        .order("viewed_at", desc=True)
        .limit(1)
        .execute()
    )
    if views_res.data:
        last_view = safe_parse_datetime(views_res.data[0]["viewed_at"])

    return AEUserWithStats(
        id=user["id"],
        name=user["name"],
        slack_user_id=user.get("slack_user_id"),
        is_admin=user.get("is_admin", False),
        created_at=user["created_at"],
        hospitals=hospitals,
        new_signals_this_week=signals_count,
        last_viewed_digest=last_view,
    )


@router.get("/ae-users", response_model=List[AEUserWithStats])
async def list_ae_users(response: Response, user: dict = Depends(get_admin_user)):
    """
    GET /api/v1/ae-users (admin only)
    Returns all AEs (is_admin=False) with assigned hospitals and stats.
    """
    supabase = get_supabase()

    # 1. Fetch all AEs
    ae_res = (
        supabase.table("ae_users")
        .select("*")
        .eq("is_admin", False)
        .execute()
    )
    aes = ae_res.data or []

    # 2. Fetch all assignments
    assignments_res = (
        supabase.table("hospital_ae_assignments")
        .select("ae_id, hospitals(*)")
        .execute()
    )
    from collections import defaultdict
    ae_hospitals = defaultdict(list)
    for a in assignments_res.data:
        if a.get("hospitals"):
            ae_hospitals[a["ae_id"]].append(a["hospitals"])

    # 3. Fetch all signals in last 7 days
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    signals_res = (
        supabase.table("signals")
        .select("hospital_id")
        .gte("created_at", seven_days_ago)
        .neq("tier", "filtered_out")
        .neq("review_status", "dismissed")
        .execute()
    )
    hosp_signals = defaultdict(int)
    for s in signals_res.data:
        hosp_signals[s["hospital_id"]] += 1

    # 4. Fetch last viewed digest for each AE
    views_res = (
        supabase.table("digest_views")
        .select("ae_id, viewed_at")
        .order("viewed_at", desc=True)
        .execute()
    )
    ae_last_view = {}
    for v in views_res.data or []:
        ae_uuid = v["ae_id"]
        if ae_uuid not in ae_last_view:
            ae_last_view[ae_uuid] = safe_parse_datetime(v["viewed_at"])

    # 5. Construct list of AEUserWithStats
    results = []
    for ae in aes:
        hlist = ae_hospitals[ae["id"]]
        sig_count = sum(hosp_signals[h["id"]] for h in hlist)
        last_view = ae_last_view.get(ae["id"])
        results.append(
            AEUserWithStats(
                id=ae["id"],
                name=ae["name"],
                slack_user_id=ae.get("slack_user_id"),
                is_admin=ae.get("is_admin", False),
                created_at=ae["created_at"],
                hospitals=hlist,
                new_signals_this_week=sig_count,
                last_viewed_digest=last_view,
            )
        )
    response.headers["X-Total-Count"] = str(len(results))
    return results


@router.post("/hospital-ae-assignments", response_model=HospitalAEAssignment, status_code=201)
async def create_assignment(
    payload: HospitalAEAssignment,
    user: dict = Depends(get_admin_user)
):
    """
    POST /api/v1/hospital-ae-assignments (admin only)
    Creates a new assignment between a hospital and an AE.
    Checks for existing assignment and returns 409 if already assigned.
    """
    supabase = get_supabase()
    
    # Check if the hospital exists
    hosp_check = supabase.table("hospitals").select("id").eq("id", str(payload.hospital_id)).execute()
    if not hosp_check.data:
        raise HTTPException(status_code=404, detail=f"Hospital {payload.hospital_id} not found")
        
    # Check if the AE exists
    ae_check = supabase.table("ae_users").select("id").eq("id", str(payload.ae_id)).execute()
    if not ae_check.data:
        raise HTTPException(status_code=404, detail=f"AE user {payload.ae_id} not found")
        
    # Check for existing assignment
    check_res = (
        supabase.table("hospital_ae_assignments")
        .select("*")
        .eq("hospital_id", str(payload.hospital_id))
        .eq("ae_id", str(payload.ae_id))
        .execute()
    )
    if check_res.data:
        raise HTTPException(
            status_code=409,
            detail=f"Hospital {payload.hospital_id} is already assigned to AE {payload.ae_id}"
        )
        
    # Create assignment
    insert_res = (
        supabase.table("hospital_ae_assignments")
        .insert({
            "hospital_id": str(payload.hospital_id),
            "ae_id": str(payload.ae_id)
        })
        .execute()
    )
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to create assignment")
        
    return insert_res.data[0]


@router.get("/digest-analytics")
async def digest_analytics(response: Response, user: dict = Depends(get_admin_user)):
    """
    GET /api/v1/digest-analytics (admin only)
    Returns per-digest engagement for the last 30 days.
    """
    supabase = get_supabase()
    from collections import defaultdict

    thirty_days_ago = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    try:
        # Fetch all digests sent in the last 30 days
        digests_res = (
            supabase.table("digests")
            .select("*, ae_users(name)")
            .gte("sent_at", thirty_days_ago)
            .order("sent_at", desc=True)
            .execute()
        )
        digests_data = digests_res.data or []
    except Exception as e:
        logger.error(f"Error fetching digests for analytics: {e}")
        return []

    digest_ids = [d["id"] for d in digests_data]
    views_by_digest = defaultdict(list)

    if digest_ids:
        try:
            # Fetch all views for these digests
            views_res = (
                supabase.table("digest_views")
                .select("*")
                .in_("digest_id", digest_ids)
                .execute()
            )
            for v in views_res.data or []:
                views_by_digest[v["digest_id"]].append(v)
        except Exception as e:
            logger.error(f"Error fetching views for analytics: {e}")

    analytics = []
    for d in digests_data:
        d_id = d["id"]
        d_views = views_by_digest.get(d_id, [])
        
        opened = len(d_views) > 0
        view_count = len(d_views)
        
        first_viewed_at = None
        time_to_open_minutes = None
        
        if opened:
            # Sort views by viewed_at ascending to find the first view
            sorted_views = sorted(d_views, key=lambda x: x["viewed_at"])
            first_viewed_at = sorted_views[0]["viewed_at"]
            
            # Compute time to open in minutes
            if d.get("sent_at") and first_viewed_at:
                sent_dt = safe_parse_datetime(d["sent_at"])
                view_dt = safe_parse_datetime(first_viewed_at)
                time_to_open_minutes = (view_dt - sent_dt).total_seconds() / 60.0

        ae_relation = d.get("ae_users")
        ae_name = "Unknown AE"
        if isinstance(ae_relation, dict):
            ae_name = ae_relation.get("name", "Unknown AE")
        elif isinstance(ae_relation, list) and ae_relation:
            ae_name = ae_relation[0].get("name", "Unknown AE")

        analytics.append({
            "digest_id": d_id,
            "ae_id": d.get("ae_id"),
            "ae_name": ae_name,
            "sent_at": d.get("sent_at"),
            "week_start": d.get("week_start"),
            "week_end": d.get("week_end"),
            "opened": opened,
            "view_count": view_count,
            "first_viewed_at": first_viewed_at,
            "time_to_open_minutes": time_to_open_minutes
        })

    response.headers["X-Total-Count"] = str(len(analytics))
    return analytics
