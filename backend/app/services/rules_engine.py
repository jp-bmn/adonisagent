"""
Rules Engine — Task 5 (Luminai Enforce pattern).

Deterministic tier and signal_type assignment based on keyword matching.
Runs BEFORE Claude to handle clear-cut signals without an LLM call,
saving API cost and latency.

Usage:
    from app.services.rules_engine import classify_with_rules, RulesEngineResult

    result = classify_with_rules(title="CRO departs NYP", text="...")
    if result.matched:
        # Use result.signal_type, result.tier, result.confidence
    else:
        # Fall through to Claude classifier (Task 7)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Optional

# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class RulesEngineResult:
    matched:     bool
    signal_type: Optional[str] = None
    tier:        Optional[str] = None
    confidence:  float         = 0.0
    rule_name:   Optional[str] = None
    matched_keywords: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.matched


# ---------------------------------------------------------------------------
# Valid enums (mirror DB CHECK constraints)
# ---------------------------------------------------------------------------

VALID_SIGNAL_TYPES = frozenset({
    "leadership_change",
    "rcm_hiring_spike",
    "epic_go_live",
    "post_golive_friction",
    "ma_acquisition",
    "vendor_change",
    "vendor_dispute",
    "restructuring",
    "new_hospital_launch",
    "financial_event",
    "ai_adoption_outside_rcm",
    "automation_proof",
    "named_automation_owner",
    "thought_leadership",
    "filtered_out",
})

VALID_TIERS = frozenset({"urgent", "worth_knowing", "filtered_out"})


# ---------------------------------------------------------------------------
# Rule definitions
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name:         str
    signal_type:  str
    tier:         str
    confidence:   float
    # Any of these patterns firing = match (OR logic within a rule)
    # Patterns matched against lowercased combined text (title + body)
    patterns:     list[str]
    # All of these must be absent for the rule to fire (negative guards)
    negative_patterns: list[str] = field(default_factory=list)


# 8 deterministic rules, ordered by specificity (most specific first)
RULES: list[Rule] = [

    # ── Rule 1: Executive / Leadership Change ────────────────────────────────
    # C-suite and VP-level hires, departures, appointments at revenue-touching roles.
    Rule(
        name        = "leadership_change",
        signal_type = "leadership_change",
        tier        = "urgent",
        confidence  = 0.92,
        patterns    = [
            r"\bcro\b",                          # Chief Revenue Officer
            r"chief revenue officer",
            r"\bcfo\b",                          # Chief Financial Officer
            r"chief financial officer",
            r"\bcio\b",                          # Chief Information Officer
            r"chief information officer",
            r"\bcmo\b",                          # Chief Medical Officer (when rcm context)
            r"vp.{0,10}revenue",                 # VP of Revenue (Cycle)
            r"vice president.{0,20}revenue",
            r"vp.{0,10}rcm",
            r"revenue cycle.{0,10}(director|head|lead|vp|vice president)",
            r"(appoint|hire|named|joins|departs?|resign|leaves?|steps? down).{0,40}"
            r"(cro|cfo|cio|chief|vp|vice president)",
            r"(cro|cfo|cio|chief|vp|vice president).{0,40}(appoint|hire|named|joins|departs?|resign|leaves?|steps? down)",
            r"new (cro|cfo|cio|chief revenue|chief financial|chief information)",
            r"(leadership|executive) (change|transition|departure|appointment)",
        ],
        negative_patterns = [
            r"cro croissant",   # edge-case guard (just an example structure)
        ],
    ),

    # ── Rule 2: Post Go-Live Friction ────────────────────────────────────────
    # Must come before epic_go_live (more specific negative signal)
    Rule(
        name        = "post_golive_friction",
        signal_type = "post_golive_friction",
        tier        = "urgent",
        confidence  = 0.90,
        patterns    = [
            r"post.?go.?live",
            r"after.{0,20}(epic|ehr|emr).{0,20}(launch|rollout|implement)",
            r"(billing|claim).{0,30}(problem|issue|error|backlog|delay|drop|decline)",  # billing/claims only — not bare 'revenue'
            r"(cash flow|ar|accounts receivable).{0,20}(impacted|affected|declined|worsened)",
            r"(physician|staff|nurse).{0,20}(frustrat|complain|dissatisf|struggle).{0,20}(epic|ehr|emr|system)",
            r"(denial rate|claim denial).{0,20}(increas|spike|jump|surged|rose)",
            r"revenue.{0,20}(fell|dropped|declined|loss).{0,20}(after|follow|since|because of)",
        ],
    ),

    # ── Rule 3: Epic Go-Live ─────────────────────────────────────────────────
    Rule(
        name        = "epic_go_live",
        signal_type = "epic_go_live",
        tier        = "urgent",
        confidence  = 0.91,
        patterns    = [
            r"epic.{0,20}(go.{0,3}live|launch|rollout|implement|deploy|cutover)",
            r"(go.{0,3}live|launch|rollout).{0,20}epic",
            r"goes.{0,3}live.{0,30}(epic|ehr|emr)",           # "goes live on Epic"
            r"(epic|ehr|emr).{0,30}goes.{0,3}live",
            r"ehr.{0,20}(go.{0,3}live|launch|implement|deploy)",
            r"emr.{0,20}(go.{0,3}live|launch|implement|deploy)",
            r"(electronic health record|electronic medical record).{0,20}(implement|launch|deploy|cutover)",
            r"(deploy|launch|implement|cutover).{0,30}(cerner|meditech)",  # action→vendor
            r"cerner.{0,20}(go.{0,3}live|launch|implement|deploy)",
            r"meditech.{0,20}(go.{0,3}live|launch|implement|deploy)",
        ],
    ),

    # ── Rule 4: M&A / Acquisition ────────────────────────────────────────────
    Rule(
        name        = "ma_acquisition",
        signal_type = "ma_acquisition",
        tier        = "urgent",
        confidence  = 0.93,
        patterns    = [
            r"\bacquir(e|ed|ing)\b",           # acquire / acquired / acquiring
            r"\bacquisition\b",                 # acquisition (no 'r' in word)
            r"\bmerger?\b",
            r"\bmerged?\b",
            r"(acquired|purchase[sd]?) by",
            r"(joint venture|partnership).{0,20}(hospital|health system|health care)",
            r"(combine[sd]?|consolidat).{0,30}(hospital|health system|network)",
            r"takeover",
            r"(affiliate|join).{0,20}(health system|network|consortium)",
        ],
        negative_patterns = [
            r"talent acquisition",
            r"customer acquisition",
        ],
    ),

    # ── Rule 5: Restructuring / Layoffs ──────────────────────────────────────
    Rule(
        name        = "restructuring",
        signal_type = "restructuring",
        tier        = "urgent",
        confidence  = 0.89,
        patterns    = [
            r"\blayoffs?\b",                    # layoff OR layoffs
            r"\brestructur",
            r"workforce reduction",
            r"reduce.{0,20}(workforce|headcount|staff|employees)",
            r"(eliminat|cut).{0,20}(position|job|role|headcount)",
            r"(furlough|redundanc)",
            r"right.?siz",
            r"(department|unit|division).{0,20}(clos|eliminat|consolidat|shutting down)",
            r"(clos|eliminat|shutting down).{0,30}(department|unit|division)",  # reverse order
            r"hospital.{0,20}(clos|shutting down|closing|shut)",
            r"(clos|shutting down).{0,20}hospital",
        ],
        negative_patterns = [
            r"(restructur).{0,20}(loan|debt|bond|financ)",
        ],
    ),

    # ── Rule 6: RCM Hiring Spike ─────────────────────────────────────────────
    Rule(
        name        = "rcm_hiring_spike",
        signal_type = "rcm_hiring_spike",
        tier        = "urgent",
        confidence  = 0.85,
        patterns    = [
            r"rcm.{0,20}(hiring|recruit|open|position|role|job)",
            r"revenue cycle.{0,20}(hiring|recruit|open|position|role|job)",
            r"(billing|coding|claims).{0,20}(specialist|coordinator|analyst|manager).{0,30}(open|hire|recruit|seek|wanted|search)",
            r"(seek|search|hiring|looking for).{0,20}(billing|coding|claims|rcm|revenue cycle)",
            r"(director|manager|vp).{0,20}revenue cycle.{0,20}(open|hire|sought|search)",
            r"revenue cycle.{0,20}(director|manager|vp).{0,20}(open|hire|sought|search)",
            r"(director|manager|vp).{0,10}of.{0,10}revenue cycle",  # "Director of Revenue Cycle" as a sought role
            r"(searching|recruiting|seeking).{0,30}(director|manager|vp).{0,20}revenue",
        ],
    ),

    # ── Rule 7: Vendor Change / Dispute ─────────────────────────────────────
    Rule(
        name        = "vendor_change",
        signal_type = "vendor_change",
        tier        = "urgent",
        confidence  = 0.82,
        patterns    = [
            r"(switch|replac|chang|migrat).{0,30}(vendor|partner|platform|system|software|solution)",
            r"(vendor|partner|platform|system|software).{0,30}(switch|replac|chang|migrat|terminat|end)",
            r"(contract|agreement).{0,20}(terminat|end|expir|cancel).{0,20}(vendor|partner)",
            r"terminat.{0,30}(vendor|partner|software|platform|billing).{0,30}(contract|agreement)",  # reverse order
            r"terminat.{0,20}(vendor|partner).{0,20}contract",
            r"(select|chose|award|sign).{0,30}(new|different).{0,20}(vendor|partner|platform|provider)",
            r"(drop|discontinu|phase out).{0,20}(vendor|platform|system|software)",
            r"(lawsuit|litigation|dispute|sue[sd]?).{0,30}(vendor|partner|supplier|contractor)",
        ],
    ),

    # ── Rule 8: Financial Event ──────────────────────────────────────────────
    Rule(
        name        = "financial_event",
        signal_type = "financial_event",
        tier        = "worth_knowing",
        confidence  = 0.80,
        patterns    = [
            r"(operating|net|annual).{0,20}(loss|deficit|shortfall)",
            r"(budget|spending).{0,20}(cut|reduc|slash|trim)",
            r"(credit|bond|debt).{0,20}(downgrad|rating|watch)",
            r"(moody|fitch|s&p).{0,20}(downgrad|rating|outlook)",
            r"(financial|fiscal).{0,20}(struggl|challeng|difficult|pressure|crisis)",
            r"(revenue|income|earnings).{0,20}(declin|decreas|fell|drop|miss)",
            r"(cash flow|liquidity).{0,20}(concern|problem|issue|negative|tight)",
            r"annual.{0,10}report",
            r"10-[kq]\b",                        # SEC filings
        ],
        negative_patterns = [
            r"revenue cycle",                    # RCM context handled by other rules
        ],
    ),
]


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------

def _compile_patterns(patterns: list[str]) -> list[re.Pattern]:
    return [re.compile(p, re.IGNORECASE) for p in patterns]


# Pre-compile all patterns at import time (one-time cost)
_compiled_rules: list[tuple[Rule, list[re.Pattern], list[re.Pattern]]] = []
for _rule in RULES:
    _pos = _compile_patterns(_rule.patterns)
    _neg = _compile_patterns(_rule.negative_patterns)
    _compiled_rules.append((_rule, _pos, _neg))


def classify_with_rules(
    title: str,
    text: str = "",
    source_name: str = "",
) -> RulesEngineResult:
    """
    Run all rules against the combined title + text.

    Rules fire on first match in definition order (most specific → least).
    Returns RulesEngineResult with matched=True if any rule fires,
    or matched=False to signal that Claude should handle classification.

    Args:
        title:       Signal title / headline
        text:        Article body or excerpt (optional but improves accuracy)
        source_name: Publication name (optional, used for context)

    Returns:
        RulesEngineResult
    """
    combined = f"{title} {text}".lower()

    for rule, pos_patterns, neg_patterns in _compiled_rules:
        # Check negative guards first (cheap exit)
        if any(neg.search(combined) for neg in neg_patterns):
            continue

        # Check positive patterns
        hits = [p.pattern for p in pos_patterns if p.search(combined)]
        if hits:
            return RulesEngineResult(
                matched          = True,
                signal_type      = rule.signal_type,
                tier             = rule.tier,
                confidence       = rule.confidence,
                rule_name        = rule.name,
                matched_keywords = hits[:3],  # top 3 for logging/debugging
            )

    return RulesEngineResult(matched=False)


def get_rules_engine_stats() -> dict:
    """
    Returns metadata about the rules engine for the /status endpoint.
    """
    return {
        "rule_count":    len(RULES),
        "rules":         [r.name for r in RULES],
        "signal_types":  sorted(VALID_SIGNAL_TYPES),
        "valid_tiers":   sorted(VALID_TIERS),
    }
