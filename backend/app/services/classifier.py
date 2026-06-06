"""
Claude Signal Classifier — Task 7 (Luminai Infer pattern).

classify_signal() orchestrates a two-stage pipeline:
  Stage 1: Deterministic rules engine (Task 5) — zero cost, <1ms
  Stage 2: Claude claude-sonnet-4-20250514 — only for ambiguous signals

Returns ClassificationResult with signal_type, tier, confidence_score,
title, summary, why_relevant, and classification_source.

Confidence thresholds:
  ≥ 0.70 → accepted as-is
  0.50–0.69 → accepted but flagged for human review (review_status=pending)
  < 0.50 → signal_type = "filtered_out", tier = "filtered_out"

Claude is called with:
  - system: expert healthcare revenue cycle analyst persona
  - user: structured article text + hospital context
  - JSON-mode-style instruction for deterministic output parsing
"""
from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass, field
from typing import Literal, Optional

import anthropic

from app.core.config import get_settings
from app.core.retry import with_retry
from app.services.rules_engine import classify_with_rules

logger = logging.getLogger(__name__)

# Model used for all Claude calls
CLAUDE_MODEL = "claude-sonnet-4-20250514"

# Confidence threshold below which we filter out the signal entirely
CONFIDENCE_FILTER_THRESHOLD = 0.50

# Valid values mirrored from schemas.py (avoids circular import)
VALID_SIGNAL_TYPES = frozenset({
    "leadership_change", "rcm_hiring_spike", "epic_go_live",
    "post_golive_friction", "ma_acquisition", "vendor_change",
    "vendor_dispute", "restructuring", "new_hospital_launch",
    "financial_event", "ai_adoption_outside_rcm", "automation_proof",
    "named_automation_owner", "thought_leadership", "filtered_out",
})
VALID_TIERS = frozenset({"urgent", "worth_knowing", "filtered_out"})

# Singleton Anthropic client
_anthropic_client: Optional[anthropic.Anthropic] = None


def get_anthropic_client() -> anthropic.Anthropic:
    global _anthropic_client
    if _anthropic_client is None:
        settings = get_settings()
        _anthropic_client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        logger.info("Anthropic client initialized")
    return _anthropic_client


# ---------------------------------------------------------------------------
# Result dataclass
# ---------------------------------------------------------------------------

@dataclass
class ClassificationResult:
    signal_type:           str
    tier:                  str
    confidence_score:      float
    title:                 str
    summary:               str
    why_relevant:          str
    classification_source: Literal["rules_engine", "claude_api", "error"]
    model_used:            Optional[str] = None
    tokens_used:           Optional[int] = None
    rule_name:             Optional[str] = None   # set when rules_engine fires

    def to_dict(self) -> dict:
        return {
            "signal_type":           self.signal_type,
            "tier":                  self.tier,
            "confidence_score":      self.confidence_score,
            "title":                 self.title,
            "summary":               self.summary,
            "why_relevant":          self.why_relevant,
            "classification_source": self.classification_source,
            "model_used":            self.model_used,
            "tokens_used":           self.tokens_used,
            "rule_name":             self.rule_name,
        }


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """You are an expert healthcare revenue cycle analyst for Adonis, \
an AI-powered account intelligence platform for RCM (Revenue Cycle Management) vendors.

Your job is to classify a hospital or health system news article and determine whether \
it represents a sales signal for RCM solutions.

Signal types and when they apply:
- leadership_change: C-suite or VP-level hire/departure in revenue-touching roles (CRO, CFO, CIO, VP Revenue)
- rcm_hiring_spike: Multiple RCM job postings indicating internal capacity gaps
- epic_go_live: EHR system go-live (Epic, Cerner, Meditech) — prime time for RCM support
- post_golive_friction: Billing problems, denial spikes, AR issues after EHR launch
- ma_acquisition: Hospital acquisition or merger — budget/vendor resets typically follow
- vendor_change: Switching or terminating a billing/RCM vendor
- vendor_dispute: Lawsuit or public dispute with a vendor
- restructuring: Layoffs, department closures, workforce reductions
- new_hospital_launch: New facility opening (expansion opportunity)
- financial_event: Operating loss, budget cuts, credit downgrade
- ai_adoption_outside_rcm: AI hiring or investment outside RCM (context signal)
- automation_proof: Evidence hospital already automates revenue processes
- named_automation_owner: Specific person named as leading automation/digital initiative
- thought_leadership: Executive publishing on RCM or digital health topics
- filtered_out: Not relevant to RCM sales (community events, unrelated news)

Tiers:
- urgent: Act this week — leadership change, EHR go-live, acquisition, friction, restructuring
- worth_knowing: Monitor — hiring spike, vendor change, financial event, thought leadership
- filtered_out: Not actionable

Return ONLY valid JSON, no markdown, no explanation:
{
  "signal_type": "<one of the signal types above>",
  "tier": "<urgent|worth_knowing|filtered_out>",
  "confidence_score": <0.0 to 1.0>,
  "title": "<concise 10-word headline>",
  "summary": "<2-3 sentence summary of what happened and why it matters for RCM>",
  "why_relevant": "<1-2 sentences: specific reason this is an RCM sales opportunity>"
}"""


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------

