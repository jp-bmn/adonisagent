from __future__ import annotations
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Request
from app.core.config import get_settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Reads X-User-Id header and fetches the user from ae_users table.
    Returns None if header is missing or user not found.
    """
    user_id = request.headers.get("X-User-Id")
    if not user_id:
        return None
    try:
        supabase = get_supabase()
        result = supabase.table("ae_users").select("*").eq("id", user_id).single().execute()
        return result.data if result.data else None
    except Exception as e:
        logger.warning(f"Failed to fetch user {user_id}: {e}")
        return None


async def get_required_user(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """Requires a valid X-User-Id header; returns 401 otherwise."""
    if user is None:
        raise HTTPException(status_code=401, detail="X-User-Id header required and must match a valid user")
    return user


async def get_admin_user(user: dict = Depends(get_required_user)) -> dict:
    """Requires is_admin=true; returns 403 otherwise."""
    if not user.get("is_admin"):
        raise HTTPException(status_code=403, detail="Admin access required")
    return user


async def check_admin_api_key(request: Request) -> None:
    """
    Validates the X-API-Key header against INTERNAL_API_KEY.
    Used on /admin/* endpoints called by the scheduler or internal tooling.
    """
    settings = get_settings()
    key = request.headers.get("X-API-Key")
    if not key or key != settings.internal_api_key:
        raise HTTPException(status_code=403, detail="Invalid or missing X-API-Key")
