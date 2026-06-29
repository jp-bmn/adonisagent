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
SLACK_USER_ID_MICHAEL = os.environ.get("SLACK_USER_ID_MICHAEL", "")
SLACK_USER_ID_DAVID = os.environ.get("SLACK_USER_ID_DAVID", "")
SLACK_USER_ID_JEFF = os.environ.get("SLACK_USER_ID_JEFF", "")

if not SLACK_BOT_TOKEN or SLACK_BOT_TOKEN.startswith("xoxb-placeholder"):
    print("❌  SLACK_BOT_TOKEN not set — add the real token to .env first")
    sys.exit(1)

team = {
    "Danielle": SLACK_USER_ID_DANIELLE,
    "Michael": SLACK_USER_ID_MICHAEL,
    "David": SLACK_USER_ID_DAVID,
    "Jeff": SLACK_USER_ID_JEFF,
}

for name, user_id in team.items():
    if not user_id or user_id.startswith("PLACEHOLDER"):
        print(f"⚠️  Skipping {name} — ID not set yet.")
        continue

# Bootstrap settings so the service can call get_settings()
os.environ.setdefault("SUPABASE_URL",         os.environ.get("SUPABASE_URL", "https://test.supabase.co"))
os.environ.setdefault("SUPABASE_KEY",         os.environ.get("SUPABASE_KEY", "test"))
os.environ.setdefault("SLACK_SIGNING_SECRET", os.environ.get("SLACK_SIGNING_SECRET", "test"))
os.environ.setdefault("ANTHROPIC_API_KEY",    os.environ.get("ANTHROPIC_API_KEY", "test"))
os.environ.setdefault("INTERNAL_API_KEY",     os.environ.get("INTERNAL_API_KEY", "test"))

# Add the backend directory to sys.path so it can find the 'app' module
import sys
from pathlib import Path
backend_dir = str(Path(__file__).resolve().parent.parent)
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

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

print("\n✅  All 3 Slack tests passed for Danielle.\n")

print("4️⃣  Pinging the rest of the team...")
for name, user_id in team.items():
    if name == "Danielle":
        continue
    try:
        result = send_dm(
            slack_user_id=user_id,
            text=f"👋 Adonis backend smoke test — hello {name}!",
        )
        print(f"   ✅  Sent to {name}! ts={result.get('ts')}")
    except Exception as e:
        print(f"   ❌  Failed sending to {name}: {e}")

print("\n🎉  Slack integration is fully verified!\n")