async def classify_signal(
    article_text: str,
    hospital_name: str,
    source_name: str = "",
    signal_type_hint: Optional[str] = None,
) -> ClassificationResult:
    """
    Classify a hospital news article as a sales signal.

    Stage 1 — Rules engine: fast, deterministic, zero cost.
    Stage 2 — Claude: only for articles the rules engine couldn't classify.

    Args:
        article_text:      Full article text or excerpt
        hospital_name:     Hospital/health system name for context
        source_name:       Publication (e.g. "Modern Healthcare", "LinkedIn")
        signal_type_hint:  Optional hint from caller (e.g. from Michael's matched_topics)

    Returns:
        ClassificationResult
    """
    # ── Stage 1: Rules engine ────────────────────────────────────────────────
    rules_result = classify_with_rules(
        title=article_text[:200],   # first 200 chars as "title"
        text=article_text,
        source_name=source_name,
    )

    if rules_result.matched:
        logger.info(
            f"Rules engine classified: {rules_result.signal_type} "
            f"(rule={rules_result.rule_name}, confidence={rules_result.confidence})"
        )
        # Generate stub title/summary since rules engine doesn't produce text
        short_text = article_text[:150].strip()
        return ClassificationResult(
            signal_type           = rules_result.signal_type,
            tier                  = rules_result.tier,
            confidence_score      = rules_result.confidence,
            title                 = short_text[:80] if short_text else f"{hospital_name} signal",
            summary               = article_text[:300].strip() or "Signal detected via rules engine.",
            why_relevant          = f"Deterministic match: {rules_result.rule_name.replace('_', ' ').title()} pattern.",
            classification_source = "rules_engine",
            rule_name             = rules_result.rule_name,
        )

    # ── Stage 2: Claude ──────────────────────────────────────────────────────
    logger.info(f"Rules engine: no match — escalating to Claude for '{hospital_name}'")
    try:
        return await _classify_with_claude(
            article_text    = article_text,
            hospital_name   = hospital_name,
            source_name     = source_name,
            signal_type_hint= signal_type_hint,
        )
    except anthropic.APIStatusError as e:
        return _error_result(f"Claude API error: {e.status_code}")
    except anthropic.APIConnectionError:
        return _error_result("Claude connection error")
    except Exception as e:
        return _error_result(str(e))


