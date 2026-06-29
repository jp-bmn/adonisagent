import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_KEY")

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

url = f"{SUPABASE_URL}/rest/v1/signals?select=id,source_url,title,hospital_id,created_at"
res = requests.get(url, headers=headers)
signals = res.json()

with open("signals_dump.json", "w") as f:
    json.dump(signals, f, indent=2)

print(f"Dumped {len(signals)} signals to signals_dump.json")
