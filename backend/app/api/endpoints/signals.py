"""
Signal endpoints — Task 3 full implementation.
Task 9 adds: POST /signals/{id}/review
Task 10 adds: territory filtering
Task 14 adds: BackgroundTasks urgent alert hook on POST /signals
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from app.core.auth import get_required_user, get_admin_user
from app.core.database import get_supabase
import logging

router = APIRouter(prefix="/signals", tags=["signals"])
logger = logging.getLogger(__name__)

VALID_SIGNAL_TYPES = {
    "leadership_change", "rcm_hiring_spike", "epic_go_live", "post_golive_friction",
    "ma_acquisition", "vendor_change", "vendor_dispute", "restructuring",
    "new_hospital_launch", "financial_event", "ai_adoption_outside_rcm",
    "automation_proof", "named_automation_owner", "thought_leadership", "filtered_out",
}

VALID_TIERS = {"urgent", "worth_knowing", "filtered_out"}


# NOTE: /pending-review must be declared BEFORE /{signal_id} to avoid routing conflict
@router.get("/pending-review")
async def get_pending_review(
    limit: int = Query(default=50, le=200),
    user: dict = Depends(get_required_user),
):
    """
    GET /api/v1/signals/pending-review
    Returns signals where review_status='pending', ordered by confidence_score ASC
    (lowest confidence first — needs the most human review).
    Includes hospital_name via join.
    """
    supabase = get_supabase()

    # Build query — join hospital name
    query = (
        supabase.table("signals")
        .select("*, hospitals(name)")
        .eq("review_status", "pending")
        .order("confidence_score", desc=False)
        .limit(limit)
    )

    # TODO (Task 10): if not admin, also filter to user's territory hospitals

    result = query.execute()
    rows = result.data or []

    # Flatten hospital name into top-level field
    return [
        {**r, "hospital_name": (r.get("hospitals") or {}).get("name"), "hospitals": None}
        for r in rows
    ]


@router.get("")
async def list_signals(
    ae_id: Optional[str] = Query(default=None, description="Filter to one AE's territory"),
    tier: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=200),
    include_dismissed: bool = Query(default=False, description="If false (default), exclude dismissed signals"),
    user: dict = Depends(get_required_user),
):
    """
    GET /api/v1/signals
    Returns signals with optional AE territory and tier filtering.
    Task 10 will enforce that AEs can only see their own territory.
    """
    supabase = get_supabase()

    query = supabase.table("signals").select("*").order("created_at", desc=True).limit(limit)

    # Tier filter
    if tier:
        if tier not in VALID_TIERS:
            raise HTTPException(status_code=422, detail=f"tier must be one of: {', '.join(VALID_TIERS)}")
        query = query.eq("tier", tier)

    # Exclude dismissed unless caller opts in
    if not include_dismissed:
        query = query.neq("review_status", "dismissed")

    # Territory filter by AE
    if ae_id:
        # Get hospital IDs for this AE
        assignments = (
            supabase.table("hospital_ae_assignments")
            .select("hospital_id")
            .eq("ae_id", ae_id)
            .execute()
        )
        hospital_ids = [a["hospital_id"] for a in (assignments.data or [])]
        if not hospital_ids:
            return []
        query = query.in_("hospital_id", hospital_ids)

    # TODO (Task 10): if not admin and no ae_id param, auto-filter to user's own territory

    result = query.execute()
    return result.data or []


@router.post("", status_code=201)
async def create_signal(
    signal_data: dict,
    background_tasks: BackgroundTasks,
    user: dict = Depends(get_required_user),
):
    """
    POST /api/v1/signals
    Validates signal_type. Applies confidence threshold to set review_status.
    Task 14 wires in urgent alert BackgroundTask.
    """
    supabase = get_supabase()

    # --- Validate signal_type ---
    signal_type = signal_data.get("signal_type")
    if not signal_type or signal_type not in VALID_SIGNAL_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"signal_type must be one of: {', '.join(sorted(VALID_SIGNAL_TYPES))}",
        )

    # --- Validate tier ---
    tier = signal_data.get("tier")
    if not tier or tier not in VALID_TIERS:
        raise HTTPException(
            status_code=422,
            detail=f"tier must be one of: {', '.join(VALID_TIERS)}",
        )

    # --- Validate hospital exists ---
    hospital_id = signal_data.get("hospital_id")
    if not hospital_id:
        raise HTTPException(status_code=422, detail="hospital_id is required")
    hospital_check = supabase.table("hospitals").select("id").eq("id", hospital_id).single().execute()
    if not hospital_check.data:
        raise HTTPException(status_code=404, detail=f"Hospital {hospital_id} not found")

    # --- Confidence threshold → review_status ---
    confidence = float(signal_data.get("confidence_score", 0.0))
    review_status = "pending" if confidence < 0.70 else None

    # --- Build insert payload ---
    insert_payload = {
        "hospital_id":      hospital_id,
        "signal_type":      signal_type,
        "tier":             tier,
        "confidence_score": confidence,
        "review_status":    review_status,
        "title":            signal_data.get("title"),
        "summary":          signal_data.get("summary"),
        "source_url":       str(signal_data.get("source_url")) if signal_data.get("source_url") else None,
        "source_name":      signal_data.get("source_name"),
        "published_date":   signal_data.get("published_date"),
    }
    # Remove None values so Supabase uses DB defaults
    insert_payload = {k: v for k, v in insert_payload.items() if v is not None}

    result = supabase.table("signals").insert(insert_payload).execute()
    if not result.data:
        raise HTTPException(status_code=500, detail="Failed to create signal")

    new_signal = result.data[0]
    logger.info(
        f"Signal created: {new_signal['id']} | type={signal_type} | tier={tier} "
        f"| confidence={confidence:.2f} | review_status={review_status}"
    )

    # --- Task 14: BackgroundTasks urgent alert ---
    # TODO (Task 14): if tier == "urgent":
    #     from app.services.alert_service import send_urgent_alert_for_signal
    #     background_tasks.add_task(send_urgent_alert_for_signal, new_signal["id"])

    return new_signal


@router.post("/{signal_id}/review")
async def review_signal(
    signal_id: str,
    review_data: dict,
    user: dict = Depends(get_admin_user),
):
    """
    POST /api/v1/signals/{signal_id}/review
    Task 9 full implementation — approve or dismiss a pending signal.
    Requires admin auth.
    """
    # TODO (Task 9): implement approve/dismiss logic
    raise HTTPException(status_code=501, detail="Signal review — implementation in Task 9")
