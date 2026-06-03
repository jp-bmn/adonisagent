"""Generate a client-facing preview page from classified signals."""

from __future__ import annotations

import html
import json
from collections import Counter
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


def _sort_signals(signals: list[dict[str, object]]) -> list[dict[str, object]]:
    tier_rank = {"urgent": 0, "worth_knowing": 1, "filtered_out": 2}
    return sorted(
        signals,
        key=lambda s: (
            tier_rank.get(str(s.get("tier", "worth_knowing")), 9),
            -float(s.get("confidence_score", 0.0) or 0.0),
        ),
    )


def _render_signal_card(signal: dict[str, object]) -> str:
    hospital = html.escape(str(signal.get("hospital", "Unknown hospital")))
    title = html.escape(str(signal.get("title", "Untitled signal")))
    source = html.escape(str(signal.get("source", "Unknown source")))
    url = html.escape(str(signal.get("url", "")))
    tier = html.escape(str(signal.get("tier", "worth_knowing")))
    confidence = float(signal.get("confidence_score", 0.0) or 0.0)
    summary = str(signal.get("one_sentence_summary", "")).strip() or str(signal.get("excerpt", "")).strip()
    summary = html.escape(summary)

    tier_class = "tier-worth"
    if tier == "urgent":
        tier_class = "tier-urgent"
    elif tier == "filtered_out":
        tier_class = "tier-filtered"

    link_html = ""
    if url:
        link_html = f'<a class="source-link" href="{url}" target="_blank" rel="noreferrer">Open source</a>'

    return (
        "<article class=\"card\">"
        f"<div class=\"meta\"><span class=\"chip {tier_class}\">{tier}</span>"
        f"<span class=\"confidence\">conf {confidence:.2f}</span></div>"
        f"<h3>{title}</h3>"
        f"<p>{summary}</p>"
        f"<div class=\"foot\"><span>{hospital}</span><span>{source}</span>{link_html}</div>"
        "</article>"
    )


def _build_page(
    now_utc: str,
    signals: list[dict[str, object]],
    tier_counts: Counter[str],
    top_sources: str,
    cards_html: str,
    theme: str,
) -> str:
    if theme == "dark":
        palette = {
            "bg": "#10151c",
            "gradient": "#1a2636",
            "card": "#16212f",
            "ink": "#edf2f7",
            "muted": "#a9b7c8",
            "line": "#28384d",
            "urgent": "#f97066",
            "worth": "#56b4fc",
            "filtered": "#9ca3af",
            "accent": "#4fd1c5",
        }
        title = "Adonis Client Feed Preview (Dark)"
    else:
        palette = {
            "bg": "#eef3f6",
            "gradient": "#dfeef2",
            "card": "#ffffff",
            "ink": "#1b2430",
            "muted": "#55606f",
            "line": "#d8e0e8",
            "urgent": "#b42318",
            "worth": "#0b4f8c",
            "filtered": "#6b7280",
            "accent": "#0f766e",
        }
        title = "Adonis Client Feed Preview"

    return f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>{title}</title>
  <style>
    :root {{
      --bg: {palette['bg']};
      --card: {palette['card']};
      --ink: {palette['ink']};
      --muted: {palette['muted']};
      --line: {palette['line']};
      --urgent: {palette['urgent']};
      --worth: {palette['worth']};
      --filtered: {palette['filtered']};
      --accent: {palette['accent']};
    }}
    * {{ box-sizing: border-box; }}
    body {{ margin: 0; font-family: ui-sans-serif, -apple-system, Segoe UI, Helvetica, Arial, sans-serif; color: var(--ink); background: linear-gradient(180deg, {palette['gradient']} 0%, var(--bg) 35%); }}
    .wrap {{ max-width: 1120px; margin: 0 auto; padding: 24px 18px 34px; }}
    h1 {{ margin: 0; font-size: 2rem; }}
    .stamp {{ margin: 4px 0 14px; color: var(--muted); }}
    .stats {{ display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); margin-bottom: 12px; }}
    .stat {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 10px 12px; }}
    .stat .k {{ color: var(--muted); font-size: 0.85rem; }}
    .stat .v {{ font-size: 1.4rem; font-weight: 700; }}
    .panel {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 12px; margin-bottom: 12px; }}
    .feed {{ display: grid; gap: 10px; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); }}
    .card {{ background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 12px; display: flex; flex-direction: column; gap: 8px; }}
    .meta {{ display: flex; justify-content: space-between; align-items: center; }}
    .chip {{ font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.02em; padding: 3px 8px; border-radius: 999px; color: white; }}
    .tier-urgent {{ background: var(--urgent); }}
    .tier-worth {{ background: var(--worth); }}
    .tier-filtered {{ background: var(--filtered); }}
    .confidence {{ color: var(--muted); font-size: 0.8rem; }}
    h3 {{ margin: 0; font-size: 1rem; line-height: 1.3; }}
    p {{ margin: 0; color: var(--muted); font-size: 0.92rem; line-height: 1.35; }}
    .foot {{ display: flex; gap: 10px; flex-wrap: wrap; align-items: center; color: var(--muted); font-size: 0.82rem; }}
    .source-link {{ margin-left: auto; color: var(--accent); text-decoration: none; font-weight: 600; }}
  </style>
