"""Generate leadership contact leads and candidate LinkedIn URLs from classified signals."""

from __future__ import annotations

import json
from pathlib import Path

from adonis_data.clients.serper import SerperClient
from adonis_data.config import load_settings
from adonis_data.enrich.contact_leads import extract_contact_leads
from adonis_data.enrich.linkedin_discovery import discover_linkedin_url, score_linkedin_match


def run() -> Path:
    settings = load_settings()
    serper = SerperClient(api_key=settings.serper_api_key, timeout_seconds=settings.request_timeout_seconds)

    classified_path = Path("outputs/day2_classified_candidates.json")
    raw_path = Path("outputs/day1_raw_signals.json")
    quality_path = Path("outputs/day2_signal_quality_log.json")

    signal_rows: list[dict[str, object]] = []
    if classified_path.exists():
        classified_payload = json.loads(classified_path.read_text(encoding="utf-8"))
        classified_rows = classified_payload.get("signals", [])
        if isinstance(classified_rows, list):
            signal_rows.extend([row for row in classified_rows if isinstance(row, dict)])

    if raw_path.exists():
        raw_payload = json.loads(raw_path.read_text(encoding="utf-8"))
        raw_rows = raw_payload.get("signals", [])
        if isinstance(raw_rows, list):
            signal_rows.extend([row for row in raw_rows if isinstance(row, dict)])

    if quality_path.exists():
        quality_payload = json.loads(quality_path.read_text(encoding="utf-8"))
        skipped_rows = quality_payload.get("skipped_examples", [])
        if isinstance(skipped_rows, list):
            signal_rows.extend([row for row in skipped_rows if isinstance(row, dict)])

    if not signal_rows:
        raise FileNotFoundError(
            "Missing signal inputs. Run collection first to generate outputs/day1_raw_signals.json."
        )

    leads = extract_contact_leads(signal_rows)

    enriched: list[dict[str, object]] = []
    found_count = 0
    high_confidence_count = 0
    for lead in leads:
        query, linkedin_url = discover_linkedin_url(
            serper=serper,
            full_name=lead.full_name,
            hospital=lead.hospital,
            num_results=5,
        )
        if linkedin_url:
            found_count += 1

        match_score, match_reason = score_linkedin_match(
            full_name=lead.full_name,
            hospital=lead.hospital,
            linkedin_url=linkedin_url,
        )
        recommended_for_manual_review = bool(linkedin_url) and match_score >= 0.70
        if recommended_for_manual_review:
            high_confidence_count += 1

        enriched.append(
            {
                "full_name": lead.full_name,
                "hospital": lead.hospital,
                "role_hint": lead.role_hint,
                "source_title": lead.source_title,
                "discovery_query": query,
                "linkedin_url": linkedin_url,
                "linkedin_verified": False,
                "linkedin_match_score": round(match_score, 3),
                "match_reason": match_reason,
                "recommended_for_manual_review": recommended_for_manual_review,
            }
        )

    output = {
        "lead_count": len(leads),
        "linkedin_found_count": found_count,
        "linkedin_missing_count": max(0, len(leads) - found_count),
        "recommended_for_manual_review_count": high_confidence_count,
        "leads": enriched,
    }

    out_path = Path("outputs/day2_contact_leads.json")
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    path = run()
    print(f"Wrote contact leads to {path}")
