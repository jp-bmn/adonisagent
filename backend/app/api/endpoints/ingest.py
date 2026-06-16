"""
Batch signal ingestion endpoint for Michael's scraper pipeline.

POST /api/v1/signals/batch
Auth: Bearer <INTERNAL_API_KEY>

Accepts Michael's payload format, resolves hospital_name → hospital_id,
maps his field names to our schema, and returns inserted/duplicate/rejected counts.
"""
from __future__ import annotations
from typing import Optional, Any
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import get_settings
from app.core.database import get_supabase
import logging
import re
from datetime import date, datetime

router = APIRouter(prefix="/signals", tags=["signals-batch"])
logger = logging.getLogger(__name__)

bearer_scheme = HTTPBearer(auto_error=False)

# ---------------------------------------------------------------------------
# Michael's matched_topics → our signal_type mapping
# ---------------------------------------------------------------------------
TOPIC_TO_SIGNAL_TYPE: dict[str, str] = {
    # Leadership / executive changes
    "leadership":           "leadership_change",
    "leadership_change":    "leadership_change",
    "executive":            "leadership_change",
    "cro":                  "leadership_change",
    "cfo":                  "leadership_change",
    "vp_revenue":           "leadership_change",
    # RCM / hiring
    "rcm_hiring":           "rcm_hiring_spike",
    "hiring_spike":         "rcm_hiring_spike",
    "revenue_cycle_hiring": "rcm_hiring_spike",
    # Epic / EHR
    "epic":                 "epic_go_live",
    "epic_go_live":         "epic_go_live",
    "ehr_go_live":          "epic_go_live",
    "post_go_live":         "post_golive_friction",
    "post_golive_friction": "post_golive_friction",
    # M&A
    "acquisition":          "ma_acquisition",
    "merger":               "ma_acquisition",
    "ma_acquisition":       "ma_acquisition",
    # Vendor
    "vendor_change":        "vendor_change",
    "vendor_dispute":       "vendor_dispute",
    "vendor":               "vendor_change",
    # Restructuring
    "restructuring":        "restructuring",
    "layoffs":              "restructuring",
    # Financial
    "financial":            "financial_event",
    "financial_event":      "financial_event",
    "earnings":             "financial_event",
    # AI / automation
    "ai_adoption":          "ai_adoption_outside_rcm",
    "automation":           "automation_proof",
    "named_automation_owner": "named_automation_owner",
    "thought_leadership":   "thought_leadership",
    # New hospital
    "new_hospital":         "new_hospital_launch",
    "expansion":            "new_hospital_launch",
}

VALID_SIGNAL_TYPES = {
    "leadership_change", "rcm_hiring_spike", "epic_go_live", "post_golive_friction",
    "ma_acquisition", "vendor_change", "vendor_dispute", "restructuring",
    "new_hospital_launch", "financial_event", "ai_adoption_outside_rcm",
    "automation_proof", "named_automation_owner", "thought_leadership", "filtered_out",
}


def _resolve_signal_type(matched_topics: list[str]) -> str:
    """Map Michael's matched_topics list to our signal_type enum. First match wins."""
    for topic in (matched_topics or []):
        normalized = topic.lower().replace("-", "_").replace(" ", "_")
        if normalized in TOPIC_TO_SIGNAL_TYPE:
            return TOPIC_TO_SIGNAL_TYPE[normalized]
        # Direct match against our enum
        if normalized in VALID_SIGNAL_TYPES:
            return normalized
    return "filtered_out"


def _parse_date(raw: Optional[str]) -> Optional[str]:
    """Parse published_at_raw into a date string YYYY-MM-DD. Returns None on failure."""
    if not raw:
        return None
    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw.strip(), fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    # Try extracting YYYY-MM-DD from any string
    match = re.search(r"\d{4}-\d{2}-\d{2}", raw)
    return match.group(0) if match else None


def _infer_tier(signal_type: str, matched_topics: list[str]) -> str:
    """Infer tier from signal_type. Rules engine will override this in Task 5."""
    urgent_types = {
        "leadership_change", "vendor_dispute", "ma_acquisition",
        "epic_go_live", "post_golive_friction", "restructuring",
        "rcm_hiring_spike", "vendor_change",
    }
    worth_knowing_types = {
        "financial_event", "ai_adoption_outside_rcm",
        "automation_proof", "named_automation_owner", "thought_leadership",
        "new_hospital_launch",
    }
    if signal_type in urgent_types:
        return "urgent"
    if signal_type in worth_knowing_types:
        return "worth_knowing"
    return "filtered_out"


