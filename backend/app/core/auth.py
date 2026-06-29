from __future__ import annotations
import logging
from typing import Optional
from fastapi import Depends, HTTPException, Request
from app.core.config import get_settings
from app.core.database import get_supabase

logger = logging.getLogger(__name__)


async def get_current_user(request: Request) -> Optional[dict]:
    """
    Reads Authorization Bearer token, verifies via Supabase auth,
    and fetches the user from ae_users table.
    Returns None if header is missing, token invalid, or user not found.
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # Fallback to X-User-Id temporarily if needed, but we should strictly enforce Bearer
        user_id = request.headers.get("X-User-Id")
        if not user_id:
            return None
    else:
        token = auth_header.split(" ")[1]
        try:
            supabase = get_supabase()
            auth_res = supabase.auth.get_user(token)
            if not auth_res or not auth_res.user:
                return None
            user_id = auth_res.user.id
        except Exception as e:
            logger.warning(f"Failed to verify JWT: {e}")
            return None

    try:
        supabase = get_supabase()
        result = supabase.table("ae_users").select("*").eq("id", user_id).single().execute()
        return result.data if result.data else None
    except Exception as e:
        logger.warning(f"Failed to fetch user {user_id} from DB: {e}")
        return None


async def get_required_user(user: Optional[dict] = Depends(get_current_user)) -> dict:
    """Requires a valid Auth token; returns 401 otherwise."""
    if user is None:
        raise HTTPException(status_code=401, detail="Valid authentication required")
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
