"""Generate leadership contact leads and candidate LinkedIn URLs from classified signals."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from adonis_data.clients.serper import SerperClient
from adonis_data.config import load_settings
from adonis_data.enrich.contact_leads import extract_contact_leads
from adonis_data.enrich.linkedin_discovery import discover_best_linkedin_match


def _write_lead_review_markdown(leads: list[dict[str, object]]) -> Path:
    ranked = sorted(
        leads,
        key=lambda row: float(row.get("linkedin_match_score", 0.0)),
        reverse=True,
    )

    lines = [
        "# Day 2 LinkedIn Lead Review",
        "",
        "| Rank | Name | Hospital | Score | Bucket | Recommended | URL |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for index, row in enumerate(ranked, start=1):
        url = str(row.get("linkedin_url", ""))
        url_cell = "" if not url else f"[profile]({url})"
        lines.append(
            "| "
            f"{index} | "
            f"{row.get('full_name', '')} | "
            f"{row.get('hospital', '')} | "
            f"{row.get('linkedin_match_score', '')} | "
            f"{row.get('match_bucket', '')} | "
            f"{row.get('recommended_for_manual_review', False)} | "
            f"{url_cell} |"
        )

    review_path = Path("outputs/day2_contact_leads_review.md")
    review_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return review_path


def _write_lead_review_csv(leads: list[dict[str, object]]) -> Path:
    ranked = sorted(
        leads,
        key=lambda row: float(row.get("linkedin_match_score", 0.0)),
        reverse=True,
    )

    csv_path = Path("outputs/day2_contact_leads_review.csv")
    with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "rank",
                "full_name",
                "hospital",
                "role_hint",
                "linkedin_match_score",
                "match_bucket",
                "recommended_for_manual_review",
                "match_reason",
                "linkedin_url",
            ],
        )
        writer.writeheader()
        for index, row in enumerate(ranked, start=1):
            writer.writerow(
                {
                    "rank": index,
                    "full_name": row.get("full_name", ""),
                    "hospital": row.get("hospital", ""),
                    "role_hint": row.get("role_hint", ""),
                    "linkedin_match_score": row.get("linkedin_match_score", ""),
                    "match_bucket": row.get("match_bucket", ""),
                    "recommended_for_manual_review": row.get(
                        "recommended_for_manual_review", False
                    ),
                    "match_reason": row.get("match_reason", ""),
                    "linkedin_url": row.get("linkedin_url", ""),
                }
            )
    return csv_path


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
    recommended_count = 0
    high_confidence_count = 0
    medium_confidence_count = 0
    low_confidence_count = 0
    missing_match_count = 0
    filtered_low_score_count = 0
    for lead in leads:
        match = discover_best_linkedin_match(
            serper=serper,
            full_name=lead.full_name,
            hospital=lead.hospital,
            num_results=5,
        )

        linkedin_url = match.linkedin_url
        match_bucket = match.match_bucket
        match_reason = match.match_reason
        if linkedin_url and match.match_score < settings.linkedin_min_match_score:
            linkedin_url = ""
            match_bucket = "missing"
            match_reason = (
                f"{match.match_reason}|below_minimum_threshold={settings.linkedin_min_match_score:.2f}"
            )
            filtered_low_score_count += 1

        if linkedin_url:
            found_count += 1

        recommended_for_manual_review = bool(linkedin_url) and (
            match.match_score >= settings.linkedin_recommended_match_score
        )
        if recommended_for_manual_review:
            recommended_count += 1
        if match_bucket == "high":
            high_confidence_count += 1
        elif match_bucket == "medium":
            medium_confidence_count += 1
        elif match_bucket == "low":
            low_confidence_count += 1
        elif match_bucket == "missing":
            missing_match_count += 1

        enriched.append(
            {
                "full_name": lead.full_name,
                "hospital": lead.hospital,
                "role_hint": lead.role_hint,
                "source_title": lead.source_title,
                "discovery_query": match.query,
                "linkedin_url": linkedin_url,
                "linkedin_verified": False,
                "linkedin_match_score": match.match_score,
                "match_reason": match_reason,
                "match_bucket": match_bucket,
                "recommended_for_manual_review": recommended_for_manual_review,
            }
        )

    review_path = _write_lead_review_markdown(enriched)
    review_csv_path = _write_lead_review_csv(enriched)

    output = {
        "lead_count": len(leads),
        "linkedin_found_count": found_count,
        "linkedin_missing_count": max(0, len(leads) - found_count),
        "recommended_for_manual_review_count": recommended_count,
        "linkedin_min_match_score": settings.linkedin_min_match_score,
        "linkedin_recommended_match_score": settings.linkedin_recommended_match_score,
        "filtered_low_score_count": filtered_low_score_count,
        "match_bucket_counts": {
            "high": high_confidence_count,
            "medium": medium_confidence_count,
            "low": low_confidence_count,
            "missing": missing_match_count,
        },
        "review_report_path": str(review_path),
        "review_csv_path": str(review_csv_path),
        "leads": enriched,
    }

    out_path = Path("outputs/day2_contact_leads.json")
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    return out_path


if __name__ == "__main__":
    path = run()
    print(f"Wrote contact leads to {path}")
