"""
Alert service — Task 14 implementation.
Provides immediate Slack alerts for urgent signals with same-day deduplication.
"""
from __future__ import annotations
import logging
from datetime import datetime, timezone
from app.core.database import get_supabase
from app.services.slack_service import send_urgent_alert, send_dm
from app.core.config import get_settings

logger = logging.getLogger(__name__)


def send_urgent_alert_for_signal(signal_id: str) -> bool:
    """
    Sends an immediate Slack alert to the assigned AE(s) for a hospital
    when a tier='urgent' signal is detected.
    
    Implements:
    - Same-day deduplication (only one alert per hospital per day).
    - Notification to Danielle (admin).
    - Updating of the signal's urgent_sent column to true.
    """
    supabase = get_supabase()

    # 1. Fetch signal and join hospital details
    try:
        res = (
            supabase.table("signals")
            .select("*, hospitals(name)")
            .eq("id", signal_id)
            .execute()
        )
        if not res.data:
            logger.warning(f"Signal {signal_id} not found. Skipping alert.")
            return False
        signal = res.data[0]
    except Exception as e:
        logger.error(f"Failed to fetch signal {signal_id}: {e}")
        return False

    hospital_id = signal.get("hospital_id")
    hospital_name = (signal.get("hospitals") or {}).get("name") or "Unknown Hospital"
    tier = signal.get("tier")

    if tier != "urgent":
        logger.info(f"Signal {signal_id} tier is '{tier}', not 'urgent'. Skipping alert.")
        return False

    # 2. Same-day deduplication check (urgent_sent=true for same hospital today)
    try:
        start_of_today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
        dedup_res = (
            supabase.table("signals")
            .select("id")
            .eq("hospital_id", hospital_id)
            .eq("urgent_sent", True)
            .gte("created_at", start_of_today)
            .execute()
        )
        if dedup_res.data:
            logger.info(f"Urgent alert for hospital '{hospital_name}' already sent today. Skipping.")
            return False
    except Exception as e:
        logger.error(f"Failed during same-day deduplication check: {e}")
        # Proceed conservatively if check fails

    # 3. Fetch AEs assigned to this hospital
    try:
        assignments_res = (
            supabase.table("hospital_ae_assignments")
            .select("ae_id")
            .eq("hospital_id", hospital_id)
            .execute()
        )
        ae_ids = [a["ae_id"] for a in (assignments_res.data or [])]
    except Exception as e:
        logger.error(f"Failed to fetch AE assignments: {e}")
        ae_ids = []

    # 4. Fetch AE details
    ae_users = []
    if ae_ids:
        try:
            ae_users_res = (
                supabase.table("ae_users")
                .select("name, slack_user_id")
                .in_("id", ae_ids)
                .execute()
            )
            ae_users = ae_users_res.data or []
        except Exception as e:
            logger.error(f"Failed to fetch AE details: {e}")

    # 5. Send Slack DM to assigned AEs
    alert_sent_to_ae = False
    for ae in ae_users:
        slack_id = ae.get("slack_user_id")
        if slack_id and not slack_id.startswith("PLACEHOLDER"):
            try:
                send_urgent_alert(
                    signal=signal,
                    hospital_name=hospital_name,
                    ae_slack_user_id=slack_id,
                )
                alert_sent_to_ae = True
            except Exception as e:
                logger.error(f"Failed to send Slack DM to AE {slack_id}: {e}")

    # 6. Notify Danielle (Admin)
    settings = get_settings()
    danielle_id = settings.slack_user_id_danielle
    if danielle_id and not danielle_id.startswith("PLACEHOLDER"):
        try:
            ae_names = ", ".join(ae.get("name", "Unknown") for ae in ae_users) if ae_users else "None"
            msg = (
                f"🚨 *Urgent Signal Notification* 🚨\n"
                f"An urgent signal was detected for *{hospital_name}*:\n"
                f"*{signal.get('title')}*\n"
                f"AEs assigned: {ae_names}"
            )
            send_dm(slack_user_id=danielle_id, text=msg)
        except Exception as e:
            logger.error(f"Failed to notify Danielle: {e}")

    # 7. Update database to mark urgent alert as sent
    try:
        supabase.table("signals").update({"urgent_sent": True}).eq("id", signal_id).execute()
    except Exception as e:
        logger.error(f"Failed to update urgent_sent column for signal {signal_id}: {e}")

    return True
