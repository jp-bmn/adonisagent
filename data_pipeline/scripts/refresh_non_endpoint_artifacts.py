"""Refresh day2 artifacts without posting to backend endpoints."""

from __future__ import annotations

import json
import os
from pathlib import Path

from scripts.generate_client_feed_preview import run as run_client_feed_preview
from scripts.generate_status_snapshot import run as run_status_snapshot
from scripts.generate_team_update import run as run_team_update
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
    snapshot_md_path, snapshot_html_path = run_status_snapshot()
    client_preview_paths = run_client_feed_preview()
    team_update_path = run_team_update()

    outputs_dir = Path("outputs")
    run_log = _read_json(outputs_dir / "day2_run_log.json")
    contact = _read_json(outputs_dir / "day2_contact_leads.json")

    print("Refreshed artifacts:")
    print(f"- raw signals: {day1_path}")
    print(f"- contact leads: {contact_path}")
    print(f"- status snapshot: {snapshot_md_path}")
    print(f"- test page: {snapshot_html_path}")
    print(f"- client feed preview (light): {client_preview_paths['light']}")
    print(f"- client feed preview (dark): {client_preview_paths['dark']}")
    print(f"- preserved client preview (light v1): {client_preview_paths['light_v1']}")
    print(f"- teammate update (plain english): {team_update_path}")
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
    print(f"- open_test_page: file://{snapshot_html_path.resolve()}")
    print(f"- open_client_preview_light: file://{client_preview_paths['light'].resolve()}")
    print(f"- open_client_preview_dark: file://{client_preview_paths['dark'].resolve()}")


if __name__ == "__main__":
    run()