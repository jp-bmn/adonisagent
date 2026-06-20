import os
import sys
from pathlib import Path

# Add the backend directory to sys.path so we can import from app
backend_dir = Path(__file__).parent.parent
sys.path.append(str(backend_dir))

from dotenv import load_dotenv
load_dotenv(backend_dir / ".env")

from supabase import create_client, Client

def clean_contacts():
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not supabase_key:
        supabase_key = os.environ.get("SUPABASE_KEY")
        
    if not supabase_url or not supabase_key:
        print("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY")
        sys.exit(1)
        
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # 1. Fetch all contacts
    print("Fetching contacts...")
    response = supabase.table("contacts").select("id, full_name, hospital_id, linkedin_url").execute()
    contacts = response.data
    print(f"Total contacts found: {len(contacts)}")
    
    garbage_keywords = [
        "health systems", "obsidian security", "chutes &", 
        "meet walmart's", "schomburger to", "fifteen thousand", "unknown"
    ]
    
    deleted_count = 0
    
    for contact in contacts:
        name_lower = contact.get("full_name", "").lower()
        hospital_id = contact.get("hospital_id", "")
        linkedin_url = contact.get("linkedin_url")
        
        is_bad = False
        reason = ""
        
        if hospital_id == "jefferson": # Wait, what is Jefferson's ID? Actually, let's find it.
            # I don't know jefferson ID. I'll just delete where hospital_id is jefferson
            is_bad = True
            reason = "Jefferson Health needs a full scrape"
        
        elif any(kw in name_lower for kw in garbage_keywords):
            is_bad = True
            reason = "Matches garbage keyword"
            
        elif any(char in name_lower for char in ['<', '>', '{', '}', '[', ']']):
            is_bad = True
            reason = "Contains special characters"
            
        elif not linkedin_url:
            is_bad = True
            reason = "Null LinkedIn URL"
            
        if is_bad:
            print(f"Deleting contact '{contact.get('full_name')}' (ID: {contact['id']}): {reason}")
            try:
                supabase.table("contacts").delete().eq("id", contact["id"]).execute()
                deleted_count += 1
            except Exception as e:
                print(f"Failed to delete {contact['id']}: {e}")
                
    # We should also ensure Jefferson Health is deleted if hospital_id was different (e.g., 'jefferson-health')
    print("Deleting any remaining Jefferson Health contacts...")
    try:
        # Search for Jefferson hospitals
        h_resp = supabase.table("hospitals").select("id, name").ilike("name", "%jefferson%").execute()
        for h in h_resp.data:
            print(f"Found Jefferson hospital ID: {h['id']}")
            try:
                del_resp = supabase.table("contacts").delete().eq("hospital_id", h['id']).execute()
                print(f"Deleted contacts for {h['id']}: {len(del_resp.data) if hasattr(del_resp, 'data') and del_resp.data else 0}")
            except Exception as e:
                print(f"Error deleting Jefferson contacts: {e}")
    except Exception as e:
        print(f"Error querying Jefferson hospitals: {e}")
        
    print(f"Done. Deleted {deleted_count} individual bad contacts.")

if __name__ == "__main__":
    clean_contacts()
