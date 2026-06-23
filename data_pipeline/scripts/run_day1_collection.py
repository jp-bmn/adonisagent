"""Run Michael's Week 1 Day 1 collection and write normalized raw signals."""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from time import perf_counter
from urllib.parse import urlparse

import requests

from adonis_data.clients.newsapi import NewsApiClient
from adonis_data.clients.serper import SerperClient
from adonis_data.classify.provisional_classifier import classify_signal
from adonis_data.config import load_settings
from adonis_data.constants import HOSPITAL_QUERIES, RSS_FEEDS
from adonis_data.delivery.outbox import queue_payload
from adonis_data.delivery.signal_sender import post_signal_batch
from adonis_data.extract.raw_signal_extractor import (
    from_newsapi_item,
    from_rss_item,
    from_serper_pdf_item,
    from_serper_item,
)
from adonis_data.ingest.pdf_text import extract_pdf_text
from adonis_data.ingest.rss import fetch_rss_entries, filter_entries_by_hospital
from adonis_data.models import RawSignal


def _canonical_url(raw_url: str) -> str:
    parsed = urlparse(raw_url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    query = f"?{parsed.query}" if parsed.query else ""
    return f"{scheme}://{netloc}{path}{query}"


def _normalize_title(raw_title: str) -> str:
    cleaned = re.sub(r"\s+", " ", raw_title.strip().lower())
    cleaned = re.sub(r"[^a-z0-9\s]", "", cleaned)
    return cleaned


def _parse_published_at(value: str, now_utc: datetime) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None

    lowered = text.lower()
    relative_match = re.match(r"^(\d+)\s+(day|days|week|weeks|month|months|year|years)\s+ago$", lowered)
    if relative_match:
        quantity = int(relative_match.group(1))
        unit = relative_match.group(2)
        if "day" in unit:
            return now_utc - timedelta(days=quantity)
        if "week" in unit:
            return now_utc - timedelta(weeks=quantity)
        if "month" in unit:
            return now_utc - timedelta(days=30 * quantity)
        if "year" in unit:
            return now_utc - timedelta(days=365 * quantity)

    try:
        parsed = parsedate_to_datetime(text)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc)
    except (TypeError, ValueError):
        pass

    for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d", "%b %d, %Y", "%B %d, %Y"):
        try:
            parsed = datetime.strptime(text, fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue

    return None


def _load_previous_signals(path: Path) -> list[RawSignal]:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    signals: list[RawSignal] = []
    for item in payload.get("signals", []):
        try:
            signals.append(
                RawSignal(
                    hospital=str(item.get("hospital", "")),
                    title=str(item.get("title", "")),
                    source=str(item.get("source", "")),
                    url=str(item.get("url", "")),
                    published_at=str(item.get("published_at", "")),
                    matched_topics=list(item.get("matched_topics", [])),
                    excerpt=str(item.get("excerpt", "")),
                )
            )
        except (TypeError, ValueError):
            continue

    return signals


def _load_database_signals(supabase_url: str, supabase_key: str, hospitals: list[str], hospital_id_map: dict[str, str]) -> list[RawSignal]:
    if not supabase_url or not supabase_key:
        return []

    signals: list[RawSignal] = []
    headers = {
        "apikey": supabase_key,
        "Authorization": f"Bearer {supabase_key}"
    }

    for hospital_name in hospitals:
        hospital_id = hospital_id_map.get(hospital_name)
        if not hospital_id:
            continue
            
        # Fetch up to 1000 recent signals for each hospital
        url = f"{supabase_url}/rest/v1/signals?select=source_url,title,published_date&hospital_id=eq.{hospital_id}&limit=1000"
        try:
            res = requests.get(url, headers=headers, timeout=10)
            if not res.ok:
                continue
            
            for item in res.json():
                try:
                    signals.append(
                        RawSignal(
                            hospital=hospital_name,
                            title=str(item.get("title", "")),
                            source="database",
                            url=str(item.get("source_url", "")),
                            published_at=str(item.get("published_date", "")),
                            matched_topics=[],
                            excerpt="",
                        )
                    )
                except (TypeError, ValueError):
                    continue
        except Exception:
            continue

    return signals


def _is_duplicate(
    signal: RawSignal,
    seen_urls: set[str],
    seen_title_dates: dict[tuple[str, str], datetime],
    now_utc: datetime,
    dedup_days: int,
) -> tuple[bool, str | None]:
    if signal.url:
        canonical = _canonical_url(signal.url)
        if canonical in seen_urls:
            return True, "duplicate_source_url"

    signal_dt = _parse_published_at(signal.published_at, now_utc) or now_utc
    title_key = (signal.hospital, _normalize_title(signal.title))
    previous_dt = seen_title_dates.get(title_key)

    if previous_dt is not None and abs((signal_dt - previous_dt).days) <= dedup_days:
        return True, f"duplicate_title_hospital_{dedup_days}d"

    if signal.url:
        seen_urls.add(_canonical_url(signal.url))
    seen_title_dates[title_key] = signal_dt
    return False, None


def _build_handoff_markdown(
    hospitals: list[str],
    included_signals: list[RawSignal],
    skip_counter: Counter[str],
    settings_recency_days: int,
    settings_dedup_days: int,
    tier_counter: Counter[str],
    rules_hits: int,
    contact_lead_snapshot: dict[str, object] | None = None,
) -> str:
    per_hospital = Counter(signal.hospital for signal in included_signals)
    top_signals = sorted(
        included_signals,
        key=lambda s: len(s.matched_topics),
        reverse=True,
    )[:10]

    lines: list[str] = []
    lines.append("# Adonis Data Handoff Summary")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Scope")
    lines.append(f"- Hospitals: {', '.join(hospitals)}")
    lines.append(f"- Recency window (days): {settings_recency_days}")
    lines.append(f"- Dedup window (days): {settings_dedup_days}")
    lines.append("")
    lines.append("## Counts")
    lines.append(f"- Stored candidates: {len(included_signals)}")
    lines.append(f"- Rules-engine hits (provisional): {rules_hits}")
    if tier_counter:
        lines.append("- Tier distribution:")
        for tier, count in sorted(tier_counter.items()):
            lines.append(f"  - {tier}: {count}")
    if skip_counter:
        lines.append("- Skip reasons:")
        for reason, count in sorted(skip_counter.items()):
            lines.append(f"  - {reason}: {count}")
    else:
        lines.append("- Skip reasons: none")
    lines.append("")
    lines.append("## Per Hospital")
    for hospital in hospitals:
        lines.append(f"- {hospital}: {per_hospital.get(hospital, 0)}")
    lines.append("")
    lines.append("## Top Candidate Signals")
    for signal in top_signals:
        topics = ", ".join(signal.matched_topics) if signal.matched_topics else "none"
        lines.append(
            f"- [{signal.hospital}] {signal.title} | source={signal.source} | topics={topics} | url={signal.url}"
        )
    lines.append("")
    lines.append("## Next Step")
    lines.append("- Feed these candidates into rules-engine and classification in the next milestone.")
    lines.append("")

    lines.append("## Lead QA Snapshot")
    if not contact_lead_snapshot or not bool(contact_lead_snapshot.get("available", False)):
        lines.append("- Contact lead QA snapshot: unavailable (run scripts.run_contact_linkedin_discovery).")
    else:
        lines.append(
            f"- Lead count: {int(contact_lead_snapshot.get('lead_count', 0))}"
        )
        lines.append(
            f"- Recommended for manual review: {int(contact_lead_snapshot.get('recommended_for_manual_review_count', 0))}"
        )
        lines.append(
            f"- Rejected low-score matches: {int(contact_lead_snapshot.get('rejected_matches_count', 0))}"
        )
        lines.append(
            f"- Match bucket counts: {contact_lead_snapshot.get('match_bucket_counts', {})}"
        )

        review_report_path = str(contact_lead_snapshot.get("review_report_path", "")).strip()
        review_csv_path = str(contact_lead_snapshot.get("review_csv_path", "")).strip()
        if review_report_path:
            lines.append(f"- Review markdown: {review_report_path}")
        if review_csv_path:
            lines.append(f"- Review CSV: {review_csv_path}")

        top_rejected = contact_lead_snapshot.get("top_rejected_examples", [])
        if isinstance(top_rejected, list) and top_rejected:
            lines.append("")
            lines.append("### Top Rejected Examples")
            for item in top_rejected:
                if not isinstance(item, dict):
                    continue
                lines.append(
                    "- "
                    f"{item.get('full_name', '')} | "
                    f"hospital={item.get('hospital', '')} | "
                    f"score={item.get('linkedin_match_score', '')} | "
                    f"reason={item.get('rejection_reason', '')}"
                )

    lines.append("")
    return "\n".join(lines)


def _load_contact_lead_snapshot(path: Path) -> dict[str, object]:
    if not path.exists():
        return {"available": False}

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"available": False}

    rejected_matches = payload.get("rejected_matches", [])
    if not isinstance(rejected_matches, list):
        rejected_matches = []

    top_rejected = sorted(
        [row for row in rejected_matches if isinstance(row, dict)],
        key=lambda row: float(row.get("linkedin_match_score", 0.0) or 0.0),
    )[:3]

    return {
        "available": True,
        "lead_count": int(payload.get("lead_count", 0) or 0),
        "recommended_for_manual_review_count": int(
            payload.get("recommended_for_manual_review_count", 0) or 0
        ),
        "rejected_matches_count": int(payload.get("rejected_matches_count", 0) or 0),
        "match_bucket_counts": payload.get("match_bucket_counts", {}),
        "review_report_path": str(payload.get("review_report_path", "")),
        "review_csv_path": str(payload.get("review_csv_path", "")),
        "top_rejected_examples": top_rejected,
    }


