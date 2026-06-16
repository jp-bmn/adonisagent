"""
Database hygiene script to re-classify existing signals using the Claude classifier
and sanitize incorrect or misclassified signal types/tiers.
"""
import os
import sys
import asyncio
from dotenv import load_dotenv

# Load .env file
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY or not ANTHROPIC_API_KEY:
    print("❌  SUPABASE_URL, SUPABASE_KEY, and ANTHROPIC_API_KEY must be set in .env")
    sys.exit(1)

# Bootstrap paths so we can import app package modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from supabase import create_client
from app.services.classifier import classify_signal

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


async def main():
    print("🔍  Fetching signals from database...")
    try:
        signals_res = supabase.table("signals").select(
            "id, title, summary, signal_type, tier, source_name, hospital_id, hospitals(name)"
        ).execute()
    except Exception as e:
        print(f"❌  Failed to fetch signals: {e}")
        return

    signals = signals_res.data or []
    print(f"Total signals found in DB: {len(signals)}")

    updated_count = 0
    deleted_count = 0

    for idx, sig in enumerate(signals):
        sig_id = sig["id"]
        title = sig["title"]
        summary = sig.get("summary") or ""
        current_type = sig["signal_type"]
        current_tier = sig["tier"]
        source_name = sig.get("source_name") or ""
        hospitals_info = sig.get("hospitals") or {}
        hospital_name = hospitals_info.get("name", "Unknown Hospital")

        print(f"\n[{idx+1}/{len(signals)}] Evaluating: '{title}' ({hospital_name})")
        print(f"  Current Type: {current_type} | Tier: {current_tier}")

        # Combine title and summary for classification
        article_text = f"{title}\n\n{summary}"

        try:
            # Call Claude classifier
            res = await classify_signal(
                article_text=article_text,
                hospital_name=hospital_name,
                source_name=source_name
            )

            new_type = res.signal_type
            new_tier = res.tier
            new_confidence = res.confidence_score

            print(f"  Classified as: {new_type} | Tier: {new_tier} | Conf: {new_confidence:.2f}")

            if new_type == "filtered_out":
                print(f"  🚨  Re-classified as filtered_out. DELETING signal {sig_id}...")
                supabase.table("signals").delete().eq("id", sig_id).execute()
                deleted_count += 1
            elif new_type != current_type or new_tier != current_tier:
                print(f"  🔄  Updating signal {sig_id} to type={new_type}, tier={new_tier}...")
                supabase.table("signals").update({
                    "signal_type": new_type,
                    "tier": new_tier,
                    "confidence_score": new_confidence
                }).eq("id", sig_id).execute()
                updated_count += 1
            else:
                print("  ✅  Classification matches. No update needed.")

        except Exception as e:
            print(f"  ❌  Error classifying signal: {e}")

    print("\n" + "="*50)
    print(f"Cleanup complete. Deleted: {deleted_count} | Updated: {updated_count}")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())