def _hospital_aliases(hospital: str) -> tuple[str, ...]:
    mapping = {
        "newyork-presbyterian": (
            "newyork-presbyterian",
            "new york-presbyterian",
            "new york presbyterian",
            "nyp",
        ),
        "new york-presbyterian": (
            "newyork-presbyterian",
            "new york-presbyterian",
            "new york presbyterian",
            "nyp",
        ),
        "umass memorial": (
            "umass memorial",
            "umass",
            "u mass memorial",
        ),
        "ascension": (
            "ascension",
            "ascension health",
        ),
        "university of arkansas": (
            "university of arkansas",
            "uams",
            "uams health",
            "university of arkansas for medical sciences",
        ),
        "university of arkansas medical sciences": (
            "university of arkansas",
            "uams",
            "uams health",
            "university of arkansas for medical sciences",
        ),
        "university of arkansas for medical sciences": (
            "university of arkansas",
            "uams",
            "uams health",
            "university of arkansas for medical sciences",
        ),
        "commonspirit": (
            "commonspirit",
            "commonspirit health",
            "chi",
            "catholic health initiatives",
            "dignity health",
        ),
        "commonspirit health": (
            "commonspirit",
            "commonspirit health",
            "chi",
            "catholic health initiatives",
            "dignity health",
        ),
        "jefferson health": (
            "jefferson health",
            "jefferson",
            "jeff",
            "thomas jefferson university",
            "thomas jefferson university hospitals",
        ),
        "jefferson": (
            "jefferson health",
            "jefferson",
            "jeff",
            "thomas jefferson university",
            "thomas jefferson university hospitals",
        ),
    }
    key = hospital.lower().strip()
    return mapping.get(key, (key,))


def _mentions_target_hospital(hospital_name: str, title: str, summary: str) -> bool:
    blob = f"{title or ''} {summary or ''}".lower()
    aliases = _hospital_aliases(hospital_name)
    return any(alias in blob for alias in aliases)


async def _verify_bearer(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> None:
    """Validates Bearer token against INTERNAL_API_KEY."""
    settings = get_settings()
    token = None
    if credentials:
        token = credentials.credentials
    # Also accept X-API-Key header for backward compat
    if not token:
        token = request.headers.get("X-API-Key")
    if not token or token != settings.internal_api_key:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing Bearer token. Set Authorization: Bearer <INTERNAL_API_KEY>",
        )


