"""Verify and update LinkedIn URLs using Claude and Serper."""

import os
import requests
import json
from typing import Any
from anthropic import Anthropic
from adonis_data.clients.serper import SerperClient
from adonis_data.config import load_settings

def patch_contact(
    endpoint_url: str,
    contact_id: str,
    payload: dict[str, Any],
    timeout_seconds: int,
    bearer_token: str = "",
) -> dict[str, Any]:
    headers = {
        "Content-Type": "application/json",
        "X-User-Id": "df7c14fd-cde3-4025-be00-ca42f4d31741"
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    url = f"{endpoint_url}/{contact_id}"
    response = requests.patch(
        url,
        json=payload,
        headers=headers,
        timeout=timeout_seconds,
    )

    result: dict[str, Any] = {
        "ok": response.ok,
        "status_code": response.status_code,
    }

    try:
        result["response_json"] = response.json()
    except ValueError:
        result["response_text"] = response.text[:1000]

    return result

def get_all_contacts(endpoint_url: str, timeout_seconds: int, hospital_id_map: dict[str, str], bearer_token: str = "") -> list[dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "X-User-Id": "df7c14fd-cde3-4025-be00-ca42f4d31741"
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"

    all_contacts = []
    for hospital_name, hospital_id in hospital_id_map.items():
        url = f"{endpoint_url}?hospital_id={hospital_id}"
        response = requests.get(url, headers=headers, timeout=timeout_seconds)
        if response.ok:
            all_contacts.extend(response.json())
        else:
            print(f"Failed to fetch contacts for {hospital_name}: {response.text}")
    return all_contacts

def run():
    settings = load_settings()
    serper = SerperClient(api_key=settings.serper_api_key, timeout_seconds=settings.request_timeout_seconds)
    
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("Missing ANTHROPIC_API_KEY")
        
    claude = Anthropic(api_key=anthropic_api_key)
    
    contacts_endpoint = settings.signals_endpoint_url.replace("/signals/batch", "/contacts")
    
    contacts = get_all_contacts(contacts_endpoint, settings.request_timeout_seconds, settings.hospital_id_map, settings.signals_endpoint_token)
    
    print(f"Loaded {len(contacts)} contacts for verification.")
    
    for contact in contacts:
        contact_id = contact["id"]
        full_name = contact["full_name"]
        role = contact.get("role", "")
        # The API doesn't return hospital_name, but it returns hospital_id.
        # We can map it back using settings.hospital_id_map
        hospital_id = contact.get("hospital_id")
        
        hospital_name = ""
        for name, h_id in settings.hospital_id_map.items():
            if h_id == hospital_id:
                hospital_name = name
                break
                
        if not hospital_name:
            continue
            
        print(f"Verifying {full_name} ({role}) at {hospital_name}...")
        
        query = f'"{full_name}" "{hospital_name}" "{role}" site:linkedin.com'
        results = serper.search_web(query=query, num_results=3)
        
        if not results:
            print("  No LinkedIn results found.")
            patch_contact(
                contacts_endpoint,
                contact_id,
                {"linkedin_url": "", "linkedin_verified": False},
                settings.request_timeout_seconds,
                settings.signals_endpoint_token
            )
            continue
            
        top_result = results[0]
        url = top_result.get("link", "")
        snippet = top_result.get("snippet", "")
        title = top_result.get("title", "")
        
        prompt = f"""
You are verifying a LinkedIn profile for a hospital executive. 
We are looking for:
Name: {full_name}
Role: {role}
Hospital: {hospital_name}

Top LinkedIn Search Result:
Title: {title}
Snippet: {snippet}
URL: {url}

Based on the title and snippet, does this LinkedIn profile confidently match the person we are looking for?
It should match the name and ideally indicate an affiliation with the hospital or role.
Respond with exactly "YES" if it's a confident match, or "NO" if it's not.
"""
        
        try:
            response = claude.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=10,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            answer = response.content[0].text.strip().upper()
        except Exception as e:
            print(f"  Error calling Anthropic: {e}")
            answer = "NO"
            
        if "YES" in answer:
            print(f"  Matched! URL: {url}")
            patch_contact(
                contacts_endpoint,
                contact_id,
                {"linkedin_url": url, "linkedin_verified": True},
                settings.request_timeout_seconds,
                settings.signals_endpoint_token
            )
        else:
            print(f"  No confident match found. (Response: {answer})")
            patch_contact(
                contacts_endpoint,
                contact_id,
                {"linkedin_url": "", "linkedin_verified": False},
                settings.request_timeout_seconds,
                settings.signals_endpoint_token
            )

if __name__ == "__main__":
    run()
