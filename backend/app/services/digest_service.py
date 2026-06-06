"""
Digest Service — Task 8 (Luminai Human-in-the-Loop & Closed-Loop patterns).

Manages compiling territory signals, formatting Slack Block Kit digests,
sending the DMs (or simulating them for placeholders), and logging history.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Optional
import uuid

from app.core.config import get_settings
from app.core.database import get_supabase
from app.services.slack_service import format_weekly_digest, send_dm

logger = logging.getLogger(__name__)


def format_week_range(start: date, end: date) -> str:
    """Format week label independently of platform (e.g., 'June 8–14')."""
    start_month = start.strftime("%B")
    end_month = end.strftime("%B")
    if start_month == end_month:
        return f"{start_month} {start.day}–{end.day}"
    else:
        return f"{start_month} {start.day} – {end_month} {end.day}"


def resolve_slack_user_id(db_user: dict) -> Optional[str]:
    """
    Resolves an AE's Slack User ID.
    If the database has a placeholder, attempts to resolve from the configured
    env/settings values. Returns None if it is unresolved or remains a placeholder.
    """
    slack_id = db_user.get("slack_user_id")
    if not slack_id:
        return None

    if slack_id.startswith("PLACEHOLDER"):
        settings = get_settings()
        name_lower = db_user.get("name", "").lower()
        
        if "danielle" in name_lower:
            resolved = settings.slack_user_id_danielle
        elif "michael" in name_lower:
            resolved = settings.slack_user_id_michael
        elif "david" in name_lower:
            resolved = settings.slack_user_id_david
        elif "jeff" in name_lower:
            resolved = settings.slack_user_id_jeff
        else:
            resolved = slack_id

        if resolved and resolved.startswith("PLACEHOLDER"):
            return None
        return resolved

    return slack_id


async def get_digest_signals_for_ae(ae_id: str) -> list[dict]:
    """
    Fetch all signals for the given AE's territory that are ready for digest.
    
    Ready signals:
      - Belong to a hospital assigned to the AE
      - included_in_digest = False
      - tier in ('urgent', 'worth_knowing')
      - review_status in (None, 'approved') (not pending, not dismissed)
    """
    supabase = get_supabase()

    # 1. Fetch assigned hospital IDs
    assignments_res = (
        supabase.table("hospital_ae_assignments")
        .select("hospital_id")
        .eq("ae_id", ae_id)
        .execute()
    )
    hospital_ids = [a["hospital_id"] for a in assignments_res.data]
    if not hospital_ids:
        return []

    # 2. Fetch un-digested signals for these hospitals, joining hospital name
    signals_res = (
        supabase.table("signals")
        .select("*, hospitals(name)")
        .in_("hospital_id", hospital_ids)
        .eq("included_in_digest", False)
        .execute()
    )

    all_signals = signals_res.data
    valid_signals = []

    # 3. Filter and preprocess in Python for simplicity and robustness
    for sig in all_signals:
        if sig.get("tier") not in ("urgent", "worth_knowing"):
            continue
        # Exclude signals still pending review or dismissed
        if sig.get("review_status") not in (None, "approved"):
            continue

        # Map joined hospitals.name -> hospital_name
        if "hospitals" in sig and isinstance(sig["hospitals"], dict):
            sig["hospital_name"] = sig["hospitals"].get("name")
        if not sig.get("hospital_name"):
            sig["hospital_name"] = sig.get("hospital_id", "Unknown Hospital")

        valid_signals.append(sig)

    return valid_signals


async def send_weekly_digest_to_all_aes() -> dict:
    """
    Main job loop for Task 8.
    
    1. Fetches all non-admin AE users
    2. Compiles territory signals
    3. Formats Block Kit and sends Slack DMs (or logs if placeholders)
    4. Records digests in the DB and marks signals as digested
    """
    supabase = get_supabase()
    
    # 1. Fetch non-admin AEs
    aes_res = (
        supabase.table("ae_users")
        .select("*")
        .eq("is_admin", False)
        .execute()
    )
    aes = aes_res.data

    summary = {
        "sent_count": 0,
        "signals_digested": 0,
        "digests_created": []
    }

    if not aes:
        logger.info("No AEs found in the system. Skipping digest send.")
        return summary

    today = date.today()
    week_start = today - timedelta(days=today.weekday())  # Current Monday
    week_end = week_start + timedelta(days=6)              # Current Sunday
    week_label = format_week_range(week_start, week_end)

    for ae in aes:
        ae_id = ae["id"]
        ae_name = ae["name"]
        
        # 2. Compile signals
        signals = await get_digest_signals_for_ae(ae_id)
        if not signals:
            logger.info(f"No digest-ready signals for {ae_name} (AE ID: {ae_id})")
            continue

        # Generate digest_id upfront to include in the UTM tracking URL
        digest_id = str(uuid.uuid4())

        # 3. Format and send
        fallback_text, blocks = format_weekly_digest(
            ae_user=ae,
            signals=signals,
            week_label=week_label,
            digest_id=digest_id
        )

        slack_user_id = resolve_slack_user_id(ae)
        slack_message_ts = None
        sent_real_slack = False

        if slack_user_id:
            try:
                slack_res = send_dm(
                    slack_user_id=slack_user_id,
                    text=fallback_text,
                    blocks=blocks
                )
                slack_message_ts = slack_res.get("ts")
                sent_real_slack = True
                logger.info(f"Weekly digest DM sent to {ae_name} ({slack_user_id})")
            except Exception as e:
                logger.error(f"Failed to send Slack DM to {ae_name}: {e}")
        
        # If no real slack_user_id could be resolved, simulate for testing/dev log
        if not sent_real_slack:
            slack_message_ts = f"simulated-ts-{uuid.uuid4()}"
            logger.warning(
                f"Slack ID placeholder for {ae_name} — simulated send and logged to DB"
            )

        # 4. Save digest log record in the database
        digest_record = {
            "id":               digest_id,
            "ae_id":            ae_id,
            "sent_at":          datetime.now(timezone.utc).isoformat(),
            "slack_message_ts": slack_message_ts,
            "week_start":       week_start.isoformat(),
            "week_end":         week_end.isoformat(),
        }
        
        try:
            digest_insert_res = (
                supabase.table("digests")
                .insert(digest_record)
                .execute()
            )
            created_digest = digest_insert_res.data[0]
            logger.info(f"Logged digest record {created_digest['id']} for {ae_name}")
        except Exception as e:
            logger.error(f"Failed to insert digest log for {ae_name}: {e}")
            continue

        # 5. Mark signals as included in digest
        signal_ids = [s["id"] for s in signals]
        try:
            supabase.table("signals").update({"included_in_digest": True}).in_("id", signal_ids).execute()
            logger.info(f"Marked {len(signal_ids)} signals as digested for {ae_name}")
        except Exception as e:
            logger.error(f"Failed to update signals as digested for {ae_name}: {e}")
            # Non-blocking, continue

        summary["sent_count"] += 1
        summary["signals_digested"] += len(signals)
        summary["digests_created"].append({
            "digest_id":        created_digest.get("id"),
            "ae_name":          ae_name,
            "ae_id":            ae_id,
            "signals_count":    len(signals),
            "sent_real_slack":  sent_real_slack,
            "slack_message_ts": slack_message_ts
        })

    logger.info(
        f"Digest run summary: sent={summary['sent_count']} signals={summary['signals_digested']}"
    )
    return summary


async def check_review_queue_and_notify() -> int:
    """
    Check if the review queue has pending signals. If it does, notify Danielle.
    
    Implements Human-in-the-Loop guard notification.
    """
    supabase = get_supabase()
    try:
        pending_res = (
            supabase.table("signals")
            .select("id", count="exact")
            .eq("review_status", "pending")
            .execute()
        )
        pending_count = pending_res.count or 0
    except Exception as e:
        logger.error(f"Failed to check pending count: {e}")
        pending_count = 0

    if pending_count > 0:
        logger.warning(f"Digest send blocked by {pending_count} pending review signals")
        
        # Locate Danielle admin user slack id
        try:
            admin_res = (
                supabase.table("ae_users")
                .select("*")
                .eq("is_admin", True)
                .execute()
            )
            admin_users = admin_res.data
            if admin_users:
                danielle_id = resolve_slack_user_id(admin_users[0])
                if danielle_id:
                    send_dm(
                        slack_user_id=danielle_id,
                        text=(
                            f"⚠️ Weekly digest is BLOCKED — {pending_count} signal"
                            f"{'s' if pending_count != 1 else ''} need your review before the digest can send.\n"
                            f"Please review at the dashboard."
                        )
                    )
                    logger.info(f"Notified Danielle of {pending_count} pending signals")
        except Exception as e:
            logger.error(f"Failed to send blocked digest notification to Danielle: {e}")

    return pending_count
