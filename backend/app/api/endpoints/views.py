"""
Digest view tracking endpoint.
Task 15: Full implementation (UTM closed-loop).
"""
import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter
from app.core.database import get_supabase

router = APIRouter(prefix="/digest-view", tags=["views"])
logger = logging.getLogger(__name__)


def is_valid_uuid(val) -> bool:
    if not val:
        return False
    try:
        uuid.UUID(str(val))
        return True
    except ValueError:
        return False


@router.post("")
async def record_digest_view(payload: dict):
    """
    POST /api/v1/digest-view
    No auth — called by the frontend on page load.
    Upserts digest_views record. Invalid digest_id or query error returns {"recorded": false}.
    """
    digest_id = payload.get("digest_id")
    ae_id = payload.get("ae_id")
    utm_source = payload.get("utm_source")

    # Graceful error handling for invalid/missing digest_id (returns {"recorded": false} with HTTP 200)
    if not is_valid_uuid(digest_id):
        logger.warning(f"Invalid or missing digest_id: {digest_id}")
        return {"recorded": False}

    if ae_id and not is_valid_uuid(ae_id):
        logger.warning(f"Invalid ae_id: {ae_id}")
        return {"recorded": False}

    supabase = get_supabase()
    try:
        # Verify the digest exists
        digest_check = (
            supabase.table("digests")
            .select("id")
            .eq("id", digest_id)
            .execute()
        )
        if not digest_check.data:
            logger.warning(f"Digest not found in database: {digest_id}")
            return {"recorded": False}

        # Verify the AE user exists if ae_id is provided
        if ae_id:
            user_check = (
                supabase.table("ae_users")
                .select("id")
                .eq("id", ae_id)
                .execute()
            )
            if not user_check.data:
                logger.warning(f"AE user not found in database: {ae_id}")
                return {"recorded": False}

        # Check for existing view for this digest + AE to deduplicate/upsert
        existing_view = None
        if ae_id:
            view_query = (
                supabase.table("digest_views")
                .select("*")
                .eq("digest_id", digest_id)
                .eq("ae_id", ae_id)
                .execute()
            )
            if view_query.data:
                existing_view = view_query.data[0]

        now_iso = datetime.now(timezone.utc).isoformat()
        if existing_view:
            # Update viewed_at and optionally utm_source
            update_data = {"viewed_at": now_iso}
            if utm_source:
                update_data["utm_source"] = utm_source
            
            update_res = (
                supabase.table("digest_views")
                .update(update_data)
                .eq("id", existing_view["id"])
                .execute()
            )
            if not update_res.data:
                return {"recorded": False}
        else:
            # Insert a new view record
            insert_data = {
                "digest_id": digest_id,
                "viewed_at": now_iso,
            }
            if ae_id:
                insert_data["ae_id"] = ae_id
            if utm_source:
                insert_data["utm_source"] = utm_source

            insert_res = (
                supabase.table("digest_views")
                .insert(insert_data)
                .execute()
            )
            if not insert_res.data:
                return {"recorded": False}

        return {"recorded": True}
    except Exception as e:
        logger.error(f"Error in record_digest_view: {e}")
        return {"recorded": False}
