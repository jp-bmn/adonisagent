"""
Task 2 — Supabase seed verification script.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/verify_seed.py

Expects a .env file with SUPABASE_URL and SUPABASE_KEY (service_role key).
Run AFTER executing migrations/001_initial_schema.sql in the Supabase SQL Editor.
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

CHECKS = [
    ("hospitals",                5, "5 hospitals"),
    ("ae_users",                 4, "4 AE users (Danielle, Michael, David, Jeff)"),
    ("hospital_ae_assignments",  5, "5 territory assignments"),
]

print("\n🔍  Adonis — Supabase seed verification\n" + "─" * 45)

all_ok = True
for table, expected, label in CHECKS:
    col = "hospital_id" if table == "hospital_ae_assignments" else "id"
    result = client.table(table).select(col, count="exact").execute()
    count = result.count
    status = "✅" if count == expected else "❌"
    if count != expected:
        all_ok = False
    print(f"  {status}  {table:30s}  {count:3d}  (expected {expected})  — {label}")

# Detailed hospital + AE dump
print("\n📋  Hospitals and their assigned AEs:\n" + "─" * 45)
hospitals = client.table("hospitals").select("id, name, website_url").execute().data
assignments = client.table("hospital_ae_assignments").select("hospital_id, ae_id").execute().data
ae_users = {u["id"]: u["name"] for u in client.table("ae_users").select("id, name").execute().data}

for h in hospitals:
    aes = [ae_users[a["ae_id"]] for a in assignments if a["hospital_id"] == h["id"]]
    ae_str = ", ".join(aes) if aes else "(unassigned)"
    print(f"  • {h['name']:<45s} → {ae_str}")

print()
if all_ok:
    print("✅  All checks passed — database is ready for Task 3.\n")
else:
    print("❌  Some checks failed — re-run the SQL migration and try again.\n")
    sys.exit(1)
