"""
Task 4 — Slack DM test script.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/test_slack_dm.py

Requires SLACK_BOT_TOKEN and SLACK_USER_ID_DANIELLE in .env.
Sends a test DM to Danielle and prints the result.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_USER_ID_DANIELLE = os.environ.get("SLACK_USER_ID_DANIELLE", "")

if not SLACK_BOT_TOKEN or SLACK_BOT_TOKEN.startswith("xoxb-placeholder"):
    print("❌  SLACK_BOT_TOKEN not set — add the real token to .env first")
    sys.exit(1)

if not SLACK_USER_ID_DANIELLE or SLACK_USER_ID_DANIELLE.startswith("PLACEHOLDER"):
    print("❌  SLACK_USER_ID_DANIELLE not set — add your Slack User ID to .env")
    sys.exit(1)

# Bootstrap settings so the service can call get_settings()
os.environ.setdefault("SUPABASE_URL",         os.environ.get("SUPABASE_URL", "https://test.supabase.co"))
os.environ.setdefault("SUPABASE_KEY",         os.environ.get("SUPABASE_KEY", "test"))
os.environ.setdefault("SLACK_SIGNING_SECRET", os.environ.get("SLACK_SIGNING_SECRET", "test"))
os.environ.setdefault("ANTHROPIC_API_KEY",    os.environ.get("ANTHROPIC_API_KEY", "test"))
os.environ.setdefault("INTERNAL_API_KEY",     os.environ.get("INTERNAL_API_KEY", "test"))

from app.services.slack_service import send_dm, format_weekly_digest, send_urgent_alert

print("\n📡  Adonis — Slack DM test\n" + "─" * 40)

# ── Test 1: Plain DM ────────────────────────────────────────────────────────
print("\n1️⃣  Sending plain test DM to Danielle...")
try:
    result = send_dm(
        slack_user_id=SLACK_USER_ID_DANIELLE,
        text="👋 Adonis backend smoke test — plain DM working.",
    )
    print(f"   ✅  Sent! ts={result.get('ts')}")
except Exception as e:
    print(f"   ❌  Failed: {e}")
    sys.exit(1)

# ── Test 2: Digest format DM ────────────────────────────────────────────────
print("\n2️⃣  Sending formatted digest preview to Danielle...")
fake_signals = [
    {
        "hospital_name": "NewYork-Presbyterian",
        "title":         "CRO John Smith departs NYP to join competitor",
        "summary":       "Chief Revenue Officer John Smith has announced his departure after 5 years at NYP.",
        "tier":          "urgent",
        "signal_type":   "leadership_change",
        "source_name":   "Modern Healthcare",
        "source_url":    "https://modernhealthcare.com/example",
        "published_date": "2026-06-02",
    },
    {
        "hospital_name": "UMass Memorial",
        "title":         "UMass posts 14 RCM coordinator openings on LinkedIn",
        "summary":       "A spike in revenue cycle hiring suggests a major billing initiative underway.",
        "tier":          "worth_knowing",
        "signal_type":   "rcm_hiring_spike",
        "source_name":   "LinkedIn",
        "source_url":    "https://linkedin.com/jobs/example",
        "published_date": "2026-06-01",
    },
]

fake_ae = {"name": "Danielle", "id": SLACK_USER_ID_DANIELLE}
try:
    fallback, blocks = format_weekly_digest(
        ae_user=fake_ae,
        signals=fake_signals,
        week_label="June 2–6",
    )
    result = send_dm(
        slack_user_id=SLACK_USER_ID_DANIELLE,
        text=fallback,
        blocks=blocks,
    )
    print(f"   ✅  Digest preview sent! ts={result.get('ts')}")
except Exception as e:
    print(f"   ❌  Failed: {e}")
    sys.exit(1)

# ── Test 3: Urgent alert ─────────────────────────────────────────────────────
print("\n3️⃣  Sending urgent alert DM to Danielle...")
fake_signal = {
    "id":          "test-signal-001",
    "title":       "Ascension acquires regional health system — 8 hospitals joining network",
    "summary":     "Ascension Health has completed the acquisition of MidWest Regional Health, adding 8 hospitals.",
    "signal_type": "ma_acquisition",
    "source_name": "Wall Street Journal",
    "source_url":  "https://wsj.com/example",
}
try:
    result = send_urgent_alert(
        signal=fake_signal,
        hospital_name="Ascension",
        ae_slack_user_id=SLACK_USER_ID_DANIELLE,
    )
    print(f"   ✅  Urgent alert sent! ts={result.get('ts')}")
except Exception as e:
    print(f"   ❌  Failed: {e}")
    sys.exit(1)

print("\n✅  All 3 Slack tests passed — Task 4 complete.\n")
print("📌  Next: add real Slack User IDs for Michael, David, Jeff to .env")
