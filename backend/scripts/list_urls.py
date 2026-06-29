import os
from supabase import create_client
from dotenv import load_dotenv

load_dotenv("../.env")
url = os.getenv("SUPABASE_URL") or os.getenv("NEXT_PUBLIC_SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(url, key)

res = client.table("signals").select("id, source_url").execute()
print(f"Total signals in DB: {len(res.data)}")
for s in res.data:
    print(s.get("source_url"))