@router.post("/batch", status_code=200)
async def ingest_signal_batch(
    payload: dict,
    request: Request,
    _: None = Depends(_verify_bearer),
):
    """
    POST /api/v1/signals/batch

    Accepts Michael's scraper pipeline payload and ingests signals into Supabase.

    Request body:
    {
      "run_context": {
        "run_id": str,
        "run_date": str,
        "scraper_version": str,
        "hospitals_scraped": int
      },
      "signals": [
        {
          "hospital_name": str,        # resolved to hospital_id via DB lookup
          "title": str,
          "source_name": str,
          "source_url": str,
          "published_at_raw": str,     # any date format, parsed to YYYY-MM-DD
          "excerpt": str,              # mapped to summary
          "matched_topics": [str],     # mapped to signal_type
          "extraction_stage": str,
          "dedup_applied": bool,
          "recency_applied": bool
        }
      ]
    }

    Response:
    {
      "run_id": str,
      "received": int,
      "inserted": int,
      "duplicates": int,
      "rejected": int,
      "details": [{ "index": int, "status": str, "reason": str, "signal_id": str|null }]
    }
    """
    supabase = get_supabase()
    run_context = payload.get("run_context", {})
    signals_raw = payload.get("signals", [])

    run_id = run_context.get("run_id", "unknown")
    logger.info(
        f"Batch ingest received | run_id={run_id} | "
        f"signal_count={len(signals_raw)} | "
        f"scraper_version={run_context.get('scraper_version', 'unknown')}"
    )

    if not isinstance(signals_raw, list):
        raise HTTPException(status_code=422, detail="`signals` must be a list")

    # ------------------------------------------------------------------
    # Pre-load hospital name → id map (single query)
    # ------------------------------------------------------------------
    hospitals_res = supabase.table("hospitals").select("id, name").execute()
    hospital_name_map: dict[str, str] = {}
    hospital_id_to_name: dict[str, str] = {}
    for h in (hospitals_res.data or []):
        # Normalize: lowercase, strip whitespace for fuzzy matching
        hospital_name_map[h["name"].lower().strip()] = h["id"]
        # Also map common abbreviations
        hospital_name_map[h["name"]] = h["id"]
        # Map ID to official name
        hospital_id_to_name[h["id"]] = h["name"]

    def _resolve_hospital_id(name: str) -> Optional[str]:
        if not name:
            return None
        # Exact match first
        if name in hospital_name_map:
            return hospital_name_map[name]
        # Case-insensitive
        lower = name.lower().strip()
        if lower in hospital_name_map:
            return hospital_name_map[lower]
        # Partial match — find first hospital whose name contains the input
        for hname, hid in hospital_name_map.items():
            if lower in hname.lower() or hname.lower() in lower:
                return hid
        return None

    # ------------------------------------------------------------------
    # Process each signal
    # ------------------------------------------------------------------
    inserted = 0
    duplicates = 0
    rejected = 0
    details = []

    for idx, sig in enumerate(signals_raw):
        detail: dict[str, Any] = {"index": idx, "status": "unknown", "reason": None, "signal_id": None}

        # --- Resolve hospital ---
        hospital_name = sig.get("hospital_name", "")
        hospital_id = _resolve_hospital_id(hospital_name)
        if not hospital_id:
            rejected += 1
            detail.update(status="rejected", reason=f"Unknown hospital: '{hospital_name}'")
            details.append(detail)
            logger.warning(f"Signal idx={idx} rejected — unknown hospital: '{hospital_name}'")
            continue

        # --- Map fields ---
        matched_topics = sig.get("matched_topics") or []
        signal_type = _resolve_signal_type(matched_topics)
        tier = _infer_tier(signal_type, matched_topics)
        published_date = _parse_date(sig.get("published_at_raw"))
        summary = sig.get("excerpt") or ""
        source_url = sig.get("source_url") or ""
        source_name = sig.get("source_name") or ""

        # --- Required & Meaningful Title ---
        title = sig.get("title") or ""
        normalized_title = title.lower().replace("_", " ").replace("-", " ").strip()
        is_generic = (
            not title or
            normalized_title in {t.replace("_", " ") for t in VALID_SIGNAL_TYPES} or
            normalized_title in ("document", "signal", "pdf filing", "low confidence signal", "classification error")
        )
        if is_generic:
            if summary:
                words = summary.split()
                fallback_title = " ".join(words[:10])
                if len(fallback_title) > 80:
                    fallback_title = fallback_title[:77] + "..."
                title = fallback_title
            else:
                title = f"{hospital_name} {signal_type.replace('_', ' ').title()} Update"

        if not title:
            rejected += 1
            detail.update(status="rejected", reason="title is required")
            details.append(detail)
            continue

        # --- Relevance check ---
        # Only attribute/save if article references the specific health system.
        official_hospital_name = hospital_id_to_name.get(hospital_id, hospital_name)
        if not _mentions_target_hospital(official_hospital_name, title, summary) and not _mentions_target_hospital(hospital_name, title, summary):
            rejected += 1
            detail.update(
                status="rejected",
                reason=f"Signal does not reference target hospital '{official_hospital_name}'"
            )
            details.append(detail)
            logger.warning(
                f"Signal idx={idx} rejected — no reference to hospital '{official_hospital_name}' in title or summary."
            )
            continue


        # Truncate to schema limits
        title   = title[:200]
        summary = summary[:1000]

        # Confidence: Michael's pipeline is trusted, default 0.75 (auto-approved)
        # TODO (Task 7): call classify_signal() here for proper scoring
        confidence_score = 0.75
        review_status = None  # auto-approved at 0.75

        # --- Deduplication: check source_url + hospital_id ---
        if source_url:
            dup_check = (
                supabase.table("signals")
                .select("id")
                .eq("hospital_id", hospital_id)
                .eq("source_url", source_url)
                .execute()
            )
            if dup_check.data:
                duplicates += 1
                detail.update(
                    status="duplicate",
                    reason="Signal with same source_url + hospital_id already exists",
                    signal_id=dup_check.data[0]["id"],
                )
                details.append(detail)
                continue

        # --- Insert ---
        insert_payload = {
            "hospital_id":      hospital_id,
            "signal_type":      signal_type,
            "tier":             tier,
            "confidence_score": confidence_score,
            "review_status":    review_status,
            "title":            title,
            "summary":          summary or None,
            "why_it_matters":   sig.get("why_it_matters"),
            "source_url":       source_url or None,
            "source_name":      source_name or None,
            "published_date":   published_date,
        }
        # Remove None values
        insert_payload = {k: v for k, v in insert_payload.items() if v is not None}

        try:
            result = supabase.table("signals").insert(insert_payload).execute()
            new_id = result.data[0]["id"] if result.data else None
            inserted += 1
            detail.update(status="inserted", signal_id=new_id)
            logger.info(
                f"Signal inserted | id={new_id} | hospital={hospital_name} "
                f"| type={signal_type} | tier={tier}"
            )
        except Exception as e:
            rejected += 1
            detail.update(status="rejected", reason=f"DB insert error: {str(e)}")
            logger.error(f"Signal idx={idx} insert failed: {e}")

        details.append(detail)

    logger.info(
        f"Batch complete | run_id={run_id} | "
        f"received={len(signals_raw)} inserted={inserted} "
        f"duplicates={duplicates} rejected={rejected}"
    )

    return {
        "run_id":     run_id,
        "received":   len(signals_raw),
        "inserted":   inserted,
        "duplicates": duplicates,
        "rejected":   rejected,
        "details":    details,
    }
