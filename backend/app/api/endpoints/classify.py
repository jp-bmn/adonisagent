"""
Classification endpoint — Task 7 full implementation.
POST /api/v1/classify — no auth (testing only).
"""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import ClassifyRequest, ClassifyResponse
from app.services.classifier import classify_signal

router = APIRouter(prefix="/classify", tags=["classify"])
logger = logging.getLogger(__name__)


@router.post("", response_model=ClassifyResponse)
async def classify_article(payload: ClassifyRequest):
    """
    POST /api/v1/classify
    No auth — for testing classifier output directly.

    Runs the two-stage classifier pipeline:
      1. Rules engine (deterministic, zero cost)
      2. Claude claude-sonnet-4-20250514 (only if rules engine doesn't match)

    Request body:
        article_text:      Full article text
        hospital_name:     Hospital name for context
        source_name:       Publication name
        signal_type_hint:  Optional hint from upstream pipeline

    Returns ClassifyResponse with signal_type, tier, confidence_score,
    title, summary, why_relevant, classification_source.
    """
    if not payload.article_text or not payload.article_text.strip():
        raise HTTPException(status_code=422, detail="article_text must not be empty")

    if not payload.hospital_name or not payload.hospital_name.strip():
        raise HTTPException(status_code=422, detail="hospital_name must not be empty")

    logger.info(
        f"Classify request: hospital='{payload.hospital_name}' "
        f"source='{payload.source_name}' text_len={len(payload.article_text)}"
    )

    result = await classify_signal(
        article_text     = payload.article_text,
        hospital_name    = payload.hospital_name,
        source_name      = payload.source_name or "",
        signal_type_hint = payload.signal_type_hint,
    )

    logger.info(
        f"Classify result: type={result.signal_type} tier={result.tier} "
        f"confidence={result.confidence_score:.2f} source={result.classification_source}"
    )

    return ClassifyResponse(
        signal_type            = result.signal_type,
        tier                   = result.tier,
        confidence_score       = result.confidence_score,
        title                  = result.title,
        summary                = result.summary,
        why_relevant           = result.why_relevant,
        classification_source  = result.classification_source,
    )
