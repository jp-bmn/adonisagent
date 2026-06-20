import os
from supabase import create_client
from dotenv import load_dotenv
load_dotenv("../.env")
url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("Missing credentials")
    exit(1)

client = create_client(url, key)

# Delete all signals that have 'example.com' or 'modernhealthcare.com/test' in their source URL
print("Deleting dummy data...")

# Fetch all signals first to see what to delete
response = client.table("signals").select("id, source_url").execute()
dummy_ids = []
for s in response.data:
    url = s.get("source_url") or ""
    if "example.com" in url or "test" in url or "e2e" in url:
        dummy_ids.append(s["id"])

if dummy_ids:
    print(f"Found {len(dummy_ids)} dummy signals. Deleting...")
    for chunk in [dummy_ids[i:i+100] for i in range(0, len(dummy_ids), 100)]:
        client.table("signals").delete().in_("id", chunk).execute()
    print("Done!")
else:
    print("No dummy signals found.")
