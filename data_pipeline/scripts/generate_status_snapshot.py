"""Generate a concise status snapshot and local HTML test page."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path


def _read_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _format_bucket_counts(raw: object) -> str:
    if not isinstance(raw, dict):
        return "{}"
    high = int(raw.get("high", 0) or 0)
    medium = int(raw.get("medium", 0) or 0)
    low = int(raw.get("low", 0) or 0)
    missing = int(raw.get("missing", 0) or 0)
    return f"high={high}, medium={medium}, low={low}, missing={missing}"


def _build_markdown(now_utc: datetime, run_log: dict[str, object], contact: dict[str, object]) -> str:
    delivery = run_log.get("delivery")
    delivery_enabled = False
    delivery_delivered = False
    if isinstance(delivery, dict):
        delivery_enabled = bool(delivery.get("enabled", False))
        delivery_delivered = bool(delivery.get("delivered", False))

    lines: list[str] = []
    lines.append("# Day 2 Status Snapshot")
    lines.append("")
    lines.append(f"Generated: {now_utc.isoformat()}")
    lines.append("")
    lines.append("## Pipeline")
    lines.append(f"- signals_new: {int(run_log.get('signals_new', 0) or 0)}")
    lines.append(f"- signals_skipped: {int(run_log.get('signals_skipped', 0) or 0)}")
    lines.append(f"- rules_engine_hits: {int(run_log.get('rules_engine_hits', 0) or 0)}")
    lines.append(f"- duration_ms: {int(run_log.get('duration_ms', 0) or 0)}")
    lines.append("")
    lines.append("## Delivery")
    lines.append(f"- delivery_enabled: {delivery_enabled}")
    lines.append(f"- delivered: {delivery_delivered}")
    lines.append("")
    lines.append("## Contact Lead QA")
    lines.append(f"- lead_count: {int(contact.get('lead_count', 0) or 0)}")
    lines.append(
        "- recommended_for_manual_review_count: "
        f"{int(contact.get('recommended_for_manual_review_count', 0) or 0)}"
    )
    lines.append(f"- rejected_matches_count: {int(contact.get('rejected_matches_count', 0) or 0)}")
    lines.append(f"- match_bucket_counts: {_format_bucket_counts(contact.get('match_bucket_counts', {}))}")
    lines.append("")
    lines.append("## Artifacts")
    lines.append(f"- review_markdown: {str(contact.get('review_report_path', ''))}")
    lines.append(f"- review_csv: {str(contact.get('review_csv_path', ''))}")
    lines.append("- handoff_summary: outputs/day2_handoff_summary.md")
    lines.append("")
    return "\n".join(lines)


def _build_html(now_utc: datetime, run_log: dict[str, object], contact: dict[str, object]) -> str:
    delivery = run_log.get("delivery")
    delivery_enabled = False
    delivery_delivered = False
    if isinstance(delivery, dict):
        delivery_enabled = bool(delivery.get("enabled", False))
        delivery_delivered = bool(delivery.get("delivered", False))

    signals_new = int(run_log.get("signals_new", 0) or 0)
    signals_skipped = int(run_log.get("signals_skipped", 0) or 0)
    rules_hits = int(run_log.get("rules_engine_hits", 0) or 0)
    duration_ms = int(run_log.get("duration_ms", 0) or 0)
    lead_count = int(contact.get("lead_count", 0) or 0)
    recommended_count = int(contact.get("recommended_for_manual_review_count", 0) or 0)
    rejected_count = int(contact.get("rejected_matches_count", 0) or 0)

    bucket_counts = _format_bucket_counts(contact.get("match_bucket_counts", {}))
    review_md = str(contact.get("review_report_path", ""))
    review_csv = str(contact.get("review_csv_path", ""))

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Adonis Day 2 Test Page</title>
  <style>
    :root {{
      --bg: #f6f4ef;
      --ink: #1f1f1f;
      --muted: #5f5a53;
      --card: #fffdf8;
      --line: #ddd4c5;
      --good: #1f7a4d;
      --warn: #8b5e00;
      --bad: #9c2f2f;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif;
      color: var(--ink);
      background: radial-gradient(circle at 20% 0%, #fff6d9 0%, var(--bg) 48%);
    }}
    .wrap {{ max-width: 980px; margin: 0 auto; padding: 28px 20px 40px; }}
    h1 {{ margin: 0 0 6px; font-size: 1.8rem; }}
    .stamp {{ color: var(--muted); margin-bottom: 18px; }}
    .grid {{ display: grid; gap: 14px; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 14px; }}
    .label {{ color: var(--muted); font-size: 0.85rem; margin-bottom: 6px; }}
    .value {{ font-size: 1.4rem; font-weight: 700; }}
    .good {{ color: var(--good); }}
    .warn {{ color: var(--warn); }}
    .bad {{ color: var(--bad); }}
    .panel {{ margin-top: 14px; background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 14px; }}
    .mono {{ font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; }}
    ul {{ margin: 8px 0 0 18px; padding: 0; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>Adonis Day 2 Test Page</h1>
    <div class=\"stamp\">Generated: {now_utc.isoformat()}</div>
    <div class=\"grid\">
      <section class=\"card\"><div class=\"label\">Signals New</div><div class=\"value\">{signals_new}</div></section>
      <section class=\"card\"><div class=\"label\">Signals Skipped</div><div class=\"value\">{signals_skipped}</div></section>
      <section class=\"card\"><div class=\"label\">Rules Hits</div><div class=\"value\">{rules_hits}</div></section>
      <section class=\"card\"><div class=\"label\">Run Duration (ms)</div><div class=\"value\">{duration_ms}</div></section>
      <section class=\"card\"><div class=\"label\">Recommended Leads</div><div class=\"value good\">{recommended_count}</div></section>
      <section class=\"card\"><div class=\"label\">Rejected Matches</div><div class=\"value bad\">{rejected_count}</div></section>
    </div>

    <section class=\"panel\">
      <div><strong>Delivery Enabled:</strong> <span class=\"mono\">{delivery_enabled}</span></div>
      <div><strong>Delivered:</strong> <span class=\"mono\">{delivery_delivered}</span></div>
      <div><strong>Lead Count:</strong> <span class=\"mono\">{lead_count}</span></div>
      <div><strong>Bucket Counts:</strong> <span class=\"mono\">{bucket_counts}</span></div>
    </section>

    <section class=\"panel\">
      <div><strong>Artifacts</strong></div>
      <ul>
        <li class=\"mono\">{review_md}</li>
        <li class=\"mono\">{review_csv}</li>
        <li class=\"mono\">outputs/day2_handoff_summary.md</li>
        <li class=\"mono\">outputs/day2_status_snapshot.md</li>
      </ul>
    </section>
  </div>
</body>
</html>
"""


def run() -> tuple[Path, Path]:
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)
    run_log = _read_json(outputs_dir / "day2_run_log.json")
    contact = _read_json(outputs_dir / "day2_contact_leads.json")
    now_utc = datetime.now(timezone.utc)

    md_path = outputs_dir / "day2_status_snapshot.md"
    html_path = outputs_dir / "day2_test_page.html"
    md_path.write_text(_build_markdown(now_utc, run_log, contact), encoding="utf-8")
    html_path.write_text(_build_html(now_utc, run_log, contact), encoding="utf-8")
    return md_path, html_path


if __name__ == "__main__":
    markdown_path, html_path = run()
    print(f"Wrote status snapshot to {markdown_path}")
    print(f"Wrote test page to {html_path}")