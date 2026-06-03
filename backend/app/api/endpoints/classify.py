"""
Classification test endpoint (no auth — testing only).
Task 7: Full implementation.
"""
from fastapi import APIRouter
import logging

router = APIRouter(prefix="/classify", tags=["classify"])
logger = logging.getLogger(__name__)


@router.post("")
async def classify_article(payload: dict):
    """
    POST /api/v1/classify
    No auth — for testing classifier output only.
    Full implementation in Task 7.
    """
    # TODO (Task 7): from app.services.classifier import classify_signal; return await classify_signal(...)
    return {"message": "classify — implementation pending Task 7"}
