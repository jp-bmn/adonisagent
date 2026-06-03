"""
Digest view tracking endpoint.
Task 15: Full implementation (UTM closed-loop).
"""
from fastapi import APIRouter
import logging

router = APIRouter(prefix="/digest-view", tags=["views"])
logger = logging.getLogger(__name__)


@router.post("")
async def record_digest_view(payload: dict):
    """
    POST /api/v1/digest-view
    No auth — called by the frontend on page load.
    Upserts digest_views record. Invalid digest_id returns {"recorded": false}.
    Full implementation in Task 15.
    """
    return {"recorded": False, "message": "digest-view — implementation pending Task 15"}
