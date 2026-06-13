import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv("backend/.env")
url = os.environ.get("SUPABASE_URL")
key = os.environ.get("SUPABASE_KEY")
supabase = create_client(url, key)

res_all = supabase.table("signals").select("id, review_status").execute()
print("Total signals:", len(res_all.data))
print("Null signals:", len([s for s in res_all.data if s.get("review_status") is None]))
print("Dismissed signals:", len([s for s in res_all.data if s.get("review_status") == "dismissed"]))

res_or = supabase.table("signals").select("id, review_status").or_("review_status.is.null,review_status.neq.dismissed").execute()
print("Filtered with OR:", len(res_or.data))
print("Filtered Nulls:", len([s for s in res_or.data if s.get("review_status") is None]))
