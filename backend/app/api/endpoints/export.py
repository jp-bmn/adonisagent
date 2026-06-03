"""
CSV export endpoint.
Task 13: Full implementation (HubSpot format, StreamingResponse).
"""
from __future__ import annotations
from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_required_user
import logging

router = APIRouter(prefix="/export", tags=["export"])
logger = logging.getLogger(__name__)


@router.get("/csv")
async def export_csv(
    ae_id: Optional[str] = Query(default=None),
    hospital_id: Optional[str] = Query(default=None),
    include_signals: bool = Query(default=True),
    user: dict = Depends(get_required_user),
):
    """
    GET /api/v1/export/csv
    HubSpot-format StreamingResponse. Full implementation in Task 13.
    """
    return {"message": "CSV export — implementation pending Task 13"}


@router.get("/contacts-count")
async def contacts_count(user: dict = Depends(get_required_user)):
    """GET /api/v1/export/contacts-count — Task 13"""
    return {"count": 0, "message": "contacts count — implementation pending Task 13"}
