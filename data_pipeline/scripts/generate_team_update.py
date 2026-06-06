"""Generate a plain-English teammate update from latest pipeline artifacts."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _fmt_int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _fmt_float(value: Any) -> float:
    try:
        return float(value or 0.0)
    except (TypeError, ValueError):
        return 0.0


def run() -> Path:
    load_dotenv()

    outputs_dir = Path("outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)

    run_log = _read_json(outputs_dir / "day2_run_log.json")
    quality_log = _read_json(outputs_dir / "day2_signal_quality_log.json")
    contact_log = _read_json(outputs_dir / "day2_contact_leads.json")
    delivery_status = _read_json(outputs_dir / "day2_delivery_status.json")

    now_utc = datetime.now(timezone.utc).isoformat()

    hospitals_checked = _fmt_int(run_log.get("hospitals_checked", 0))
    articles_found = _fmt_int(run_log.get("articles_found", 0))
    signals_new = _fmt_int(run_log.get("signals_new", 0))
    signals_skipped = _fmt_int(run_log.get("signals_skipped", 0))
    rules_engine_hits = _fmt_int(run_log.get("rules_engine_hits", 0))
    duration_ms = _fmt_int(run_log.get("duration_ms", 0))

    skip_reasons = run_log.get("skip_reasons", {})
    if not isinstance(skip_reasons, dict):
        skip_reasons = {}

    top_skip = sorted(
        ((str(k), _fmt_int(v)) for k, v in skip_reasons.items()),
        key=lambda row: row[1],
        reverse=True,
    )[:4]

    lead_count = _fmt_int(contact_log.get("lead_count", 0))
    recommended = _fmt_int(contact_log.get("recommended_for_manual_review_count", 0))
    rejected = _fmt_int(contact_log.get("rejected_matches_count", 0))

    delivery_enabled = bool((run_log.get("delivery") or {}).get("enabled", False))
    delivered = bool((run_log.get("delivery") or {}).get("delivered", False))

    quality_mode = str(run_log.get("quality_mode_used", "balanced") or "balanced")

    # This is the blocker that currently prevents live posting completion.
    hospital_id_map_raw = os.getenv("HOSPITAL_ID_MAP", "").strip()
    waiting_on_ids = hospital_id_map_raw == "" and not delivered

    lines: list[str] = []
    lines.append("# Teammate Update (Plain English)")
    lines.append("")
    lines.append(f"Generated: {now_utc}")
    lines.append("")
    lines.append("## What We Completed")
    lines.append(
        f"- The pipeline run finished successfully across {hospitals_checked} hospitals in {duration_ms} ms."
    )
    lines.append(
        f"- It found {articles_found} source articles and kept {signals_new} candidate signals after filtering."
    )
    lines.append(
        f"- The rules engine auto-prioritized {rules_engine_hits} signals before fallback classification."
    )
    lines.append(f"- Summary quality mode used this run: {quality_mode}.")
    lines.append("")
    lines.append("## Quality and Filtering")
    lines.append(f"- {signals_skipped} signals were skipped for quality/duplication/recency reasons.")
    if top_skip:
        for reason, count in top_skip:
            lines.append(f"- Top skip reason: {reason} = {count}")
    lines.append("")
    lines.append("## Contact Lead QA")
    lines.append(f"- Total leads identified: {lead_count}")
    lines.append(f"- Recommended for manual review: {recommended}")
    lines.append(f"- Rejected low-confidence matches: {rejected}")
    lines.append("")
    lines.append("## Delivery Status")
    lines.append(f"- Delivery enabled in this run: {str(delivery_enabled)}")
    lines.append(f"- Delivery completed in this run: {str(delivered)}")
    if not delivery_enabled:
        lines.append("- Note: this run appears to be artifact-only mode (no live posting).")
    lines.append("")
    lines.append("## Blockers")
    if waiting_on_ids:
        lines.append("- Waiting on valid AE UUID/project access to populate HOSPITAL_ID_MAP and unblock live posting.")
    else:
        lines.append("- No config blocker detected for HOSPITAL_ID_MAP.")
    lines.append("")
    lines.append("## Useful Artifacts")
    lines.append("- Status snapshot: outputs/day2_status_snapshot.md")
    lines.append("- Handoff summary: outputs/day2_handoff_summary.md")
    lines.append("- Run log: outputs/day2_run_log.json")
    lines.append("- Delivery status: outputs/day2_delivery_status.json")
    lines.append("- Contact lead review: outputs/day2_contact_leads_review.md")
    lines.append("")

    output_path = outputs_dir / "day2_team_update_plain_english.md"
    output_path.write_text("\n".join(lines), encoding="utf-8")
    return output_path


if __name__ == "__main__":
    path = run()
    print(f"Wrote teammate update to {path}")
