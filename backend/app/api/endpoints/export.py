"""
CSV export endpoints - HubSpot compatible contacts export.
Task 13: Full implementation (StreamingResponse, HubSpot format, territory gated).
"""
from __future__ import annotations
import csv
import io
import logging
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse

from app.core.auth import get_required_user
from app.core.database import get_supabase

router = APIRouter(prefix="/export", tags=["export"])
logger = logging.getLogger(__name__)


def generate_csv_rows(contacts: list[dict], signals_map: dict[str, list[str]], include_signals: bool):
    """
    Generator that formats contacts into CSV rows and yields them as string chunks.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # HubSpot expected headers
    writer.writerow([
        "First Name",
        "Last Name",
        "Job Title",
        "Company Name",
        "Website URL",
        "LinkedIn Biodata URL",
        "Notes"
    ])
    yield output.getvalue()
    output.seek(0)
    output.truncate(0)

    for contact in contacts:
        # Split first and last name
        name_parts = (contact.get("full_name") or "").strip().split(maxsplit=1)
        first_name = name_parts[0] if name_parts else ""
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        job_title = contact.get("role") or ""

        # Retrieve hospital details from joined relationship
        hospital = contact.get("hospitals") or {}
        company_name = hospital.get("name") or ""
        website_url = hospital.get("website_url") or ""

        # LinkedIn biodata URL: verified contacts only
        linkedin_url = ""
        if contact.get("linkedin_verified") and contact.get("linkedin_url"):
            linkedin_url = str(contact.get("linkedin_url"))

        prior_emp = contact.get("prior_employer") or ""

        # Populate Notes field: include recent signals if requested
        if include_signals:
            recent_sigs = signals_map.get(contact["hospital_id"], [])
            sigs_str = "; ".join(recent_sigs) if recent_sigs else ""
            notes = f"Prior employer: {prior_emp}. | Recent signals: {sigs_str}"
        else:
            notes = f"Prior employer: {prior_emp}."

        writer.writerow([
            first_name,
            last_name,
            job_title,
            company_name,
            website_url,
            linkedin_url,
            notes
        ])
        yield output.getvalue()
        output.seek(0)
        output.truncate(0)


@router.get("/csv")
async def export_csv(
    ae_id: Optional[str] = Query(default=None),
    hospital_id: Optional[str] = Query(default=None),
    include_signals: bool = Query(default=True),
    user: dict = Depends(get_required_user),
):
    """
    GET /api/v1/export/csv
    HubSpot-format StreamingResponse.
    Territory-gated: Non-admin AEs can only export their assigned territory.
    """
    supabase = get_supabase()

    # 1. Territory filtering logic
    if not user.get("is_admin", False):
        if ae_id and ae_id != str(user["id"]):
            raise HTTPException(
                status_code=403,
                detail="Access denied: cannot export another AE's territory"
            )
        ae_id = str(user["id"])

        # Fetch AE's territory assignments
        assignments_res = (
            supabase.table("hospital_ae_assignments")
            .select("hospital_id")
            .eq("ae_id", ae_id)
            .execute()
        )
        allowed_hospital_ids = [a["hospital_id"] for a in (assignments_res.data or [])]
        if not allowed_hospital_ids:
            # Empty territory, return empty CSV
            return StreamingResponse(
                generate_csv_rows([], {}, include_signals),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=contacts_export.csv"}
            )

        if hospital_id:
            if hospital_id not in allowed_hospital_ids:
                raise HTTPException(
                    status_code=403,
                    detail="Access denied: hospital is outside your territory"
                )
            filter_hospital_ids = [hospital_id]
        else:
            filter_hospital_ids = allowed_hospital_ids
    else:
        # Admins can filter by any AE or hospital
        if ae_id:
            assignments_res = (
                supabase.table("hospital_ae_assignments")
                .select("hospital_id")
                .eq("ae_id", ae_id)
                .execute()
            )
            allowed_hospital_ids = [a["hospital_id"] for a in (assignments_res.data or [])]
            if not allowed_hospital_ids:
                filter_hospital_ids = []
            elif hospital_id:
                if hospital_id not in allowed_hospital_ids:
                    filter_hospital_ids = []  # mismatch
                else:
                    filter_hospital_ids = [hospital_id]
            else:
                filter_hospital_ids = allowed_hospital_ids
        elif hospital_id:
            filter_hospital_ids = [hospital_id]
        else:
            filter_hospital_ids = None

    # 2. Query contacts
    contacts_query = (
        supabase.table("contacts")
        .select("*, hospitals(name, website_url)")
        .eq("is_active", True)
    )
    if filter_hospital_ids is not None:
        if not filter_hospital_ids:
            return StreamingResponse(
                generate_csv_rows([], {}, include_signals),
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=contacts_export.csv"}
            )
        contacts_query = contacts_query.in_("hospital_id", filter_hospital_ids)

    try:
        contacts_res = contacts_query.execute()
        contacts = contacts_res.data or []
    except Exception as e:
        logger.error(f"Failed to fetch contacts for export: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve contacts")

    # 3. Retrieve recent signals for the Notes field if requested
    signals_map = {}
    if include_signals and contacts:
        unique_hospital_ids = list({c["hospital_id"] for c in contacts})
        for hid in unique_hospital_ids:
            try:
                sig_res = (
                    supabase.table("signals")
                    .select("summary")
                    .eq("hospital_id", hid)
                    .order("created_at", desc=True)
                    .limit(2)
                    .execute()
                )
                signals_map[hid] = [
                    s["summary"] for s in (sig_res.data or []) if s.get("summary")
                ]
            except Exception as e:
                logger.warning(f"Failed to fetch signals for hospital {hid}: {e}")
                signals_map[hid] = []

    return StreamingResponse(
        generate_csv_rows(contacts, signals_map, include_signals),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contacts_export.csv"}
    )


@router.get("/contacts-count")
async def contacts_count(
    ae_id: Optional[str] = Query(default=None),
    hospital_id: Optional[str] = Query(default=None),
    user: dict = Depends(get_required_user),
):
    """
    GET /api/v1/export/contacts-count
    Returns count of exportable contacts matching the criteria and territory restrictions.
    """
    supabase = get_supabase()

    # Territory filtering logic
    if not user.get("is_admin", False):
        if ae_id and ae_id != str(user["id"]):
            raise HTTPException(status_code=403, detail="Access denied")
        ae_id = str(user["id"])

        assignments_res = (
            supabase.table("hospital_ae_assignments")
            .select("hospital_id")
            .eq("ae_id", ae_id)
            .execute()
        )
        allowed_hospital_ids = [a["hospital_id"] for a in (assignments_res.data or [])]
        if not allowed_hospital_ids:
            return {"count": 0}

        if hospital_id:
            if hospital_id not in allowed_hospital_ids:
                raise HTTPException(status_code=403, detail="Access denied")
            filter_hospital_ids = [hospital_id]
        else:
            filter_hospital_ids = allowed_hospital_ids
    else:
        if ae_id:
            assignments_res = (
                supabase.table("hospital_ae_assignments")
                .select("hospital_id")
                .eq("ae_id", ae_id)
                .execute()
            )
            allowed_hospital_ids = [a["hospital_id"] for a in (assignments_res.data or [])]
            if not allowed_hospital_ids:
                return {"count": 0}
            if hospital_id:
                if hospital_id not in allowed_hospital_ids:
                    return {"count": 0}
                filter_hospital_ids = [hospital_id]
            else:
                filter_hospital_ids = allowed_hospital_ids
        elif hospital_id:
            filter_hospital_ids = [hospital_id]
        else:
            filter_hospital_ids = None

    # Count matching active contacts
    query = supabase.table("contacts").select("id", count="exact").eq("is_active", True)
    if filter_hospital_ids is not None:
        if not filter_hospital_ids:
            return {"count": 0}
        query = query.in_("hospital_id", filter_hospital_ids)

    try:
        res = query.execute()
        return {"count": res.count or 0}
    except Exception as e:
        logger.error(f"Failed to count exportable contacts: {e}")
        raise HTTPException(status_code=500, detail="Failed to count contacts")
