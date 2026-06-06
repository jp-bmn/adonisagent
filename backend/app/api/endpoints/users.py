"""
/me and AE user endpoints — Task 10 implementation.
Task 15 adds last_viewed_digest to ae-users response.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_required_user, get_admin_user
from app.core.database import get_supabase
from app.models.schemas import AEUserWithStats, HospitalAEAssignment

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

    return AEUserWithStats(
        id=user["id"],
        name=user["name"],
        slack_user_id=user.get("slack_user_id"),
        is_admin=user.get("is_admin", False),
        created_at=user["created_at"],
        hospitals=hospitals,
        new_signals_this_week=signals_count,
        last_viewed_digest=None,
    )


@router.get("/ae-users", response_model=List[AEUserWithStats])
async def list_ae_users(user: dict = Depends(get_admin_user)):
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

    # 4. Construct list of AEUserWithStats
    results = []
    for ae in aes:
        hlist = ae_hospitals[ae["id"]]
        sig_count = sum(hosp_signals[h["id"]] for h in hlist)
        results.append(
            AEUserWithStats(
                id=ae["id"],
                name=ae["name"],
                slack_user_id=ae.get("slack_user_id"),
                is_admin=ae.get("is_admin", False),
                created_at=ae["created_at"],
                hospitals=hlist,
                new_signals_this_week=sig_count,
                last_viewed_digest=None,
            )
        )
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
async def digest_analytics(user: dict = Depends(get_admin_user)):
    """
    GET /api/v1/digest-analytics (admin only)
    Returns per-digest engagement for the last 30 days.
    Full implementation in Task 15.
    """
    # TODO (Task 15): query digests + digest_views, compute time_to_open_minutes
    return {"message": "digest analytics — implementation pending Task 15"}
