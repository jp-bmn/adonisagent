import os
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Missing Supabase credentials")
    exit(1)

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("Fetching all signals from DB...")
# Fetch all signals
url = f"{SUPABASE_URL}/rest/v1/signals?select=id,source_url,title,hospital_id,created_at"
res = requests.get(url, headers=headers)
if not res.ok:
    print(f"❌ Failed to fetch signals: {res.text}")
    exit(1)

signals = res.json()
print(f"Found {len(signals)} total signals in the DB.")

# Track seen urls and titles per hospital
seen_urls = set()
seen_titles = set()
duplicates_to_delete = []

# Sort by created_at desc so we keep the newest ones and delete the older ones
signals.sort(key=lambda s: s.get("created_at", ""), reverse=True)

for s in signals:
    sig_id = s["id"]
    source_url = s.get("source_url")
    title = s.get("title", "").lower().strip()
    hospital_id = s.get("hospital_id")
    
    is_duplicate = False
    
    if source_url:
        # Basic canonicalization (strip query params)
        canonical = source_url.split("?")[0].rstrip("/")
        if canonical in seen_urls:
            is_duplicate = True
        else:
            seen_urls.add(canonical)
            
    title_key = f"{hospital_id}_{title}"
    if title_key in seen_titles:
        is_duplicate = True
    else:
        seen_titles.add(title_key)
        
    if is_duplicate:
        duplicates_to_delete.append(sig_id)

print(f"Found {len(duplicates_to_delete)} duplicates to delete.")

# Delete them
deleted = 0
for sig_id in duplicates_to_delete:
    del_url = f"{SUPABASE_URL}/rest/v1/signals?id=eq.{sig_id}"
    del_res = requests.delete(del_url, headers=headers)
    if del_res.ok:
        deleted += 1
    else:
        print(f"Failed to delete {sig_id}: {del_res.text}")

print(f"✅ Successfully deleted {deleted} duplicate signals from the database!")
