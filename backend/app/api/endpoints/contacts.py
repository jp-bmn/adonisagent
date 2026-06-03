"""
Contact endpoints.
Task 11: Full implementation.
"""
from fastapi import APIRouter, Depends, Query
from app.core.auth import get_required_user, get_admin_user
import logging

router = APIRouter(prefix="/contacts", tags=["contacts"])
logger = logging.getLogger(__name__)


@router.get("")
async def list_contacts(
    hospital_id: str = Query(...),
    is_active: bool = Query(default=True),
    user: dict = Depends(get_required_user),
):
    """GET /api/v1/contacts — Task 11"""
    return {"message": "contacts list — implementation pending Task 11"}


@router.post("", status_code=201)
async def create_contact(contact_data: dict, user: dict = Depends(get_required_user)):
    """POST /api/v1/contacts — Task 11"""
    return {"message": "create contact — implementation pending Task 11"}


@router.patch("/{contact_id}")
async def update_contact(
    contact_id: str, update_data: dict, user: dict = Depends(get_required_user)
):
    """PATCH /api/v1/contacts/{contact_id} — Task 11"""
    return {"message": "update contact — implementation pending Task 11"}


@router.post("/{contact_id}/verify-linkedin")
async def verify_linkedin(
    contact_id: str, payload: dict, user: dict = Depends(get_required_user)
):
    """POST /api/v1/contacts/{contact_id}/verify-linkedin — Task 11"""
    return {"message": "verify linkedin — implementation pending Task 11"}


@router.delete("/{contact_id}")
async def delete_contact(contact_id: str, user: dict = Depends(get_admin_user)):
    """DELETE /api/v1/contacts/{contact_id} (soft delete, admin only) — Task 11"""
    return {"message": "soft delete contact — implementation pending Task 11"}
