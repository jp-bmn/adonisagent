"""
Digest endpoints.
Task 8: Full implementation.
"""
from fastapi import APIRouter, Depends
from app.core.auth import get_required_user, get_admin_user
import logging

router = APIRouter(prefix="/digests", tags=["digests"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_digests(user: dict = Depends(get_required_user)):
    """GET /api/v1/digests — Task 8"""
    return {"message": "digests list — implementation pending Task 8"}
