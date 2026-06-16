"""
Database hygiene script to scan for and delete signals that are misattributed
to hospitals they do not mention.
"""
import os
import sys
from dotenv import load_dotenv

# Load .env file from directory root
load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌  SUPABASE_URL and SUPABASE_KEY must be set in .env")
    sys.exit(1)

from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_KEY)


def _hospital_aliases(hospital: str) -> tuple[str, ...]:
    mapping = {
        "newyork-presbyterian": (
            "newyork-presbyterian",
            "new york-presbyterian",
            "new york presbyterian",
            "nyp",
        ),
        "new york-presbyterian": (
            "newyork-presbyterian",
            "new york-presbyterian",
            "new york presbyterian",
            "nyp",
        ),
        "umass memorial": (
            "umass memorial",
            "umass",
            "u mass memorial",
        ),
        "ascension": (
            "ascension",
            "ascension health",
        ),
        "university of arkansas": (
            "university of arkansas",
            "uams",
            "uams health",
            "university of arkansas for medical sciences",
        ),
        "university of arkansas medical sciences": (
            "university of arkansas",
            "uams",
            "uams health",
            "university of arkansas for medical sciences",
        ),
        "university of arkansas for medical sciences": (
            "university of arkansas",
            "uams",
            "uams health",
            "university of arkansas for medical sciences",
        ),
        "commonspirit": (
            "commonspirit",
            "commonspirit health",
            "chi",
            "catholic health initiatives",
            "dignity health",
        ),
        "commonspirit health": (
            "commonspirit",
            "commonspirit health",
            "chi",
            "catholic health initiatives",
            "dignity health",
        ),
        "jefferson health": (
            "jefferson health",
            "jefferson",
            "jeff",
            "thomas jefferson university",
            "thomas jefferson university hospitals",
        ),
        "jefferson": (
            "jefferson health",
            "jefferson",
            "jeff",
            "thomas jefferson university",
            "thomas jefferson university hospitals",
        ),
    }
    key = hospital.lower().strip()
    return mapping.get(key, (key,))


def _mentions_target_hospital(hospital_name: str, title: str, summary: str) -> bool:
    blob = f"{title or ''} {summary or ''}".lower()
    aliases = _hospital_aliases(hospital_name)
    return any(alias in blob for alias in aliases)


def main():
    print("🔍  Fetching signals from database...")
    try:
        signals_res = client.table("signals").select("id, title, summary, hospital_id, hospitals(name)").execute()
    except Exception as e:
        print(f"❌  Failed to fetch signals: {e}")
        sys.exit(1)
        
    signals = signals_res.data or []
    print(f"Total signals found in DB: {len(signals)}")
    
    mismatched = []
    for sig in signals:
        hospitals_info = sig.get("hospitals")
        if not hospitals_info:
            print(f"⚠️  Signal {sig['id']} has no associated hospital info. Skipping.")
            continue
        hospital_name = hospitals_info.get("name")
        title = sig.get("title") or ""
        summary = sig.get("summary") or ""
        
        if not _mentions_target_hospital(hospital_name, title, summary):
            mismatched.append(sig)
            
    print(f"Found {len(mismatched)} mismatched signals.")
    
    if not mismatched:
        print("✅  No mismatched signals found. Database is clean!")
        return

    print("\nMismatched Signals Details:")
    for m in mismatched:
        hname = m["hospitals"]["name"]
        print(f"  • ID: {m['id']}")
        print(f"    Hospital: {hname}")
        print(f"    Title: {m['title']}")
        print(f"    Summary: {m['summary'][:150] if m.get('summary') else ''}...")
        print("-" * 50)
        
    print(f"\nDeleting {len(mismatched)} mismatched signals...")
    for m in mismatched:
        try:
            client.table("signals").delete().eq("id", m["id"]).execute()
            print(f"  Deleted: {m['id']}")
        except Exception as e:
            print(f"  ❌  Failed to delete {m['id']}: {e}")
            
    print("\n✅  Database hygiene cleanup completed successfully!")


if __name__ == "__main__":
    main()
