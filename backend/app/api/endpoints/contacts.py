"""
Contact endpoints — Task 11 implementation.
Provides GET, POST, PATCH, DELETE (soft), and LinkedIn verification for hospital contacts.
"""
from __future__ import annotations

import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, Response

from app.core.auth import get_required_user, get_admin_user
from app.core.database import get_supabase
from app.models.schemas import Contact, ContactCreate, ContactUpdate, ContactLinkedInVerify

router = APIRouter(prefix="/contacts", tags=["contacts"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[Contact])
async def list_contacts(
    response: Response,
    hospital_id: str = Query(...),
    is_active: bool = Query(default=True),
    user: dict = Depends(get_required_user),
):
    """
    GET /api/v1/contacts
    
    Returns all contacts for a specific hospital.
    - If user is non-admin AE, verifies hospital is assigned to their territory.
    """
    supabase = get_supabase()

    # Territory check for non-admin AEs
    if not user.get("is_admin", False):
        assignments_res = (
            supabase.table("hospital_ae_assignments")
            .select("*")
            .eq("hospital_id", hospital_id)
            .eq("ae_id", str(user["id"]))
            .execute()
        )
        if not assignments_res.data:
            raise HTTPException(
                status_code=403,
                detail="Access denied: hospital not assigned to your territory"
            )

    # Fetch contacts
    res = (
        supabase.table("contacts")
        .select("*")
        .eq("hospital_id", hospital_id)
        .eq("is_active", is_active)
        .order("full_name")
        .execute()
    )
    response.headers["X-Total-Count"] = str(len(res.data or []))
    return res.data


@router.post("", response_model=Contact, status_code=201)
async def create_contact(payload: ContactCreate, user: dict = Depends(get_required_user)):
    """
    POST /api/v1/contacts
    
    Creates a new contact for a hospital.
    - Checks that hospital exists.
    - Verifies non-admin AE owns the hospital territory.
    - Performs duplicate checks (by name+hospital and by LinkedIn URL).
    """
    supabase = get_supabase()
    hosp_id_str = str(payload.hospital_id)

    # 1. Verify hospital exists
    hosp_check = supabase.table("hospitals").select("id").eq("id", hosp_id_str).execute()
    if not hosp_check.data:
        raise HTTPException(status_code=404, detail=f"Hospital {payload.hospital_id} not found")

    # 2. Territory check for non-admin AE
    if not user.get("is_admin", False):
        assignments_res = (
            supabase.table("hospital_ae_assignments")
            .select("*")
            .eq("hospital_id", hosp_id_str)
            .eq("ae_id", str(user["id"]))
            .execute()
        )
        if not assignments_res.data:
            raise HTTPException(
                status_code=403,
                detail="Access denied: cannot create contacts for hospitals outside your territory"
            )

    # 3. Duplicate checks
    # Check for existing contact by name + hospital first
    dup_name = (
        supabase.table("contacts")
        .select("*")
        .eq("hospital_id", hosp_id_str)
        .eq("full_name", payload.full_name)
        .execute()
    )
    
    existing_contact = dup_name.data[0] if dup_name.data else None

    # Ensure URL uniqueness if provided
    if payload.linkedin_url:
        dup_url = (
            supabase.table("contacts")
            .select("*")
            .eq("linkedin_url", str(payload.linkedin_url))
            .execute()
        )
        if dup_url.data:
            if not existing_contact or dup_url.data[0]["id"] != existing_contact["id"]:
                raise HTTPException(
                    status_code=409,
                    detail=f"Contact with LinkedIn URL '{payload.linkedin_url}' already exists"
                )

    if existing_contact:
        if existing_contact["is_active"]:
            raise HTTPException(
                status_code=409,
                detail=f"Contact '{payload.full_name}' already exists for this hospital"
            )
        else:
            # Reactivate contact
            update_payload = {
                "is_active": True,
                "role": payload.role,
                "prior_employer": payload.prior_employer,
                "linkedin_verified": payload.linkedin_verified
            }
            if payload.linkedin_url:
                update_payload["linkedin_url"] = str(payload.linkedin_url)
            
            # Strip Nones
            update_payload = {k: v for k, v in update_payload.items() if v is not None}
            
            update_res = supabase.table("contacts").update(update_payload).eq("id", existing_contact["id"]).execute()
            if not update_res.data:
                raise HTTPException(status_code=500, detail="Failed to reactivate contact")
                
            logger.info(f"Contact reactivated: {existing_contact['id']} ({payload.full_name})")
            return update_res.data[0]

    # 4. Insert contact
    insert_payload = {
        "hospital_id":       hosp_id_str,
        "full_name":         payload.full_name,
        "role":              payload.role,
        "prior_employer":    payload.prior_employer,
        "linkedin_url":      str(payload.linkedin_url) if payload.linkedin_url else None,
        "linkedin_verified": payload.linkedin_verified,
        "is_active":         True
    }
    # Strip Nones
    insert_payload = {k: v for k, v in insert_payload.items() if v is not None}

    insert_res = supabase.table("contacts").insert(insert_payload).execute()
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to create contact")

    new_contact = insert_res.data[0]
    logger.info(f"Contact created: {new_contact['id']} ({new_contact['full_name']})")
    return new_contact


@router.patch("/{contact_id}", response_model=Contact)
async def update_contact(
    contact_id: str,
    payload: ContactUpdate,
    user: dict = Depends(get_required_user)
):
    """
    PATCH /api/v1/contacts/{contact_id}
    
    Updates an existing contact's profile details.
    - Verifies contact exists.
    - Verifies non-admin AE owns the hospital territory.
    """
    supabase = get_supabase()

    # 1. Fetch contact
    contact_res = supabase.table("contacts").select("*").eq("id", contact_id).execute()
    if not contact_res.data:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    contact = contact_res.data[0]
    hosp_id_str = contact["hospital_id"]

    # 2. Territory check for non-admin AE
    if not user.get("is_admin", False):
        assignments_res = (
            supabase.table("hospital_ae_assignments")
            .select("*")
            .eq("hospital_id", hosp_id_str)
            .eq("ae_id", str(user["id"]))
            .execute()
        )
        if not assignments_res.data:
            raise HTTPException(
                status_code=403,
                detail="Access denied: cannot update contacts for hospitals outside your territory"
            )

    # 3. Update database
    update_data = payload.model_dump(exclude_unset=True)
    if not update_data:
        return contact

    # Stringify URL if present
    if "linkedin_url" in update_data and update_data["linkedin_url"] is not None:
        update_data["linkedin_url"] = str(update_data["linkedin_url"])

    update_res = supabase.table("contacts").update(update_data).eq("id", contact_id).execute()
    if not update_res.data:
        raise HTTPException(status_code=500, detail="Failed to update contact")

    updated_contact = update_res.data[0]
    logger.info(f"Contact updated: {contact_id}")
    return updated_contact


@router.post("/{contact_id}/verify-linkedin", response_model=Contact)
async def verify_linkedin(
    contact_id: str,
    payload: ContactLinkedInVerify,
    user: dict = Depends(get_required_user)
):
    """
    POST /api/v1/contacts/{contact_id}/verify-linkedin
    
    Sets the contact's LinkedIn URL and flags it as verified.
    - Verifies contact exists.
    - Verifies non-admin AE owns the hospital territory.
    """
    supabase = get_supabase()

    # 1. Fetch contact
    contact_res = supabase.table("contacts").select("*").eq("id", contact_id).execute()
    if not contact_res.data:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")
    contact = contact_res.data[0]
    hosp_id_str = contact["hospital_id"]

    # 2. Territory check for non-admin AE
    if not user.get("is_admin", False):
        assignments_res = (
            supabase.table("hospital_ae_assignments")
            .select("*")
            .eq("hospital_id", hosp_id_str)
            .eq("ae_id", str(user["id"]))
            .execute()
        )
        if not assignments_res.data:
            raise HTTPException(
                status_code=403,
                detail="Access denied: cannot verify contacts for hospitals outside your territory"
            )

    # 3. Update status
    update_res = (
        supabase.table("contacts")
        .update({
            "linkedin_url":      str(payload.linkedin_url),
            "linkedin_verified": True
        })
        .eq("id", contact_id)
        .execute()
    )
    if not update_res.data:
        raise HTTPException(status_code=500, detail="Failed to verify contact's LinkedIn URL")

    updated_contact = update_res.data[0]
    logger.info(f"LinkedIn verified for contact {contact_id}")
    return updated_contact


@router.delete("/{contact_id}", response_model=Contact)
async def delete_contact(contact_id: str, user: dict = Depends(get_admin_user)):
    """
    DELETE /api/v1/contacts/{contact_id} (soft delete, admin only)
    
    Soft-deletes a contact by marking is_active = False.
    """
    supabase = get_supabase()

    # 1. Fetch contact
    contact_res = supabase.table("contacts").select("id").eq("id", contact_id).execute()
    if not contact_res.data:
        raise HTTPException(status_code=404, detail=f"Contact {contact_id} not found")

    # 2. Soft delete
    delete_res = supabase.table("contacts").update({"is_active": False}).eq("id", contact_id).execute()
    if not delete_res.data:
        raise HTTPException(status_code=500, detail="Failed to delete contact")

    deleted_contact = delete_res.data[0]
    logger.info(f"Contact soft-deleted: {contact_id}")
    return deleted_contact
