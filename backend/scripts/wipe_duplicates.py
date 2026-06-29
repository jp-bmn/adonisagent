import os
import json
import requests
from collections import defaultdict
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("Fetching all signals...")
url = f"{SUPABASE_URL}/rest/v1/signals?select=id,source_url,title,hospital_id,created_at"
res = requests.get(url, headers=headers)
signals = res.json()

by_title = defaultdict(list)
for s in signals:
    title = s.get("title", "").lower().strip()
    by_title[title].append(s)

deleted = 0
for title, items in by_title.items():
    if len(items) > 1:
        # Sort by created_at DESC so we keep the newest one
        items.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        # Keep the first one, delete the rest
        for dup in items[1:]:
            sig_id = dup["id"]
            del_url = f"{SUPABASE_URL}/rest/v1/signals?id=eq.{sig_id}"
            del_res = requests.delete(del_url, headers=headers)
            if del_res.ok:
                deleted += 1
                print(f"Deleted duplicate: {dup['title']} ({sig_id})")
            else:
                print(f"Failed to delete {sig_id}: {del_res.text}")

print(f"✅ Cleaned up {deleted} duplicates.")
