"""Refresh day2 artifacts without posting to backend endpoints."""

from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.run_contact_linkedin_discovery import run as run_contact_discovery
from scripts.run_day1_collection import run as run_day1_collection


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def run() -> None:
    # Keep this refresh endpoint-independent and avoid outbox growth.
    os.environ["POST_SIGNALS_ENABLED"] = "false"
    os.environ["OUTBOX_ENABLED"] = "false"

    day1_path = run_day1_collection()
    contact_path = run_contact_discovery()

    outputs_dir = Path("outputs")
    run_log = _read_json(outputs_dir / "day2_run_log.json")
    contact = _read_json(outputs_dir / "day2_contact_leads.json")

    print("Refreshed artifacts:")
    print(f"- raw signals: {day1_path}")
    print(f"- contact leads: {contact_path}")
    print("")
    print("Readiness snapshot:")
    print(f"- signals_new: {run_log.get('signals_new', 0)}")
    print(f"- signals_skipped: {run_log.get('signals_skipped', 0)}")
    print(f"- delivery_enabled: {((run_log.get('delivery') or {}).get('enabled', False))}")
    print(
        "- recommended_for_manual_review_count: "
        f"{contact.get('recommended_for_manual_review_count', 0)}"
    )
    print(f"- rejected_matches_count: {contact.get('rejected_matches_count', 0)}")
    print(f"- review_report_path: {contact.get('review_report_path', '')}")


if __name__ == "__main__":
    run()