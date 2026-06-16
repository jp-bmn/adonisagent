"""
Task 2 — Python-based seed runner.

Alternative to running SQL directly in the Supabase editor.
Uses supabase-py with the service_role key to insert seed data.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/seed_db.py

Run AFTER executing migrations/001_initial_schema.sql in the Supabase SQL Editor,
or use this script to re-seed users/hospitals without re-running DDL.
"""
import os
import sys
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌  SUPABASE_URL and SUPABASE_KEY must be set in .env")
    sys.exit(1)

from supabase import create_client

client = create_client(SUPABASE_URL, SUPABASE_KEY)


def seed_hospitals():
    hospitals = [
        {"name": "NewYork-Presbyterian",                    "website_url": "https://nyp.org"},
        {"name": "UMass Memorial",                          "website_url": "https://umassmemorial.org"},
        {"name": "Ascension",                               "website_url": "https://ascension.org"},
        {"name": "University of Arkansas Medical Sciences", "website_url": "https://uams.edu"},
        {
            "name": "CommonSpirit Health",
            "website_url": "https://commonspirit.org",
            "division_note": "Specific division TBD — confirm with Danielle before expanding scraper scope",
        },
        {"name": "Jefferson Health",                        "website_url": "https://www.jeffersonhealth.org"},
    ]
    result = client.table("hospitals").upsert(hospitals, on_conflict="name").execute()
    print(f"  ✅  Hospitals upserted: {len(result.data)}")
    return {h["name"]: h["id"] for h in result.data}


def seed_ae_users():
    users = [
        {"name": "Danielle Ferdon", "slack_user_id": "PLACEHOLDER_DANIELLE", "is_admin": True},
        {"name": "Michael",         "slack_user_id": "PLACEHOLDER_MICHAEL",   "is_admin": False},
        {"name": "David",           "slack_user_id": "PLACEHOLDER_DAVID",     "is_admin": False},
        {"name": "Jeff",            "slack_user_id": "PLACEHOLDER_JEFF",      "is_admin": False},
    ]
    result = client.table("ae_users").upsert(users, on_conflict="name").execute()
    print(f"  ✅  AE users upserted: {len(result.data)}")
    return {u["name"]: u["id"] for u in result.data}


def seed_assignments(hospital_ids: dict, ae_ids: dict):
    MAPPING = [
        ("NewYork-Presbyterian",                    "Michael"),
        ("UMass Memorial",                          "Michael"),
        ("Ascension",                               "David"),
        ("University of Arkansas Medical Sciences", "David"),
        ("CommonSpirit Health",                     "David"),
        ("Jefferson Health",                        "Jeff"),
    ]
    assignments = [
        {"hospital_id": hospital_ids[h], "ae_id": ae_ids[u]}
        for h, u in MAPPING
        if h in hospital_ids and u in ae_ids
    ]
    result = (
        client.table("hospital_ae_assignments")
        .upsert(assignments, on_conflict="hospital_id,ae_id")
        .execute()
    )
    print(f"  ✅  Assignments upserted: {len(result.data)}")


def main():
    print("\n🌱  Adonis — database seed\n" + "─" * 40)
    try:
        hospital_ids = seed_hospitals()
        ae_ids       = seed_ae_users()
        seed_assignments(hospital_ids, ae_ids)
        print("\n✅  Seed complete. Run verify_seed.py to confirm.\n")
    except Exception as e:
        print(f"\n❌  Seed failed: {e}")
        raise


if __name__ == "__main__":
    main()
