"""Scrape hospital leadership data and post to backend."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from adonis_data.clients.serper import SerperClient
from adonis_data.config import load_settings
from adonis_data.constants import HOSPITAL_QUERIES
import requests


def post_contact(
    endpoint_url: str,
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

    response = requests.post(
        endpoint_url,
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


def extract_leadership(hospital_name: str, serper: SerperClient) -> list[dict[str, str]]:
    """Use serper and Claude to find current leadership for the hospital."""
    import os
    from anthropic import Anthropic
    
    anthropic_api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not anthropic_api_key:
        raise ValueError("Missing ANTHROPIC_API_KEY")
        
    client = Anthropic(api_key=anthropic_api_key)
    roles = ["CEO", "CFO", "CRO", "VP Revenue Cycle"]
    contacts: list[dict[str, str]] = []

    for role in roles:
        query = f"{hospital_name} {role} leadership team"
        results = serper.search_news(query=query, num_results=5)
        
        if not results:
            continue
            
        snippets = "\n\n".join(
            f"Title: {r.get('title')}\nSnippet: {r.get('snippet')}" 
            for r in results
        )
        
        prompt = f"""
You are an expert data extraction assistant. Based on the following news snippets, extract the name of the CURRENT {role} of {hospital_name}.
If the person has retired or stepped down, extract the name of the new or current {role}.
Return ONLY the person's full name, and nothing else. If you cannot confidently determine the name, return 'Unknown'.

Snippets:
{snippets}
"""
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=50,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            extracted_name = response.content[0].text.strip()
        except Exception as e:
            print(f"Error calling Anthropic: {e}")
            extracted_name = "Unknown"
            
        if extracted_name != "Unknown":
            contacts.append({
                "hospital": hospital_name,
                "role": role,
                "name": extracted_name,
                "linkedin_url": "", # Left blank for the verifier agent
                "source": str(results[0].get("link", ""))
            })
            
    return contacts


def get_contacts(
    endpoint_url: str,
    hospital_id: str,
    timeout_seconds: int,
    bearer_token: str = "",
) -> list[dict[str, Any]]:
    headers = {
        "Content-Type": "application/json",
        "X-User-Id": "df7c14fd-cde3-4025-be00-ca42f4d31741"
    }
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
        
    url = f"{endpoint_url}?hospital_id={hospital_id}"
    response = requests.get(url, headers=headers, timeout=timeout_seconds)
    if response.ok:
        return response.json()
    return []

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

def run() -> Path:
    settings = load_settings()
    serper = SerperClient(api_key=settings.serper_api_key, timeout_seconds=settings.request_timeout_seconds)

    contacts_endpoint = settings.signals_endpoint_url.replace("/signals/batch", "/contacts")

    all_contacts: list[dict[str, str]] = []
    post_results: list[dict[str, Any]] = []

    for hospital in HOSPITAL_QUERIES.keys():
        print(f"Scraping leadership for {hospital}...")
        hospital_id = settings.hospital_id_map.get(hospital, "") if settings.hospital_id_map else ""
        contacts = extract_leadership(hospital, serper)
        
        existing_contacts = []
        if settings.post_signals_enabled and contacts_endpoint and hospital_id:
            existing_contacts = get_contacts(contacts_endpoint, hospital_id, settings.request_timeout_seconds, settings.signals_endpoint_token)
            
        existing_map = {c["full_name"]: c["id"] for c in existing_contacts if "full_name" in c and "id" in c}
        
        for contact in contacts:
            full_name = contact["name"]
            payload = {
                "hospital_id": hospital_id,
                "full_name": full_name,
                "role": contact["role"],
                "linkedin_url": contact["linkedin_url"],
                "source_url": contact["source"]
            }
            all_contacts.append(payload)
            
            if settings.post_signals_enabled and contacts_endpoint:
                if full_name in existing_map:
                    patch_payload = {
                        "role": contact["role"],
                        "linkedin_url": contact["linkedin_url"]
                    }
                    res = patch_contact(
                        endpoint_url=contacts_endpoint,
                        contact_id=existing_map[full_name],
                        payload=patch_payload,
                        timeout_seconds=settings.request_timeout_seconds,
                        bearer_token=settings.signals_endpoint_token
                    )
                else:
                    res = post_contact(
                        endpoint_url=contacts_endpoint,
                        payload=payload,
                        timeout_seconds=settings.request_timeout_seconds,
                        bearer_token=settings.signals_endpoint_token
                    )
                post_results.append({"payload": payload, "result": res})

    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    contacts_path = output_dir / "day3_leadership_contacts.json"
    contacts_path.write_text(json.dumps(all_contacts, indent=2), encoding="utf-8")
    
    if post_results:
        results_path = output_dir / "day3_leadership_post_results.json"
        results_path.write_text(json.dumps(post_results, indent=2), encoding="utf-8")

    return contacts_path


if __name__ == "__main__":
    path = run()
    print(f"Wrote extracted contacts to {path}")
