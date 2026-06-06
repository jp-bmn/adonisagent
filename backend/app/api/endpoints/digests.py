"""
Digest endpoints — Task 8 implementation.
Provides GET /api/v1/digests (list digests) and POST /api/v1/digests/send (manual trigger).
"""
from __future__ import annotations

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException

from app.core.auth import get_required_user, get_admin_user
from app.core.database import get_supabase
from app.models.schemas import Digest
from app.services.digest_service import send_weekly_digest_to_all_aes

router = APIRouter(prefix="/digests", tags=["digests"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[Digest])
async def list_digests(user: dict = Depends(get_required_user)):
    """
    GET /api/v1/digests
    
    Returns all digests.
    - If user is admin (Danielle), returns all digests in the system.
    - If user is non-admin AE, returns only their own digests.
    """
    supabase = get_supabase()
    query = supabase.table("digests").select("*")
    
    if not user.get("is_admin", False):
        query = query.eq("ae_id", user["id"])
        
    query = query.order("sent_at", desc=True)
    res = query.execute()
    return res.data


@router.post("/send")
async def trigger_digest_send(admin_user: dict = Depends(get_admin_user)):
    """
    POST /api/v1/digests/send
    
    Admin-only endpoint to trigger sending digests manually to all AEs.
    Unlike the Monday scheduler job, this sends digests immediately based on
    current un-digested signals.
    """
    logger.info(f"Admin {admin_user.get('name')} triggered manual digest send")
    try:
        summary = await send_weekly_digest_to_all_aes()
        return summary
    except Exception as e:
        logger.error(f"Manual digest send failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