def _write_signal_csv(path: Path, signals: list[RawSignal]) -> None:
    header = "hospital,title,source,url,published_at,matched_topics"
    rows = [header]
    for signal in signals:
        fields = [
            signal.hospital,
            signal.title,
            signal.source,
            signal.url,
            signal.published_at,
            "|".join(signal.matched_topics),
        ]
        escaped = ['"' + value.replace('"', '""') + '"' for value in fields]
        rows.append(",".join(escaped))
    path.write_text("\n".join(rows) + "\n", encoding="utf-8")


def _build_signal_batch_payload(
    classified_signals: list[dict[str, object]],
    now_utc: datetime,
    recency_days: int,
    dedup_days: int,
    hospital_id_map: dict[str, str] | None,
) -> dict[str, object]:
    resolved_hospital_ids = hospital_id_map or {}

    def _normalize_published_date(value: object) -> str:
        parsed = _parse_published_at(str(value or ""), now_utc)
        if parsed is None:
            return now_utc.date().isoformat()
        return parsed.date().isoformat()

    def _truncate_title_words(title: str, max_words: int = 10) -> str:
        words = [word for word in title.split() if word]
        if len(words) <= max_words:
            return title
        return " ".join(words[:max_words])

    signal_rows: list[dict[str, object]] = []
    for signal in classified_signals:
        hospital_name = str(signal.get("hospital", "")).strip()
        source_name = str(signal.get("source", "")).strip()
        source_url = str(signal.get("url", "")).strip()
        summary = str(signal.get("one_sentence_summary", "")).strip() or str(signal.get("excerpt", "")).strip()
        title = str(signal.get("title", "")).strip()
        signal_type = str(signal.get("signal_type", "financial_event")).strip()
        
        # Check if title is empty or generic
        normalized_title = title.lower().replace("_", " ").replace("-", " ").strip()
        is_generic = (
            not title or
            normalized_title in {t.replace("_", " ") for t in ["leadership_change", "rcm_hiring_spike", "epic_go_live", "post_golive_friction", "ma_acquisition", "vendor_change", "vendor_dispute", "restructuring", "new_hospital_launch", "financial_event", "ai_adoption_outside_rcm", "automation_proof", "named_automation_owner", "thought_leadership", "filtered_out"]} or
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

        published_raw = str(signal.get("published_at", "")).strip()
        hospital_id = resolved_hospital_ids.get(hospital_name, "")

        signal_rows.append(
            {
                "hospital_id": hospital_id,
                "hospital_name": hospital_name,
                "signal_type": signal_type,
                "tier": str(signal.get("tier", "worth_knowing")).strip(),
                "confidence_score": float(signal.get("confidence_score", 0.0) or 0.0),
                "title": _truncate_title_words(title),
                "summary": summary,
                "source_url": source_url,
                "source_name": source_name,
                "published_date": _normalize_published_date(published_raw),
                # Keep legacy keys to avoid breaking Joel's current batch parser.
                "published_at_raw": published_raw,
                "excerpt": str(signal.get("excerpt", "")).strip(),
                "matched_topics": list(signal.get("matched_topics", [])),
                "extraction_stage": "raw_candidate",
                "dedup_applied": True,
                "recency_applied": True,
            }
        )


    return {
        "run_context": {
            "run_at_utc": now_utc.isoformat(),
            "source_pipeline_version": "day2",
            "recency_days": recency_days,
            "dedup_days": dedup_days,
            "hospitals": list(HOSPITAL_QUERIES.keys()),
        },
        "signals": signal_rows,
    }


def _signal_key(item: dict[str, object]) -> str:
    hospital = str(item.get("hospital", "")).strip()
    url = str(item.get("url", "")).strip()
    title = str(item.get("title", "")).strip()
    if url:
        return _canonical_url(url)
    return f"{hospital}|{_normalize_title(title)}"


def _load_previous_classified(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    rows = payload.get("signals", [])
    if not isinstance(rows, list):
        return []
    return [row for row in rows if isinstance(row, dict)]


def _build_daily_diff_markdown(diff: dict[str, object]) -> str:
    lines: list[str] = []
    lines.append("# Adonis Daily Diff Report")
    lines.append("")
    lines.append(f"Generated: {diff.get('generated_at_utc', '')}")
    lines.append("")
    lines.append("## Summary")
    lines.append(f"- New signals: {diff.get('new_count', 0)}")
    lines.append(f"- Removed signals: {diff.get('removed_count', 0)}")
    lines.append(f"- Unchanged signals: {diff.get('unchanged_count', 0)}")
    lines.append(f"- Tier changes: {diff.get('tier_changed_count', 0)}")
    lines.append("")
    lines.append("## New By Hospital")
    for hospital, count in sorted((diff.get("new_by_hospital", {}) or {}).items()):
        lines.append(f"- {hospital}: {count}")
    lines.append("")
    lines.append("## Removed By Hospital")
    for hospital, count in sorted((diff.get("removed_by_hospital", {}) or {}).items()):
        lines.append(f"- {hospital}: {count}")
    lines.append("")
    lines.append("## New Signal Titles")
    for title in (diff.get("new_titles", []) or [])[:20]:
        lines.append(f"- {title}")
    lines.append("")
    lines.append("## Removed Signal Titles")
    for title in (diff.get("removed_titles", []) or [])[:20]:
        lines.append(f"- {title}")
    lines.append("")
    return "\n".join(lines)


def _build_executive_brief_markdown(
    now_utc: datetime,
    classified_signals: list[dict[str, object]],
    daily_diff: dict[str, object],
    min_confidence: float,
    max_items: int,
    include_urgent_override: bool,
) -> str:
    selection = _select_brief_signals(
        classified_signals=classified_signals,
        min_confidence=min_confidence,
        max_items=max_items,
        include_urgent_override=include_urgent_override,
    )
    top = selection["included"]

    lines: list[str] = []
    lines.append("# Adonis Executive Brief")
    lines.append("")
    lines.append(f"Generated: {now_utc.isoformat()}")
    lines.append("")
    lines.append("## Snapshot")
    lines.append(f"- New signals since prior run: {daily_diff.get('new_count', 0)}")
    lines.append(f"- Removed signals since prior run: {daily_diff.get('removed_count', 0)}")
    lines.append(f"- Unchanged signals: {daily_diff.get('unchanged_count', 0)}")
    lines.append(f"- Brief confidence threshold: {min_confidence:.2f}")
    lines.append(f"- Include urgent override: {str(include_urgent_override).lower()}")
    lines.append("")
    lines.append(f"## Top {max(1, max_items)} Account Updates")
    if not top:
        lines.append("- No qualifying updates in this run at current confidence threshold.")
    else:
        for idx, signal in enumerate(top, start=1):
            hospital = str(signal.get("hospital", "Unknown hospital"))
            title = str(signal.get("title", "Untitled signal"))
            tier = str(signal.get("tier", "worth_knowing"))
            confidence = float(signal.get("confidence_score", 0.0) or 0.0)
            source = str(signal.get("source", "Unknown source"))
            summary = str(signal.get("one_sentence_summary", "")).strip() or str(signal.get("excerpt", "")).strip()
            lines.append(
                f"{idx}. [{hospital}] ({tier}, conf={confidence:.2f}) {title}"
            )
            lines.append(f"   - Summary: {summary}")
            lines.append(f"   - Source: {source}")

    excluded_for_confidence = len(selection["excluded_below_confidence"])
    if excluded_for_confidence > 0:
        lines.append("")
        lines.append(f"- Excluded for confidence below threshold: {excluded_for_confidence}")

    lines.append("")
    lines.append("## Suggested Action")
    lines.append("- Review urgent items first, then include worth-knowing items in weekly AE digest drafting.")
    lines.append("")
    return "\n".join(lines)


def _select_brief_signals(
    classified_signals: list[dict[str, object]],
    min_confidence: float,
    max_items: int,
    include_urgent_override: bool,
) -> dict[str, list[dict[str, object]]]:
    tier_rank = {"urgent": 0, "worth_knowing": 1, "filtered_out": 2}
    sorted_signals = sorted(
        classified_signals,
        key=lambda s: (
            tier_rank.get(str(s.get("tier", "worth_knowing")), 9),
            -float(s.get("confidence_score", 0.0) or 0.0),
        ),
    )

    eligible: list[dict[str, object]] = []
    excluded_below_confidence: list[dict[str, object]] = []
    urgent_override_included: list[dict[str, object]] = []

    for signal in sorted_signals:
        confidence = float(signal.get("confidence_score", 0.0) or 0.0)
        tier = str(signal.get("tier", ""))
        if confidence >= min_confidence:
            eligible.append(signal)
            continue

        if include_urgent_override and tier == "urgent":
            eligible.append(signal)
            urgent_override_included.append(signal)
            continue

        excluded_below_confidence.append(signal)

    included = eligible[: max(1, max_items)]
    included_keys = {_signal_key(item) for item in included}

    excluded_max_items = [item for item in eligible if _signal_key(item) not in included_keys]

    return {
        "included": included,
        "excluded_below_confidence": excluded_below_confidence,
        "excluded_max_items": excluded_max_items,
        "urgent_override_included": urgent_override_included,
    }


def _collect_api_signals(
    hospital: str,
    query: str,
    serper: SerperClient,
    newsapi: NewsApiClient,
    pdf_ingestion_enabled: bool,
    pdf_max_words: int,
    request_timeout_seconds: int,
) -> list[RawSignal]:
    signals: list[RawSignal] = []

    for item in serper.search_news(query=query, num_results=10):
        link = str(item.get("link", "")).strip().lower()
        is_pdf = ".pdf" in link

        if is_pdf and pdf_ingestion_enabled:
            try:
                pdf_text = extract_pdf_text(
                    url=str(item.get("link", "")).strip(),
                    timeout_seconds=request_timeout_seconds,
                    max_words=pdf_max_words,
                )
                source_name = "SEC Filing"
                if "irs" in link or "form-990" in link or "990" in link:
                    source_name = "IRS Form 990"
                signals.append(
                    from_serper_pdf_item(
                        hospital=hospital,
                        item=item,
                        pdf_text=pdf_text,
                        source_name=source_name,
                    )
                )
                continue
            except Exception:
                # Fall back to snippet extraction if PDF parse fails.
                pass

        signals.append(from_serper_item(hospital=hospital, item=item))

    for item in newsapi.search_everything(query=query, page_size=10):
        signals.append(from_newsapi_item(hospital=hospital, item=item))

    return signals


def _collect_rss_signals(hospital: str) -> list[RawSignal]:
    signals: list[RawSignal] = []

    for source_name, url in RSS_FEEDS.items():
        entries = fetch_rss_entries(feed_url=url)
        matches = filter_entries_by_hospital(entries=entries, hospital_name=hospital)
        for item in matches:
            signals.append(from_rss_item(hospital=hospital, source_name=source_name, item=item))

    return signals


def _reason_for_skip(signal: RawSignal) -> str | None:
    if not signal.title:
        return "missing_title"
    if not signal.url:
        return "missing_url"
    if not signal.excerpt:
        return "missing_excerpt"
    if not signal.matched_topics:
        return "no_topic_match"
    return None


def _word_count(text: str) -> int:
    return len(re.findall(r"[a-zA-Z0-9]+", text or ""))


def _low_information_reason(signal: RawSignal) -> str | None:
    title_words = _word_count(signal.title)
    excerpt_words = _word_count(signal.excerpt)

    if title_words <= 4 and excerpt_words <= 12:
        return "low_information_signal"

    if excerpt_words < 8 and len(signal.matched_topics) <= 1:
        return "low_information_signal"

    return None


def _noise_reason(signal: RawSignal, noise_guard_enabled: bool, noise_keywords: tuple[str, ...]) -> str | None:
    if not noise_guard_enabled:
        return None

    title = signal.title.lower()
    excerpt = signal.excerpt.lower()
    source = signal.source.lower()
    blob = f"{title} {excerpt}"

    for keyword in noise_keywords:
        if keyword and keyword in blob:
            return "noise_generic_headline"
            
    broad_markers = ["stock roundup", "industry trends", "market report", "stocks to watch", "daily briefing"]
    if any(marker in title for marker in broad_markers):
        return "noise_broad_industry_report"

    # Common broad update pages that often drown account-specific signals.
    if source in {"modern healthcare", "fierce healthcare"} and any(
        marker in title for marker in ["tracker", "live updates", "deals tracker", "layoff tracker"]
    ):
        return "noise_source_tracker_page"

    return None


def _is_broad_update_page(signal: RawSignal) -> bool:
    title = signal.title.lower()
    source = signal.source.lower()
    markers = [
        "tracker",
        "live updates",
        "dealmakers",
        "layoff",
        "roundup",
        "stock roundup",
        "market report",
        "industry trends",
        "daily briefing"
    ]
    return source in {"modern healthcare", "fierce healthcare"} and any(marker in title for marker in markers)


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


def _mentions_target_hospital(signal: RawSignal) -> bool:
    blob = f"{signal.title} {signal.excerpt}".lower()
    return any(alias in blob for alias in _hospital_aliases(signal.hospital))


def _is_allowlisted(
    signal: RawSignal,
    allowlist_enabled: bool,
    allowlist_domains: tuple[str, ...],
    allowlist_sources: tuple[str, ...],
) -> bool:
    if not allowlist_enabled:
        return False

    source = signal.source.lower().strip()
    if source and source in allowlist_sources:
        return True

    if signal.url:
        netloc = urlparse(signal.url).netloc.lower().strip()
        if any(domain and domain in netloc for domain in allowlist_domains):
            return True

    return False


def run(quality_mode_override: str | None = None) -> Path:
    started = perf_counter()
    settings = load_settings()
    quality_mode = (quality_mode_override or settings.quality_mode).strip().lower()
    if quality_mode not in {"open", "balanced", "strict"}:
        quality_mode = settings.quality_mode
    serper = SerperClient(api_key=settings.serper_api_key)
    newsapi = NewsApiClient(api_key=settings.newsapi_api_key)
    now_utc = datetime.now(timezone.utc)

    all_signals: list[RawSignal] = []
    per_hospital_queries: dict[str, str] = {}

    for hospital, query in HOSPITAL_QUERIES.items():
        per_hospital_queries[hospital] = query
        all_signals.extend(
            _collect_api_signals(
                hospital,
                query,
                serper,
                newsapi,
                pdf_ingestion_enabled=settings.pdf_ingestion_enabled,
                pdf_max_words=settings.pdf_max_words,
                request_timeout_seconds=settings.request_timeout_seconds,
            )
        )
        all_signals.extend(_collect_rss_signals(hospital))

    included_signals: list[RawSignal] = []
    skipped_signals: list[dict[str, str]] = []
    skip_counter: Counter[str] = Counter()

    for signal in all_signals:
        skip_reason = _reason_for_skip(signal)
        if skip_reason is None:
            included_signals.append(signal)
            continue

        skip_counter[skip_reason] += 1
        skipped_signals.append(
            {
                "hospital": signal.hospital,
                "title": signal.title,
                "url": signal.url,
                "reason": skip_reason,
            }
        )

    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "day1_raw_signals.json"
    quality_log_path = output_dir / "day2_signal_quality_log.json"
    handoff_md_path = output_dir / "day2_handoff_summary.md"
    handoff_csv_path = output_dir / "day2_signal_summary.csv"
    batch_payload_path = output_dir / "day2_signal_ingest_example_payload.json"
    delivery_status_path = output_dir / "day2_delivery_status.json"
    classified_path = output_dir / "day2_classified_candidates.json"
    run_log_path = output_dir / "day2_run_log.json"
    quality_upgrade_metrics_path = output_dir / "day2_quality_upgrade_metrics.json"
    daily_diff_json_path = output_dir / "day2_daily_diff.json"
    daily_diff_md_path = output_dir / "day2_daily_diff.md"
    executive_brief_path = output_dir / "day2_executive_brief.md"
    executive_brief_audit_path = output_dir / "day2_executive_brief_audit.json"
    contact_leads_path = output_dir / "day2_contact_leads.json"
    previous_run_log: dict[str, object] = {}
    if run_log_path.exists():
        try:
            loaded = json.loads(run_log_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                previous_run_log = loaded
        except (OSError, json.JSONDecodeError):
            previous_run_log = {}

    previous_classified = _load_previous_classified(classified_path)

    # 1. Load from Database
    db_signals = _load_database_signals(
        supabase_url=settings.supabase_url,
        supabase_key=settings.supabase_service_key,
        hospitals=list(HOSPITAL_QUERIES.keys()),
        hospital_id_map=settings.hospital_id_map or {},
    )
    
    # 2. Fallback to Local JSON
    local_signals = _load_previous_signals(output_path)
    
    previous_signals = db_signals + local_signals
    seen_urls: set[str] = set()
    seen_title_dates: dict[tuple[str, str], datetime] = {}

    for previous in previous_signals:
        prev_dt = _parse_published_at(previous.published_at, now_utc) or now_utc
        if previous.url:
            seen_urls.add(_canonical_url(previous.url))
        seen_title_dates[(previous.hospital, _normalize_title(previous.title))] = prev_dt

    final_signals: list[RawSignal] = []
    quality_upgrade_before_count = len(included_signals)
    low_information_skipped = 0

    recency_cutoff = now_utc - timedelta(days=settings.recency_days)
    for signal in included_signals:
        low_information_reason = _low_information_reason(signal)
        if low_information_reason is not None:
            low_information_skipped += 1
            skip_counter[low_information_reason] += 1
            skipped_signals.append(
                {
                    "hospital": signal.hospital,
                    "title": signal.title,
                    "url": signal.url,
                    "reason": low_information_reason,
                }
            )
            continue

        allowlisted = _is_allowlisted(
            signal=signal,
            allowlist_enabled=settings.allowlist_enabled,
            allowlist_domains=settings.allowlist_domains,
            allowlist_sources=settings.allowlist_sources,
        )

        noise_reason = _noise_reason(
            signal=signal,
            noise_guard_enabled=settings.noise_guard_enabled,
            noise_keywords=settings.noise_keywords,
        )
        if noise_reason is not None and not allowlisted:
            skip_counter[noise_reason] += 1
            skipped_signals.append(
                {
                    "hospital": signal.hospital,
                    "title": signal.title,
                    "url": signal.url,
                    "reason": noise_reason,
                }
            )
            continue

        # The agent should only attribute a signal to a hospital if the article directly references that specific health system.
        # Broad tracker pages must always mention the target hospital, even if from an allowlisted source.
        must_mention = not allowlisted or _is_broad_update_page(signal)
        if must_mention and not _mentions_target_hospital(signal):
            skip_counter["noise_not_hospital_specific"] += 1
            skipped_signals.append(
                {
                    "hospital": signal.hospital,
                    "title": signal.title,
                    "url": signal.url,
                    "reason": "noise_not_hospital_specific",
                }
            )
            continue

        parsed_dt = _parse_published_at(signal.published_at, now_utc)
        if parsed_dt is not None and parsed_dt < recency_cutoff:
            skip_counter["outside_recency_window"] += 1
            skipped_signals.append(
                {
                    "hospital": signal.hospital,
                    "title": signal.title,
                    "url": signal.url,
                    "reason": "outside_recency_window",
                }
            )
            continue

        is_dupe, dupe_reason = _is_duplicate(
            signal=signal,
            seen_urls=seen_urls,
            seen_title_dates=seen_title_dates,
            now_utc=now_utc,
            dedup_days=settings.dedup_days,
        )
        if is_dupe:
            skip_counter[dupe_reason or "duplicate"] += 1
            skipped_signals.append(
                {
                    "hospital": signal.hospital,
                    "title": signal.title,
                    "url": signal.url,
                    "reason": dupe_reason or "duplicate",
                }
            )
            continue

        final_signals.append(signal)

    payload = {
        "signal_count": len(final_signals),
        "signals": [signal.to_dict() for signal in final_signals],
    }

    classified_signals: list[dict[str, object]] = []
    tier_counter: Counter[str] = Counter()
    rules_engine_hits = 0
    for signal in final_signals:
        classification = classify_signal(signal, quality_mode=quality_mode)
        if classification.rules_engine_hit:
            rules_engine_hits += 1
        tier_counter[classification.tier] += 1
        classified_signals.append(
            {
                **signal.to_dict(),
                "signal_type": classification.signal_type,
                "tier": classification.tier,
                "confidence_score": classification.confidence_score,
                "one_sentence_summary": classification.one_sentence_summary,
                "why_relevant_to_adonis": classification.why_relevant_to_adonis,
                "rules_engine_hit": classification.rules_engine_hit,
                "rules_engine_reason": classification.rules_engine_reason,
            }
        )

    quality_payload = {
        "hospitals": list(HOSPITAL_QUERIES.keys()),
        "queries": per_hospital_queries,
        "articles_found": len(all_signals),
        "classified_candidates": len(all_signals),
        "stored_candidates": len(final_signals),
        "skipped_count": len(skipped_signals),
        "skip_reasons": dict(skip_counter),
        "skipped_examples": skipped_signals[:20],
        "recency_days": settings.recency_days,
        "dedup_days": settings.dedup_days,
        "noise_guard_enabled": settings.noise_guard_enabled,
        "noise_keywords": list(settings.noise_keywords),
        "allowlist_enabled": settings.allowlist_enabled,
        "allowlist_domains": list(settings.allowlist_domains),
        "allowlist_sources": list(settings.allowlist_sources),
        "rules_engine_hits": rules_engine_hits,
        "quality_mode_used": quality_mode,
        "tier_counts": dict(tier_counter),
        "quality_upgrade": {
            "before_upgrade_candidate_count": quality_upgrade_before_count,
            "after_upgrade_candidate_count": quality_upgrade_before_count - low_information_skipped,
            "after_all_filters_candidate_count": len(final_signals),
            "low_information_skipped": low_information_skipped,
        },
    }

    previous_signals_new = int(previous_run_log.get("signals_new", 0) or 0)
    previous_signals_skipped = int(previous_run_log.get("signals_skipped", 0) or 0)
    previous_skip_reasons = previous_run_log.get("skip_reasons", {})
    if not isinstance(previous_skip_reasons, dict):
        previous_skip_reasons = {}
    previous_low_information_skipped = int(previous_skip_reasons.get("low_information_signal", 0) or 0)

    quality_upgrade_metrics_payload = {
        "generated_at_utc": now_utc.isoformat(),
        "before_upgrade_candidate_count": quality_upgrade_before_count,
        "after_upgrade_candidate_count": quality_upgrade_before_count - low_information_skipped,
        "after_all_filters_candidate_count": len(final_signals),
        "low_information_skipped": low_information_skipped,
        "before_after_vs_previous_run": {
            "previous_signals_new": previous_signals_new,
            "current_signals_new": len(final_signals),
            "delta_signals_new": len(final_signals) - previous_signals_new,
            "previous_signals_skipped": previous_signals_skipped,
            "current_signals_skipped": len(skipped_signals),
            "delta_signals_skipped": len(skipped_signals) - previous_signals_skipped,
            "previous_low_information_skipped": previous_low_information_skipped,
            "current_low_information_skipped": low_information_skipped,
            "delta_low_information_skipped": low_information_skipped - previous_low_information_skipped,
        },
    }

    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    quality_log_path.write_text(json.dumps(quality_payload, indent=2), encoding="utf-8")
    quality_upgrade_metrics_path.write_text(
        json.dumps(quality_upgrade_metrics_payload, indent=2),
        encoding="utf-8",
    )
    classified_path.write_text(
        json.dumps(
            {
                "classified_count": len(classified_signals),
                "signals": classified_signals,
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    prev_map = {_signal_key(item): item for item in previous_classified}
    curr_map = {_signal_key(item): item for item in classified_signals}

    prev_keys = set(prev_map)
    curr_keys = set(curr_map)
    new_keys = curr_keys - prev_keys
    removed_keys = prev_keys - curr_keys
    unchanged_keys = curr_keys & prev_keys

    new_by_hospital: Counter[str] = Counter()
    removed_by_hospital: Counter[str] = Counter()
    tier_changed_count = 0

    for key in new_keys:
        new_by_hospital[str(curr_map[key].get("hospital", "Unknown"))] += 1

    for key in removed_keys:
        removed_by_hospital[str(prev_map[key].get("hospital", "Unknown"))] += 1

    for key in unchanged_keys:
        prev_tier = str(prev_map[key].get("tier", ""))
        curr_tier = str(curr_map[key].get("tier", ""))
        if prev_tier != curr_tier:
            tier_changed_count += 1

    daily_diff_payload: dict[str, object] = {
        "generated_at_utc": now_utc.isoformat(),
        "new_count": len(new_keys),
        "removed_count": len(removed_keys),
        "unchanged_count": len(unchanged_keys),
        "tier_changed_count": tier_changed_count,
        "new_by_hospital": dict(new_by_hospital),
        "removed_by_hospital": dict(removed_by_hospital),
        "new_titles": [str(curr_map[key].get("title", "")) for key in sorted(new_keys)],
        "removed_titles": [str(prev_map[key].get("title", "")) for key in sorted(removed_keys)],
    }

    daily_diff_json_path.write_text(json.dumps(daily_diff_payload, indent=2), encoding="utf-8")
    daily_diff_md_path.write_text(_build_daily_diff_markdown(daily_diff_payload), encoding="utf-8")
    brief_selection = _select_brief_signals(
        classified_signals=classified_signals,
        min_confidence=settings.executive_brief_min_confidence,
        max_items=settings.executive_brief_max_items,
        include_urgent_override=settings.executive_brief_include_urgent_override,
    )

    executive_brief_path.write_text(
        _build_executive_brief_markdown(
            now_utc=now_utc,
            classified_signals=classified_signals,
            daily_diff=daily_diff_payload,
            min_confidence=settings.executive_brief_min_confidence,
            max_items=settings.executive_brief_max_items,
            include_urgent_override=settings.executive_brief_include_urgent_override,
        ),
        encoding="utf-8",
    )
    executive_brief_audit_path.write_text(
        json.dumps(
            {
                "generated_at_utc": now_utc.isoformat(),
                "min_confidence": settings.executive_brief_min_confidence,
                "max_items": settings.executive_brief_max_items,
                "include_urgent_override": settings.executive_brief_include_urgent_override,
                "included_count": len(brief_selection["included"]),
                "excluded_below_confidence_count": len(brief_selection["excluded_below_confidence"]),
                "excluded_max_items_count": len(brief_selection["excluded_max_items"]),
                "urgent_override_included_count": len(brief_selection["urgent_override_included"]),
                "included": [
                    {
                        "hospital": str(item.get("hospital", "")),
                        "title": str(item.get("title", "")),
                        "tier": str(item.get("tier", "")),
                        "confidence_score": float(item.get("confidence_score", 0.0) or 0.0),
                    }
                    for item in brief_selection["included"]
                ],
                "excluded_below_confidence": [
                    {
                        "hospital": str(item.get("hospital", "")),
                        "title": str(item.get("title", "")),
                        "tier": str(item.get("tier", "")),
                        "confidence_score": float(item.get("confidence_score", 0.0) or 0.0),
                    }
                    for item in brief_selection["excluded_below_confidence"]
                ],
                "excluded_max_items": [
                    {
                        "hospital": str(item.get("hospital", "")),
                        "title": str(item.get("title", "")),
                        "tier": str(item.get("tier", "")),
                        "confidence_score": float(item.get("confidence_score", 0.0) or 0.0),
                    }
                    for item in brief_selection["excluded_max_items"]
                ],
                "urgent_override_included": [
                    {
                        "hospital": str(item.get("hospital", "")),
                        "title": str(item.get("title", "")),
                        "tier": str(item.get("tier", "")),
                        "confidence_score": float(item.get("confidence_score", 0.0) or 0.0),
                    }
                    for item in brief_selection["urgent_override_included"]
                ],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    handoff_md_path.write_text(
        _build_handoff_markdown(
            hospitals=list(HOSPITAL_QUERIES.keys()),
            included_signals=final_signals,
            skip_counter=skip_counter,
            settings_recency_days=settings.recency_days,
            settings_dedup_days=settings.dedup_days,
            tier_counter=tier_counter,
            rules_hits=rules_engine_hits,
            contact_lead_snapshot=_load_contact_lead_snapshot(contact_leads_path),
        ),
        encoding="utf-8",
    )
    _write_signal_csv(handoff_csv_path, final_signals)

    batch_payload = _build_signal_batch_payload(
        classified_signals=classified_signals,
        now_utc=now_utc,
        recency_days=settings.recency_days,
        dedup_days=settings.dedup_days,
        hospital_id_map=settings.hospital_id_map,
    )
    batch_payload_path.write_text(json.dumps(batch_payload, indent=2), encoding="utf-8")

    delivery_status: dict[str, object] = {
        "enabled": settings.post_signals_enabled,
        "endpoint_configured": bool(settings.signals_endpoint_url),
        "signals_in_payload": len(final_signals),
        "delivered": False,
        "outbox_enabled": settings.outbox_enabled,
    }

    if settings.outbox_enabled:
        queued_path = queue_payload(settings.outbox_dir, batch_payload)
        delivery_status["outbox_file"] = str(queued_path)

    if settings.post_signals_enabled and settings.signals_endpoint_url:
        try:
            send_result = post_signal_batch(
                endpoint_url=settings.signals_endpoint_url,
                payload=batch_payload,
                timeout_seconds=settings.request_timeout_seconds,
                bearer_token=settings.signals_endpoint_token,
            )
            delivery_status.update(
                {
                    "delivered": bool(send_result.get("ok", False)),
                    "status_code": send_result.get("status_code"),
                    "response": send_result.get("response_json", send_result.get("response_text", "")),
                }
            )
        except Exception as exc:
            delivery_status.update(
                {
                    "error": str(exc),
                }
            )
    elif settings.post_signals_enabled and not settings.signals_endpoint_url:
        delivery_status.update({"error": "POST_SIGNALS_ENABLED is true but SIGNALS_ENDPOINT_URL is empty."})
    else:
        delivery_status.update({"note": "Delivery disabled. Set POST_SIGNALS_ENABLED=true to send payload."})

    delivery_status_path.write_text(json.dumps(delivery_status, indent=2), encoding="utf-8")

    duration_ms = int((perf_counter() - started) * 1000)
    run_log_path.write_text(
        json.dumps(
            {
                "run_at_utc": now_utc.isoformat(),
                "hospitals_checked": len(HOSPITAL_QUERIES),
                "articles_found": len(all_signals),
                "classified_candidates": len(classified_signals),
                "signals_new": len(final_signals),
                "signals_skipped": len(skipped_signals),
                "rules_engine_hits": rules_engine_hits,
                "quality_mode_used": quality_mode,
                "skip_reasons": dict(skip_counter),
                "quality_upgrade": quality_upgrade_metrics_payload,
                "daily_diff": {
                    "new_count": len(new_keys),
                    "removed_count": len(removed_keys),
                    "unchanged_count": len(unchanged_keys),
                    "tier_changed_count": tier_changed_count,
                },
                "executive_brief": {
                    "min_confidence": settings.executive_brief_min_confidence,
                    "max_items": settings.executive_brief_max_items,
                    "include_urgent_override": settings.executive_brief_include_urgent_override,
                    "included_count": len(brief_selection["included"]),
                    "excluded_below_confidence_count": len(brief_selection["excluded_below_confidence"]),
                    "excluded_max_items_count": len(brief_selection["excluded_max_items"]),
                    "urgent_override_included_count": len(brief_selection["urgent_override_included"]),
                },
                "pdf_ingestion": {
                    "enabled": settings.pdf_ingestion_enabled,
                    "pdf_max_words": settings.pdf_max_words,
                },
                "duration_ms": duration_ms,
                "delivery": delivery_status,
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    if settings.post_signals_enabled and settings.signals_endpoint_url:
        post_result = post_signal_batch(
            endpoint_url=settings.signals_endpoint_url,
            payload=batch_payload,
            timeout_seconds=settings.request_timeout_seconds,
            bearer_token=settings.signals_endpoint_token,
        )
        delivery_status_path.write_text(json.dumps(post_result, indent=2), encoding="utf-8")

    return output_path


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run day 1 raw signal collection.")
    parser.add_argument("--quality-mode", choices=["open", "balanced", "strict"], default=None, help="Override quality mode for this run")
    args = parser.parse_args()
    
    path = run(quality_mode_override=args.quality_mode)
    print(f"Wrote raw signals to {path}")
