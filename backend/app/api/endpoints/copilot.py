"""
Co-pilot chat stub endpoint — Phase 3.
POST /api/v1/copilot
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, Depends
from app.models.schemas import CopilotRequest, CopilotResponse
from app.core.auth import get_required_user

router = APIRouter(prefix="/copilot", tags=["copilot"])
logger = logging.getLogger(__name__)


@router.post("", response_model=CopilotResponse)
async def ask_copilot(
    payload: CopilotRequest,
    user: dict = Depends(get_required_user),
):
    """
    POST /api/v1/copilot
    
    Receives user co-pilot chat query and context, and returns a mocked response.
    Requires a valid X-User-Id header.
    """
    logger.info(
        f"Co-pilot request: user_id='{payload.user_id}' "
        f"authenticated_as='{user.get('id')}' "
        f"message='{payload.message}' "
        f"history_length={len(payload.history)} "
        f"context_hospital_id='{payload.context_hospital_id}'"
    )

    return CopilotResponse(
        reply="I am the Adonis Co-pilot stub. Once integrated with Sonnet, I will assist you with territory insights.",
        sources=[],
    )
