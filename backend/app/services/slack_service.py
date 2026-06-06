"""
Slack service — Task 4 full implementation.

Provides:
  send_dm()               — raw DM with optional Block Kit payload
  format_weekly_digest()  — Block Kit digest for one AE's territory
  send_urgent_alert()     — immediate DM for tier=urgent signals
  SlackRateLimiter        — deque-based 10 req/min guard

All calls go through _send_with_rate_limit() which respects the
Slack Tier 1 API limit and retries on rate-limit (HTTP 429) responses.
"""
from __future__ import annotations
import logging
import time
from collections import deque
from typing import Optional

from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from app.core.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Rate limiter  — Slack Tier 1: ~1 req/sec (60/min). We cap at 10/min to be
# conservative and avoid disrupting other Slack API callers in the workspace.
# ---------------------------------------------------------------------------

MAX_REQUESTS_PER_MINUTE = 10


class SlackRateLimiter:
    """Sliding-window rate limiter using a deque of request timestamps."""

    def __init__(self, max_per_minute: int = MAX_REQUESTS_PER_MINUTE):
        self._max = max_per_minute
        self._timestamps: deque[float] = deque()

    def wait_if_needed(self) -> None:
        now = time.monotonic()
        window_start = now - 60.0

        # Drop timestamps older than the window
        while self._timestamps and self._timestamps[0] < window_start:
            self._timestamps.popleft()

        if len(self._timestamps) >= self._max:
            # Must wait until the oldest request leaves the window
            sleep_for = 60.0 - (now - self._timestamps[0]) + 0.1
            if sleep_for > 0:
                logger.info(f"Slack rate limit — sleeping {sleep_for:.1f}s")
                time.sleep(sleep_for)

        self._timestamps.append(time.monotonic())


_rate_limiter = SlackRateLimiter()


# ---------------------------------------------------------------------------
# Slack client singleton
# ---------------------------------------------------------------------------

_client: Optional[WebClient] = None


def get_slack_client() -> WebClient:
    global _client
    if _client is None:
        settings = get_settings()
        _client = WebClient(token=settings.slack_bot_token)
        logger.info("Slack WebClient initialized")
    return _client


# ---------------------------------------------------------------------------
# Core send helper
# ---------------------------------------------------------------------------

def _send_with_rate_limit(
    channel: str,
    text: str,
    blocks: Optional[list] = None,
    max_retries: int = 3,
) -> dict:
    """
    Rate-limited Slack message sender. Retries up to max_retries times
    on HTTP 429 (rate_limited) using the retry_after header.
    Returns the full Slack API response dict on success.
    Raises SlackApiError on non-retryable failures.
    """
    client = get_slack_client()

    for attempt in range(1, max_retries + 1):
        _rate_limiter.wait_if_needed()
        try:
            kwargs: dict = {"channel": channel, "text": text}
            if blocks:
                kwargs["blocks"] = blocks
            response = client.chat_postMessage(**kwargs)
            logger.info(f"Slack DM sent → channel={channel} ts={response['ts']}")
            return dict(response.data)
        except SlackApiError as e:
            if e.response["error"] == "ratelimited":
                retry_after = int(e.response.headers.get("Retry-After", 10))
                logger.warning(
                    f"Slack 429 ratelimited — waiting {retry_after}s "
                    f"(attempt {attempt}/{max_retries})"
                )
                time.sleep(retry_after + 1)
            else:
                logger.error(f"Slack API error: {e.response['error']} → channel={channel}")
                raise
    raise SlackApiError(
        message=f"Failed to send Slack message after {max_retries} retries",
        response={"error": "max_retries_exceeded"},
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def send_dm(
    slack_user_id: str,
    text: str,
    blocks: Optional[list] = None,
) -> dict:
    """
    Send a direct message to a Slack user by their User ID.
    Uses chat.postMessage with channel=<user_id> which opens a DM automatically.

    Args:
        slack_user_id: Slack user ID (e.g. "U0123ABCDEF")
        text:          Fallback plain text (shown in notifications + screen readers)
        blocks:        Optional Block Kit payload for rich formatting

    Returns:
        Slack API response dict with "ts" (message timestamp) on success
    """
    logger.info(f"send_dm → user={slack_user_id}")
    return _send_with_rate_limit(channel=slack_user_id, text=text, blocks=blocks)


def format_weekly_digest(
    ae_user: dict,
    signals: list[dict],
    week_label: str = "",
    dashboard_url: Optional[str] = None,
    digest_id: Optional[str] = None,
) -> tuple[str, list]:
    """
    Formats a weekly digest as Slack Block Kit.

    Args:
        ae_user:       AE user dict (keys: name, id)
        signals:       List of signal dicts from Supabase
        week_label:    Human-readable week label e.g. "June 2–6"
        dashboard_url: Link to the dashboard (falls back to settings)
        digest_id:     Optional UUID of the digest for tracking

    Returns:
        Tuple of (fallback_text, blocks) for use with send_dm()
    """
    settings = get_settings()
    url = dashboard_url or settings.dashboard_url

    ae_id = ae_user.get("id")
    if digest_id and ae_id:
        separator = "&" if "?" in url else "?"
        url = f"{url}{separator}digest_id={digest_id}&ae_id={ae_id}&utm_source=slack&utm_medium=digest"

    # Separate by tier
    urgent     = [s for s in signals if s.get("tier") == "urgent"]
    worth_knowing = [s for s in signals if s.get("tier") == "worth_knowing"]

    ae_name = ae_user.get("name", "there")
    signal_count = len(signals)
    week_str = f" — Week of {week_label}" if week_label else ""
    fallback_text = (
        f"Adonis Intel Digest{week_str}: "
        f"{signal_count} signal{'s' if signal_count != 1 else ''} "
        f"for {ae_name}'s territory"
    )

    blocks: list = []

    # ── Header ──────────────────────────────────────────────────────────────
    blocks.append({
        "type": "header",
        "text": {
            "type": "plain_text",
            "text": f"🏥 Adonis Intel Digest{week_str}",
            "emoji": True,
        },
    })
    blocks.append({
        "type": "section",
        "text": {
            "type": "mrkdwn",
            "text": (
                f"Hey {ae_name} 👋 Here's what happened in your territory this week.\n"
                f"*{signal_count} signal{'s' if signal_count != 1 else ''}* — "
                f"{len(urgent)} urgent, {len(worth_knowing)} worth knowing."
            ),
        },
    })
    blocks.append({"type": "divider"})

    # ── Urgent signals ───────────────────────────────────────────────────────
    if urgent:
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*🚨 Urgent — Act This Week*"},
        })
        for sig in urgent:
            blocks.append(_signal_block(sig))

    # ── Worth knowing ────────────────────────────────────────────────────────
    if worth_knowing:
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "section",
            "text": {"type": "mrkdwn", "text": "*📌 Worth Knowing*"},
        })
        for sig in worth_knowing:
            blocks.append(_signal_block(sig))

    # ── Footer ───────────────────────────────────────────────────────────────
    blocks.append({"type": "divider"})
    blocks.append({
        "type": "actions",
        "elements": [
            {
                "type": "button",
                "text": {"type": "plain_text", "text": "View Dashboard", "emoji": True},
                "url": url,
                "style": "primary",
            }
        ],
    })
    blocks.append({
        "type": "context",
        "elements": [
            {
                "type": "mrkdwn",
                "text": "_Adonis Account Intelligence · Automated intel from hospital news_",
            }
        ],
    })

    return fallback_text, blocks