@with_retry(max_attempts=3, base_delay=2.0)
async def _classify_with_claude(
    article_text: str,
    hospital_name: str,
    source_name: str,
    signal_type_hint: Optional[str],
) -> ClassificationResult:
    """Call Claude and parse the JSON classification response."""

    hint_line = (
        f"\nSignal type hint from source pipeline: {signal_type_hint}"
        if signal_type_hint and signal_type_hint != "filtered_out"
        else ""
    )

    user_message = (
        f"Hospital: {hospital_name}\n"
        f"Source: {source_name or 'Unknown'}"
        f"{hint_line}\n\n"
        f"Article text:\n{article_text[:4000]}"  # stay within token budget
    )

    try:
        client = get_anthropic_client()
        response = client.messages.create(
            model      = CLAUDE_MODEL,
            max_tokens = 512,
            system     = SYSTEM_PROMPT,
            messages   = [{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text.strip()
        tokens   = response.usage.input_tokens + response.usage.output_tokens

        logger.info(
            f"Claude classification complete | "
            f"hospital={hospital_name} tokens={tokens}"
        )

        parsed = _parse_claude_response(raw_text)

        # Apply confidence filter
        if parsed["confidence_score"] < CONFIDENCE_FILTER_THRESHOLD:
            logger.info(
                f"Low confidence ({parsed['confidence_score']:.2f}) — filtering out signal"
            )
            return ClassificationResult(
                signal_type           = "filtered_out",
                tier                  = "filtered_out",
                confidence_score      = parsed["confidence_score"],
                title                 = parsed.get("title", "Low-confidence signal"),
                summary               = parsed.get("summary", ""),
                why_relevant          = "Filtered: confidence below threshold.",
                classification_source = "claude_api",
                model_used            = CLAUDE_MODEL,
                tokens_used           = tokens,
            )

        return ClassificationResult(
            signal_type           = parsed["signal_type"],
            tier                  = parsed["tier"],
            confidence_score      = parsed["confidence_score"],
            title                 = parsed.get("title", "")[:80],
            summary               = parsed.get("summary", "")[:1000],
            why_relevant          = parsed.get("why_relevant", ""),
            classification_source = "claude_api",
            model_used            = CLAUDE_MODEL,
            tokens_used           = tokens,
        )

    except anthropic.APIStatusError as e:
        logger.error(f"Claude API error: {e.status_code} — {e.message}")
        raise
    except anthropic.APIConnectionError as e:
        logger.error(f"Claude connection error: {e}")
        raise
    except (KeyError, ValueError, json.JSONDecodeError) as e:
        logger.error(f"Claude response parse error: {e}")
        return _error_result("Claude response parse error")
    except Exception as e:
        logger.error(f"Unexpected classifier error: {e}")
        raise


def _parse_claude_response(raw_text: str) -> dict:
    """
    Extract and validate JSON from Claude's response.
    Handles cases where Claude wraps JSON in markdown code fences.
    """
    # Strip markdown code fences if present
    text = raw_text
    fence_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if fence_match:
        text = fence_match.group(1)
    else:
        # Try to extract bare JSON object
        json_match = re.search(r"\{.*\}", text, re.DOTALL)
        if json_match:
            text = json_match.group(0)

    data = json.loads(text)

    # Validate and normalise fields
    signal_type = data.get("signal_type", "filtered_out")
    if signal_type not in VALID_SIGNAL_TYPES:
        logger.warning(f"Claude returned unknown signal_type '{signal_type}' — using filtered_out")
        signal_type = "filtered_out"

    tier = data.get("tier", "filtered_out")
    if tier not in VALID_TIERS:
        logger.warning(f"Claude returned unknown tier '{tier}' — using filtered_out")
        tier = "filtered_out"

    confidence = float(data.get("confidence_score", 0.0))
    confidence = max(0.0, min(1.0, confidence))  # clamp to [0, 1]

    return {
        "signal_type":      signal_type,
        "tier":             tier,
        "confidence_score": confidence,
        "title":            str(data.get("title", ""))[:80],
        "summary":          str(data.get("summary", ""))[:1000],
        "why_relevant":     str(data.get("why_relevant", "")),
    }


def _error_result(reason: str) -> ClassificationResult:
    """Return a safe fallback result on any classifier failure."""
    return ClassificationResult(
        signal_type           = "filtered_out",
        tier                  = "filtered_out",
        confidence_score      = 0.0,
        title                 = "Classification error",
        summary               = reason,
        why_relevant          = "",
        classification_source = "error",
    )
