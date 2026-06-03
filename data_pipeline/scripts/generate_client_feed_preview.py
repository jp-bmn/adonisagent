"""Generate client-facing feed preview pages (light and dark)."""

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


def _format_label(value: str) -> str:
    text = value.replace("_", " ").strip()
    return " ".join(part.capitalize() for part in text.split())


def _render_signal_card(signal: dict[str, object]) -> str:
    hospital = html.escape(str(signal.get("hospital", "Unknown hospital")))
    title = html.escape(str(signal.get("title", "Untitled signal")))
    source = html.escape(str(signal.get("source", "Unknown source")))
    url = html.escape(str(signal.get("url", "")))
    tier = html.escape(_format_label(str(signal.get("tier", "worth_knowing"))))
    confidence = float(signal.get("confidence_score", 0.0) or 0.0)
    summary = str(signal.get("one_sentence_summary", "")).strip() or str(signal.get("excerpt", "")).strip()
    summary = html.escape(summary)

    tier_class = "tier-worth"
    if tier.lower() == "urgent":
        tier_class = "tier-urgent"
    elif tier.lower() == "filtered out":
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


def _render_dark_signal_card(signal: dict[str, object], hospital_color: str) -> str:
    hospital = html.escape(str(signal.get("hospital", "Unknown hospital")))
    title = html.escape(str(signal.get("title", "Untitled signal")))
    source = html.escape(str(signal.get("source", "Unknown source")))
    url = html.escape(str(signal.get("url", "")))
    tier_raw = str(signal.get("tier", "worth_knowing"))
    tier_label = html.escape(_format_label(tier_raw))
    signal_type = html.escape(_format_label(str(signal.get("signal_type", "strategy"))))
    confidence = float(signal.get("confidence_score", 0.0) or 0.0)
    why = html.escape(
        str(signal.get("why_relevant_to_adonis", "")).strip()
        or "Potential revenue cycle impact or buying-signal relevance for Adonis territory accounts."
    )

    urgency_badge = "badge badge-muted"
    card_class = "card"
    if tier_raw == "urgent":
        urgency_badge = "badge badge-danger"
        card_class = "card urgent"
    elif tier_raw == "worth_knowing":
        urgency_badge = "badge badge-warn"

    link_html = ""
    if url:
        link_html = (
            f'<a class="act-icon" title="Open article" href="{url}" target="_blank" rel="noreferrer">'
            '<i class="ti ti-external-link"></i></a>'
        )

    return (
        f'<div class="{card_class}">'
        '<div class="card-top">'
        f'<span class="hosp-dot" style="background:{hospital_color}"></span>'
        f'<span class="hosp-name">{hospital}</span>'
        f'<span class="{urgency_badge}">{tier_label}</span>'
        f'<span class="badge badge-type">{signal_type}</span>'
        f'<span class="card-time">conf {confidence:.2f}</span>'
        '</div>'
        f'<p class="card-summary">{title}</p>'
        f'<p class="card-why">{why}</p>'
        '<div class="card-footer">'
        f'<div class="card-meta"><span>{source}</span></div>'
        '<div class="card-actions">'
        '<button class="act-icon" title="Save"><i class="ti ti-bookmark"></i></button>'
        f'{link_html}'
        '</div></div></div>'
    )