def _signal_block(signal: dict) -> dict:
    """Renders one signal as a Slack section block."""
    hospital_name = signal.get("hospital_name") or signal.get("hospital_id", "Unknown Hospital")
    title         = signal.get("title") or "Untitled signal"
    summary       = signal.get("summary") or ""
    source_name   = signal.get("source_name") or ""
    source_url    = signal.get("source_url") or ""
    pub_date      = signal.get("published_date") or ""

    # Build the text
    lines = [f"*{hospital_name}* · _{title}_"]
    if summary:
        # Truncate long summaries
        short = summary[:200] + "…" if len(summary) > 200 else summary
        lines.append(short)

    meta_parts = []
    if source_name and source_url:
        meta_parts.append(f"<{source_url}|{source_name}>")
    elif source_url:
        meta_parts.append(f"<{source_url}|Read more>")
    elif source_name:
        meta_parts.append(source_name)
    if pub_date:
        meta_parts.append(pub_date)
    if meta_parts:
        lines.append("_" + " · ".join(meta_parts) + "_")

    return {
        "type": "section",
        "text": {"type": "mrkdwn", "text": "\n".join(lines)},
    }


def send_urgent_alert(
    signal: dict,
    hospital_name: str,
    ae_slack_user_id: str,
) -> dict:
    """
    Sends an immediate Slack DM when a tier=urgent signal is stored.
    Called via FastAPI BackgroundTasks (Task 14) or directly.

    Implements the Luminai Escalate pattern:
    - Fires immediately, not waiting for the Monday digest
    - Includes source link and a call to action
    - Same-day deduplication is handled by the caller (Task 14 / alert_service)

    Args:
        signal:            Signal dict from Supabase
        hospital_name:     Human-readable hospital name
        ae_slack_user_id:  Slack user ID of the responsible AE

    Returns:
        Slack API response dict
    """
    title      = signal.get("title", "Urgent signal detected")
    summary    = signal.get("summary", "")
    source_url = signal.get("source_url", "")
    source_name = signal.get("source_name", "")
    signal_type = signal.get("signal_type", "").replace("_", " ").title()

    fallback = f"🚨 Urgent alert — {hospital_name}: {title}"

    source_line = ""
    if source_url and source_name:
        source_line = f"\n📰 <{source_url}|{source_name}>"
    elif source_url:
        source_line = f"\n📰 <{source_url}|Read article>"

    blocks = [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": f"🚨 Urgent Signal — {hospital_name}",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    f"*{title}*\n"
                    f"_{signal_type}_\n"
                    + (f"\n{summary}" if summary else "")
                    + source_line
                ),
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "_This is an automated urgent alert from Adonis Account Intelligence_",
                }
            ],
        },
    ]

    logger.info(
        f"send_urgent_alert → user={ae_slack_user_id} "
        f"hospital={hospital_name} signal_id={signal.get('id')}"
    )
    return send_dm(slack_user_id=ae_slack_user_id, text=fallback, blocks=blocks)
