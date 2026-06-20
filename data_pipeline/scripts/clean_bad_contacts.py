import requests
import json
import re

HEADERS = {
    "X-User-Id": "df7c14fd-cde3-4025-be00-ca42f4d31741",
    "Content-Type": "application/json"
}

BASE_URL = "https://adonisagents-production.up.railway.app/api/v1"

ERROR_PATTERNS = [
    re.compile(r"^the provided snippets", re.IGNORECASE),
    re.compile(r"^unknown$", re.IGNORECASE),
    re.compile(r"^i (could not|cannot|don't|do not)", re.IGNORECASE),
    re.compile(r"^no information", re.IGNORECASE),
    re.compile(r"^based on the (provided|given)", re.IGNORECASE),
    re.compile(r"obsidian security", re.IGNORECASE),
    re.compile(r"chutes &", re.IGNORECASE),
    re.compile(r"deals tracker:", re.IGNORECASE),
    re.compile(r"meet walmart's", re.IGNORECASE),
    re.compile(r"schomburger to", re.IGNORECASE),
    re.compile(r"fifteen thousand", re.IGNORECASE),
    re.compile(r"health systems", re.IGNORECASE),
    re.compile(r"\n"),  # newline in name
]

def is_invalid_name(name):
    if not name or len(name.strip()) < 2:
        return True
    return any(p.search(name.strip()) for p in ERROR_PATTERNS)

def run():
    print("Fetching hospitals...")
    h_res = requests.get(f"{BASE_URL}/hospitals", headers=HEADERS)
    hospitals = h_res.json()
    
    for h in hospitals:
        h_id = h.get("id")
        h_name = h.get("name")
        print(f"\nProcessing {h_name}...")
        
        c_res = requests.get(f"{BASE_URL}/contacts?hospital_id={h_id}", headers=HEADERS)
        if not c_res.ok:
            continue
            
        contacts = c_res.json()
        for c in contacts:
            c_id = c.get("id")
            name = c.get("full_name")
            
            if is_invalid_name(name):
                print(f"  [BAD] Deactivating: '{name}'")
                patch_res = requests.patch(
                    f"{BASE_URL}/contacts/{c_id}",
                    headers=HEADERS,
                    json={"is_active": False}
                )
                if patch_res.ok:
                    print("    -> Success")
                else:
                    print(f"    -> Failed: {patch_res.text}")
            else:
                pass # valid contact

if __name__ == "__main__":
    run()
