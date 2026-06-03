"""
/me and AE user endpoints.
Task 10: Full implementation.
Task 15: last_viewed_digest added to ae-users response.
"""
from fastapi import APIRouter, Depends
from app.core.auth import get_required_user, get_admin_user
import logging

router = APIRouter(tags=["users"])
logger = logging.getLogger(__name__)


@router.get("/me")
async def get_me(user: dict = Depends(get_required_user)):
    """
    GET /api/v1/me
    Returns current user profile + assigned hospitals + new signals this week.
    Full implementation in Task 10.
    """
    # TODO (Task 10): join hospitals, count signals in last 7 days
    return {"id": user.get("id"), "name": user.get("name"), "is_admin": user.get("is_admin")}


@router.get("/ae-users")
async def list_ae_users(user: dict = Depends(get_admin_user)):
    """
    GET /api/v1/ae-users (admin only)
    Returns all AEs with assigned hospitals and last_viewed_digest.
    Full implementation in Task 10. last_viewed_digest added in Task 15.
    """
    # TODO (Task 10): return all is_admin=false users with hospital assignments
    # TODO (Task 15): add last_viewed_digest from digest_views
    return {"message": "ae-users — implementation pending Task 10"}


@router.post("/hospital-ae-assignments", status_code=201)
async def create_assignment(payload: dict, user: dict = Depends(get_admin_user)):
    """
    POST /api/v1/hospital-ae-assignments (admin only)
    Full implementation in Task 10.
    """
    # TODO (Task 10): check for existing assignment (409), create and return 201
    return {"message": "assignment — implementation pending Task 10"}


@router.get("/digest-analytics")
async def digest_analytics(user: dict = Depends(get_admin_user)):
    """
    GET /api/v1/digest-analytics (admin only)
    Returns per-digest engagement for the last 30 days.
    Full implementation in Task 15.
    """
    # TODO (Task 15): query digests + digest_views, compute time_to_open_minutes
    return {"message": "digest analytics — implementation pending Task 15"}
