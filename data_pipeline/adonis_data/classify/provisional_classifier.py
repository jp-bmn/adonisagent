"""Provisional classifier used until Joel's rules_engine + Claude path is connected."""

from __future__ import annotations

from dataclasses import dataclass

from adonis_data.models import RawSignal


@dataclass(frozen=True)
class ClassificationResult:
    signal_type: str
    tier: str
    confidence_score: float
    one_sentence_summary: str
    why_relevant_to_adonis: str
    rules_engine_hit: bool
    rules_engine_reason: str


_SIGNAL_TYPE_RULES: list[tuple[str, list[str]]] = [
    ("leadership_change", ["ceo", "cfo", "cro", "chief", "appointed", "step down", "resign"]),
    ("vendor_dispute", ["lawsuit", "sues", "antitrust", "dispute", "failure"]),
    ("ma_acquisition", ["acquire", "acquisition", "merger", "affiliation", "divestiture"]),
    ("epic_go_live", ["epic go-live", "epic go live", "ehr rollout", "epic implementation"]),
    ("post_golive_friction", ["post go-live", "friction", "interoperability issue", "breakdown"]),
    ("restructuring", ["layoff", "closure", "restructuring", "reorganization", "cuts"]),
    ("rcm_hiring_spike", ["hiring", "job posting", "denials", "ar specialist", "revenue cycle role"]),
    ("ai_adoption_outside_rcm", ["ai tool", "artificial intelligence", "automation tool"]),
    ("thought_leadership", ["interview", "speaker", "advisory board", "thought leadership"]),
    ("financial_event", ["operating income", "margin", "credit", "bond", "profit"]),
]


def _infer_signal_type(signal: RawSignal) -> str:
    blob = f"{signal.title} {signal.excerpt}".lower()
    for signal_type, keywords in _SIGNAL_TYPE_RULES:
        if any(keyword in blob for keyword in keywords):
            return signal_type

    if "epic" in signal.matched_topics:
        return "epic_go_live"
    if "acquisition" in signal.matched_topics:
        return "ma_acquisition"
    if "leadership" in signal.matched_topics:
        return "leadership_change"
    return "automation_proof"


def _apply_local_rules(signal: RawSignal, signal_type: str) -> tuple[str, float, bool, str]:
    text = f"{signal.title} {signal.excerpt}".lower()

    if signal_type == "leadership_change" and any(role in text for role in ["cro", "cfo", "crco", "vp revenue cycle"]):
        return "urgent", 1.0, True, "leadership_role_priority"
    if signal_type in {"vendor_dispute", "ma_acquisition", "epic_go_live", "post_golive_friction", "restructuring"}:
        return "urgent", 1.0, True, f"forced_{signal_type}"
    if signal_type == "rcm_hiring_spike":
        return "urgent", 0.95, True, "forced_rcm_hiring_spike"
    if signal_type == "ai_adoption_outside_rcm":
        return "worth_knowing", 0.90, True, "forced_ai_adoption_outside_rcm"
    if signal_type == "thought_leadership":
        return "worth_knowing", 0.85, True, "forced_thought_leadership"

    return "worth_knowing", 0.75, False, "default_provisional_rule"


def _apply_quality_penalty(signal: RawSignal, confidence: float, reason: str) -> tuple[float, str]:
    title_len = len(signal.title.strip())
    excerpt_len = len(signal.excerpt.strip())

    penalty = 0.0
    tags: list[str] = [reason]

    # Very short signals are often low-information snippets from index pages.
    if title_len < 45:
        penalty += 0.08
        tags.append("short_title_penalty")
    if excerpt_len < 110:
        penalty += 0.12
        tags.append("short_excerpt_penalty")

    adjusted = max(0.50, min(1.0, confidence - penalty))
    return adjusted, "|".join(tags)


def classify_signal(signal: RawSignal) -> ClassificationResult:
    signal_type = _infer_signal_type(signal)
    tier, confidence, rules_hit, reason = _apply_local_rules(signal, signal_type)
    confidence, reason = _apply_quality_penalty(signal, confidence, reason)

    summary = signal.excerpt.strip() or signal.title.strip()
    summary = summary.split(".")[0].strip() if summary else signal.title.strip()
    if summary and not summary.endswith("."):
        summary = f"{summary}."

    why = (
        "Potential revenue cycle impact or buying-signal relevance for Adonis territory accounts."
        if tier == "urgent"
        else "Useful context for account monitoring and weekly AE planning."
    )

    return ClassificationResult(
        signal_type=signal_type,
        tier=tier,
        confidence_score=confidence,
        one_sentence_summary=summary,
        why_relevant_to_adonis=why,
        rules_engine_hit=rules_hit,
        rules_engine_reason=reason,
    )
