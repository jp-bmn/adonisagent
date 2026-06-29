import os
import sys
from pathlib import Path

# Add backend dir to python path
sys.path.append(str(Path(__file__).parent.parent))

from app.core.database import get_supabase

def migrate_users():
    supabase = get_supabase()
    
    # 1. Fetch existing users
    result = supabase.table("ae_users").select("*").execute()
    existing_users = result.data
    
    print(f"Found {len(existing_users)} existing users in ae_users")
    
    for ae in existing_users:
        name = ae["name"]
        old_id = ae["id"]
        
        # Determine email
        email = f"{name.lower().replace(' ', '.')}@adonis.com"
        password = "Adonis2026!"
        
        print(f"Migrating {name} ({email})...")
        
        try:
            # Create auth user
            auth_res = supabase.auth.admin.create_user({
                "email": email,
                "password": password,
                "email_confirm": True,
                "user_metadata": {"name": name}
            })
            
            new_id = auth_res.user.id
            print(f" -> Created Auth User: {new_id}")
            
            # Create new ae_user
            supabase.table("ae_users").insert({
                "id": new_id,
                "name": ae["name"],
                "slack_user_id": ae["slack_user_id"],
                "is_admin": ae["is_admin"]
            }).execute()
            
            # Cascade updates manually
            supabase.table("hospital_ae_assignments").update({"ae_id": new_id}).eq("ae_id", old_id).execute()
            supabase.table("digests").update({"ae_id": new_id}).eq("ae_id", old_id).execute()
            supabase.table("digest_views").update({"ae_id": new_id}).eq("ae_id", old_id).execute()
            supabase.table("signal_views").update({"ae_id": new_id}).eq("ae_id", old_id).execute()
            
            # Delete old user
            supabase.table("ae_users").delete().eq("id", old_id).execute()
            print(f" -> Successfully mapped existing records to new ID.")
            
        except Exception as e:
            print(f" -> Error migrating {name}: {e}")

if __name__ == "__main__":
    migrate_users()