def _build_dark_intel_page(now_utc: str, signals: list[dict[str, object]], ranked: list[dict[str, object]], tier_counts: Counter[str]) -> str:
    hospitals: list[str] = []
    for signal in ranked:
        hospital = str(signal.get("hospital", "Unknown hospital"))
        if hospital not in hospitals:
            hospitals.append(hospital)

    palette = ["#378ADD", "#00C48C", "#D85A30", "#F5A623", "#A78BFA", "#7DD3FC"]
    hospital_colors = {hospital: palette[idx % len(palette)] for idx, hospital in enumerate(hospitals)}

    urgent_signals = [s for s in ranked if str(s.get("tier", "")) == "urgent"]
    week_signals = [s for s in ranked if str(s.get("tier", "")) != "urgent"]

    urgent_cards = "\n".join(
        _render_dark_signal_card(signal, hospital_colors.get(str(signal.get("hospital", "")), "#378ADD"))
        for signal in urgent_signals[:12]
    )
    week_cards = "\n".join(
        _render_dark_signal_card(signal, hospital_colors.get(str(signal.get("hospital", "")), "#378ADD"))
        for signal in week_signals[:24]
    )

    hospital_items = "\n".join(
        (
            '<div class="sb-item">'
            f'<span class="hosp-dot" style="background:{hospital_colors[hospital]}"></span>'
            f'{html.escape(hospital)}'
            '</div>'
        )
        for hospital in hospitals
    )

    return f"""<!doctype html>
<html lang=\"en\">
<head>
<meta charset=\"UTF-8\" />
<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
<title>Adonis Intel - Client Preview (Dark)</title>
<link rel=\"preconnect\" href=\"https://fonts.googleapis.com\" />
<link href=\"https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap\" rel=\"stylesheet\" />
<link rel=\"stylesheet\" href=\"https://cdn.jsdelivr.net/npm/@tabler/icons-webfont@latest/tabler-icons.min.css\" />
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  :root {{
    --ad-bg: #0D1117; --ad-surface: #161C26; --ad-surface2: #1E2633; --ad-border: rgba(255,255,255,0.08); --ad-border2: rgba(255,255,255,0.13);
    --ad-green: #00C48C; --ad-green-dim: rgba(0,196,140,0.10); --ad-green-border: rgba(0,196,140,0.20);
    --ad-text: #F0F4F8; --ad-muted: #8896A8; --ad-subtle: #BCC8D4; --ad-danger: #FF5C5C; --ad-danger-bg: rgba(255,92,92,0.10); --ad-warn: #F5A623; --ad-warn-bg: rgba(245,166,35,0.10);
  }}
  html, body {{ height: 100%; background: var(--ad-bg); font-family: 'Inter', sans-serif; color: var(--ad-text); font-size: 13px; }}
  .app {{ display: flex; flex-direction: column; min-height: 100vh; }}
  .topbar {{ display: flex; align-items: center; gap: 14px; padding: 0 20px; height: 48px; background: var(--ad-surface); border-bottom: 1px solid var(--ad-border); }}
  .logo {{ font-size: 13px; font-weight: 700; letter-spacing: 0.08em; color: var(--ad-green); }}
  .logo-sep {{ color: var(--ad-border2); margin: 0 2px; }}
  .logo-sub {{ font-size: 11px; font-weight: 500; letter-spacing: 0.06em; color: var(--ad-muted); }}
  .topbar-right {{ margin-left: auto; display: flex; align-items: center; gap: 8px; }}
  .tb-btn {{ display: flex; align-items: center; gap: 5px; font-size: 11px; font-weight: 500; padding: 5px 11px; border-radius: 6px; border: 1px solid var(--ad-border2); color: var(--ad-muted); background: transparent; cursor: pointer; transition: border-color 0.15s, color 0.15s; }}
  .tb-btn:hover {{ border-color: var(--ad-green); color: var(--ad-green); }}
  .avatar {{ width: 28px; height: 28px; border-radius: 50%; background: var(--ad-green-dim); border: 1px solid var(--ad-green); display: flex; align-items: center; justify-content: center; font-size: 10px; font-weight: 700; color: var(--ad-green); letter-spacing: 0.04em; }}
  .body {{ display: flex; flex: 1; min-height: 0; }}
  .sidebar {{ width: 196px; border-right: 1px solid var(--ad-border); background: var(--ad-surface); overflow-y: auto; padding: 16px 0; }}
  .sb-section {{ padding: 0 12px; margin-bottom: 22px; }}
  .sb-label {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.09em; color: var(--ad-muted); margin-bottom: 8px; padding: 0 6px; }}
  .sb-item {{ display: flex; align-items: center; gap: 8px; padding: 6px 8px; border-radius: 6px; font-size: 12px; color: var(--ad-muted); border: 1px solid transparent; transition: background 0.12s, color 0.12s, border-color 0.12s; }}
  .sb-item:hover {{ background: var(--ad-surface2); color: var(--ad-text); }}
  .sb-item.active {{ background: var(--ad-green-dim); color: var(--ad-green); border-color: var(--ad-green-border); }}
  .sb-badge {{ margin-left: auto; font-size: 10px; font-weight: 700; padding: 1px 6px; border-radius: 20px; }}
  .sb-badge-danger {{ background: var(--ad-danger-bg); color: var(--ad-danger); }}
  .sb-badge-muted {{ background: rgba(255,255,255,0.06); color: var(--ad-muted); }}
  .hosp-dot {{ width: 7px; height: 7px; border-radius: 50%; flex-shrink: 0; }}
  .main {{ flex: 1; display: flex; flex-direction: column; min-width: 0; }}
  .main-header {{ padding: 14px 20px 12px; background: var(--ad-surface); border-bottom: 1px solid var(--ad-border); }}
  .main-title {{ font-size: 15px; font-weight: 600; margin-bottom: 3px; }}
  .main-sub {{ font-size: 12px; color: var(--ad-muted); }}
  .main-sub strong {{ color: var(--ad-danger); font-weight: 600; }}
  .filter-row {{ display: flex; gap: 7px; padding: 9px 20px; background: var(--ad-surface); border-bottom: 1px solid var(--ad-border); flex-wrap: wrap; align-items: center; }}
  .filter-btn {{ font-size: 11px; font-weight: 500; padding: 4px 11px; border-radius: 20px; border: 1px solid var(--ad-border2); color: var(--ad-muted); background: transparent; }}
  .filter-btn.on.danger {{ background: var(--ad-danger-bg); color: var(--ad-danger); border-color: rgba(255,92,92,0.28); }}
  .filter-btn.on.warn {{ background: var(--ad-warn-bg); color: var(--ad-warn); border-color: rgba(245,166,35,0.28); }}
  .filter-btn.on {{ background: var(--ad-surface2); color: var(--ad-text); }}
  .filter-sep {{ width: 1px; height: 14px; background: var(--ad-border2); margin: 0 2px; flex-shrink: 0; }}
  .feed {{ flex: 1; overflow-y: auto; padding: 14px 20px; display: flex; flex-direction: column; gap: 10px; }}
  .feed::-webkit-scrollbar {{ width: 4px; }}
  .feed::-webkit-scrollbar-track {{ background: transparent; }}
  .feed::-webkit-scrollbar-thumb {{ background: var(--ad-surface2); border-radius: 2px; }}
  .section-label {{ font-size: 10px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: var(--ad-muted); padding: 2px 0; }}
  .card {{ background: var(--ad-surface); border: 1px solid var(--ad-border); border-radius: 10px; padding: 13px 15px; cursor: pointer; transition: border-color 0.15s; }}
  .card:hover {{ border-color: var(--ad-border2); }}
  .card.urgent {{ border-left: 2px solid var(--ad-danger); border-radius: 0 10px 10px 0; }}
  .card-top {{ display: flex; align-items: center; gap: 7px; margin-bottom: 9px; flex-wrap: wrap; }}
  .hosp-name {{ font-size: 13px; font-weight: 600; }}
  .badge {{ font-size: 10px; font-weight: 600; padding: 2px 7px; border-radius: 20px; }}
  .badge-danger {{ background: var(--ad-danger-bg); color: var(--ad-danger); }}
  .badge-warn {{ background: var(--ad-warn-bg); color: var(--ad-warn); }}
  .badge-muted {{ background: rgba(255,255,255,0.06); color: var(--ad-muted); }}
  .badge-type {{ background: var(--ad-green-dim); color: var(--ad-green); }}
  .card-time {{ margin-left: auto; font-size: 11px; color: var(--ad-muted); }}
  .card-summary {{ font-size: 12px; color: var(--ad-subtle); line-height: 1.6; margin-bottom: 7px; }}
  .card-why {{ font-size: 11px; font-weight: 500; line-height: 1.55; margin-bottom: 10px; padding: 6px 10px; background: var(--ad-green-dim); border-left: 2px solid var(--ad-green); color: var(--ad-green); border-radius: 0 5px 5px 0; }}
  .card-footer {{ display: flex; justify-content: space-between; align-items: center; }}
  .card-meta {{ font-size: 11px; color: var(--ad-muted); }}
  .card-actions {{ display: flex; gap: 5px; }}
  .act-icon {{ display: flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 6px; border: 1px solid var(--ad-border2); color: var(--ad-muted); background: transparent; text-decoration: none; cursor: pointer; transition: all 0.12s; }}
  .act-icon:hover {{ border-color: var(--ad-green); color: var(--ad-green); }}
  .empty-state {{ display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 48px 24px; color: var(--ad-muted); text-align: center; gap: 8px; }}
</style>
</head>
<body>
<div class=\"app\">
  <div class=\"topbar\">
    <span class=\"logo\">ADONIS<span class=\"logo-sep\"> · </span><span class=\"logo-sub\">INTEL</span></span>
    <div class=\"topbar-right\">
      <button class=\"tb-btn\"><i class=\"ti ti-bell\" style=\"font-size:13px\"></i> Alerts</button>
      <button class=\"tb-btn\"><i class=\"ti ti-settings\" style=\"font-size:13px\"></i> Preferences</button>
      <div class=\"avatar\">MC</div>
    </div>
  </div>
  <div class=\"body\">
    <div class=\"sidebar\">
      <div class=\"sb-section\">
        <div class=\"sb-label\">Views</div>
        <div class=\"sb-item active\"><i class=\"ti ti-layout-list\"></i> All signals <span class=\"sb-badge sb-badge-danger\">{len(signals)}</span></div>
        <div class=\"sb-item\"><i class=\"ti ti-alert-circle\"></i> Urgent <span class=\"sb-badge sb-badge-danger\">{tier_counts.get('urgent', 0)}</span></div>
        <div class=\"sb-item\"><i class=\"ti ti-network\"></i> Connections <span class=\"sb-badge sb-badge-muted\">1</span></div>
      </div>
      <div class=\"sb-section\">
        <div class=\"sb-label\">My accounts</div>
        <div class=\"sb-item active\"><i class=\"ti ti-building-hospital\"></i> All accounts</div>
        {hospital_items}
      </div>
      <div class=\"sb-section\">
        <div class=\"sb-label\">Signal type</div>
        <div class=\"sb-item\"><i class=\"ti ti-user-check\"></i> Executive</div>
        <div class=\"sb-item\"><i class=\"ti ti-arrows-join\"></i> M&A</div>
        <div class=\"sb-item\"><i class=\"ti ti-chart-bar\"></i> Financial</div>
        <div class=\"sb-item\"><i class=\"ti ti-scale\"></i> Regulatory</div>
        <div class=\"sb-item\"><i class=\"ti ti-target\"></i> Strategy</div>
      </div>
    </div>
    <div class=\"main\">
      <div class=\"main-header\">
        <div class=\"main-title\">My intel feed</div>
        <div class=\"main-sub\">Generated {now_utc} · {len(hospitals)} accounts · <strong>{tier_counts.get('urgent', 0)} urgent signals</strong></div>
      </div>
      <div class=\"filter-row\">
        <button class=\"filter-btn on danger\"><i class=\"ti ti-alert-circle\" style=\"font-size:11px\"></i> Urgent</button>
        <button class=\"filter-btn on warn\">Medium</button>
        <button class=\"filter-btn on\">Low</button>
        <div class=\"filter-sep\"></div>
        <button class=\"filter-btn on\">Unread</button>
        <button class=\"filter-btn\"><i class=\"ti ti-bookmark\" style=\"font-size:11px\"></i> Saved</button>
      </div>
      <div class=\"feed\">
        <div class=\"section-label\">Urgent — act now</div>
        {urgent_cards if urgent_cards else '<div class="empty-state"><i class="ti ti-check"></i><p>No urgent signals right now.</p></div>'}
        <div class=\"section-label\">This week</div>
        {week_cards if week_cards else '<div class="empty-state"><i class="ti ti-notes"></i><p>No additional signals in this view.</p></div>'}
      </div>
    </div>
  </div>
</div>
</body>
</html>
"""


def _build_page(
    now_utc: str,
    signals: list[dict[str, object]],
    tier_counts: Counter[str],
    top_sources: str,
    cards_html: str,
    theme: str,
) -> str:
    if theme == "dark":
        return _build_dark_intel_page(
            now_utc=now_utc,
            signals=signals,
            ranked=_sort_signals(signals),
            tier_counts=tier_counts,
        )

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
      --bg: {palette['bg']}; --card: {palette['card']}; --ink: {palette['ink']}; --muted: {palette['muted']}; --line: {palette['line']};
      --urgent: {palette['urgent']}; --worth: {palette['worth']}; --filtered: {palette['filtered']}; --accent: {palette['accent']};
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
    .tier-urgent {{ background: var(--urgent); }} .tier-worth {{ background: var(--worth); }} .tier-filtered {{ background: var(--filtered); }}
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
    <section class=\"panel\"><strong>Top Sources</strong><ul>{top_sources}</ul></section>
    <section class=\"feed\">{cards_html}</section>
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