</head>
<body>
  <div class=\"wrap\">
    <h1>{title}</h1>
    <div class=\"stamp\">Generated: {now_utc}</div>
    <section class=\"stats\">
      <div class=\"stat\"><div class=\"k\">Total Classified</div><div class=\"v\">{len(signals)}</div></div>
      <div class=\"stat\"><div class=\"k\">Urgent</div><div class=\"v\">{tier_counts.get('urgent', 0)}</div></div>
      <div class=\"stat\"><div class=\"k\">Worth Knowing</div><div class=\"v\">{tier_counts.get('worth_knowing', 0)}</div></div>
      <div class=\"stat\"><div class=\"k\">Filtered Out</div><div class=\"v\">{tier_counts.get('filtered_out', 0)}</div></div>
    </section>
    <section class=\"panel\">
      <strong>Top Sources</strong>
      <ul>
        {top_sources}
      </ul>
    </section>
    <section class=\"feed\">
      {cards_html}
    </section>
  </div>
</body>
</html>
"""


def run(max_items: int = 40) -> dict[str, Path]:
    outputs_dir = Path("outputs")
    outputs_dir.mkdir(parents=True, exist_ok=True)

    classified = _read_json(outputs_dir / "day2_classified_candidates.json")
    rows = classified.get("signals", [])
    if not isinstance(rows, list):
        rows = []

    signals = [row for row in rows if isinstance(row, dict)]
    ranked = _sort_signals(signals)[: max(1, max_items)]

    tier_counts: Counter[str] = Counter(str(s.get("tier", "worth_knowing")) for s in signals)
    source_counts: Counter[str] = Counter(str(s.get("source", "Unknown")) for s in signals)

    cards_html = "\n".join(_render_signal_card(s) for s in ranked)
    top_sources = "\n".join(
        f"<li>{html.escape(source)}: {count}</li>"
        for source, count in source_counts.most_common(8)
    )

    now_utc = datetime.now(timezone.utc).isoformat()

    light_path = outputs_dir / "day2_client_feed_preview.html"
    dark_path = outputs_dir / "day2_client_feed_preview_dark.html"
    archived_light_v1_path = outputs_dir / "day2_client_feed_preview_light_v1.html"

    if light_path.exists() and not archived_light_v1_path.exists():
        archived_light_v1_path.write_text(light_path.read_text(encoding="utf-8"), encoding="utf-8")

    light_page = _build_page(
        now_utc=now_utc,
        signals=signals,
        tier_counts=tier_counts,
        top_sources=top_sources,
        cards_html=cards_html,
        theme="light",
    )
    dark_page = _build_page(
        now_utc=now_utc,
        signals=signals,
        tier_counts=tier_counts,
        top_sources=top_sources,
        cards_html=cards_html,
        theme="dark",
    )

    light_path.write_text(light_page, encoding="utf-8")
    dark_path.write_text(dark_page, encoding="utf-8")
    return {
        "light": light_path,
        "dark": dark_path,
        "light_v1": archived_light_v1_path,
    }


if __name__ == "__main__":
  pages = run()
  print(f"Wrote client feed preview (light) to {pages['light']}")
  print(f"Wrote client feed preview (dark) to {pages['dark']}")
  print(f"Saved original light version at {pages['light_v1']}")