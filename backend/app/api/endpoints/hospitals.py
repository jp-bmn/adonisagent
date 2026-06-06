"""
Hospital endpoints — Task 3 full implementation.
Task 10 adds territory filtering (admin vs AE views).
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from app.core.auth import get_required_user
from app.core.database import get_supabase
import logging

router = APIRouter(prefix="/hospitals", tags=["hospitals"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_hospitals(user: dict = Depends(get_required_user)):
    """
    GET /api/v1/hospitals
    Returns all hospitals with their assigned AEs, joined from hospital_ae_assignments.
    Task 10 will add territory filtering: AEs see only their assigned hospitals.
    """
    supabase = get_supabase()

    # Fetch all hospitals
    hospitals_res = supabase.table("hospitals").select("*").order("name").execute()
    hospitals = hospitals_res.data or []

    if not hospitals:
        return []

    # Fetch all assignments with AE details in one query
    assignments_res = (
        supabase.table("hospital_ae_assignments")
        .select("hospital_id, ae_id, ae_users(id, name, is_admin)")
        .execute()
    )
    assignments = assignments_res.data or []

    # Build a map: hospital_id → list of AE user objects
    ae_map: dict[str, list[dict]] = {}
    for a in assignments:
        hid = a["hospital_id"]
        ae = a.get("ae_users")
        if ae:
            ae_map.setdefault(hid, []).append(ae)

    # Filter hospitals to only those where user is assigned if not admin
    if not user.get("is_admin", False):
        user_id = str(user["id"])
        hospitals = [
            h for h in hospitals
            if any(str(ae["id"]) == user_id for ae in ae_map.get(h["id"], []))
        ]

    return [
        {
            "id": h["id"],
            "name": h["name"],
            "website_url": h["website_url"],
            "division_note": h["division_note"],
            "created_at": h["created_at"],
            "ae_users": ae_map.get(h["id"], []),
        }
        for h in hospitals
    ]


@router.get("/{hospital_id}/signals")
async def get_hospital_signals(
    hospital_id: str,
    tier: Optional[str] = Query(default=None, description="Filter: urgent | worth_knowing | filtered_out"),
    limit: int = Query(default=50, le=200),
    user: dict = Depends(get_required_user),
):
    """
    GET /api/v1/hospitals/{hospital_id}/signals
    Returns signals for one hospital ordered by created_at DESC.
    """
    supabase = get_supabase()

    # Verify hospital exists
    hospital_res = supabase.table("hospitals").select("id, name").eq("id", hospital_id).single().execute()
    if not hospital_res.data:
        raise HTTPException(status_code=404, detail=f"Hospital {hospital_id} not found")

    # Territory check for non-admin AEs
    if not user.get("is_admin", False):
        assignment_check = (
            supabase.table("hospital_ae_assignments")
            .select("*")
            .eq("hospital_id", hospital_id)
            .eq("ae_id", str(user["id"]))
            .execute()
        )
        if not assignment_check.data:
            raise HTTPException(status_code=403, detail="Access denied to this hospital's signals")

    query = (
        supabase.table("signals")
        .select("*")
        .eq("hospital_id", hospital_id)
        .order("created_at", desc=True)
        .limit(limit)
    )

    if tier:
        valid_tiers = ("urgent", "worth_knowing", "filtered_out")
        if tier not in valid_tiers:
            raise HTTPException(
                status_code=422,
                detail=f"tier must be one of: {', '.join(valid_tiers)}",
            )
        query = query.eq("tier", tier)

    result = query.execute()
    return result.data or []
