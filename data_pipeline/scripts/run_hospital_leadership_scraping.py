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
import re

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
    re.compile(r"\n"),
]

def is_valid_contact_name(name):
    if not name or len(name.strip()) < 2:
        return False
    return not any(p.search(name.strip()) for p in ERROR_PATTERNS)


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
You are an expert data extraction assistant. Based on the following news snippets, extract the name of the CURRENT {role} of {hospital_name}, as well as their prior employer (if mentioned in the snippets).
If the person has retired or stepped down, extract the name of the new or current {role}.
Return a JSON object with exactly two keys: "name" and "prior_employer". 
If you cannot confidently determine the name, set "name" to "Unknown". 
If you cannot determine the prior employer, set "prior_employer" to null.
Do not wrap your response in markdown code blocks. Just output raw JSON.

Snippets:
{snippets}
"""
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=100,
                temperature=0.0,
                messages=[{"role": "user", "content": prompt}]
            )
            content = response.content[0].text.strip()
            if content.startswith("```json"):
                content = content.split("```json")[1].split("```")[0].strip()
            data = json.loads(content)
            extracted_name = data.get("name", "Unknown")
            prior_employer = data.get("prior_employer", None)
        except Exception as e:
            print(f"Error calling Anthropic: {e}")
            extracted_name = "Unknown"
            prior_employer = None
            
        if "unknown" not in extracted_name.lower():
            
            # Secondary search specifically for prior employer
            pe_query = f'"{extracted_name}" "{hospital_name}" "prior to" OR "previously" OR "former"'
            pe_results = serper.search_web(query=pe_query, num_results=5)
            pe_snippets = "\\n\\n".join(
                f"Title: {r.get('title')}\\nSnippet: {r.get('snippet')}" 
                for r in pe_results
            )
            
            pe_prompt = f"""
You are an expert data extraction assistant. We are looking for the prior employer of {extracted_name}, who is the {role} at {hospital_name}.
Based on the following search snippets, extract the name of their most recent prior employer before joining {hospital_name}.
Return a JSON object with exactly one key: "prior_employer".
If you cannot determine the prior employer from the snippets, set "prior_employer" to null.
Do not wrap your response in markdown code blocks. Just output raw JSON.

Snippets:
{pe_snippets}
"""
            try:
                pe_response = client.messages.create(
                    model="claude-haiku-4-5-20251001",
                    max_tokens=100,
                    temperature=0.0,
                    messages=[{"role": "user", "content": pe_prompt}]
                )
                pe_content = pe_response.content[0].text.strip()
                if pe_content.startswith("```json"):
                    pe_content = pe_content.split("```json")[1].split("```")[0].strip()
                pe_data = json.loads(pe_content)
                extracted_prior_employer = pe_data.get("prior_employer", prior_employer)
                if not extracted_prior_employer:
                    extracted_prior_employer = prior_employer # Fallback to the one extracted from news
            except Exception as e:
                print(f"Error calling Anthropic for prior employer: {e}")
                extracted_prior_employer = prior_employer

            contacts.append({
                "hospital": hospital_name,
                "role": role,
                "name": extracted_name,
                "prior_employer": extracted_prior_employer,
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
        
        # Validation
        valid_contacts = []
        for contact in contacts:
            if is_valid_contact_name(contact["name"]):
                valid_contacts.append(contact)
            else:
                print(f"Skipping invalid contact name: {contact['name']}")
        contacts = valid_contacts
        
        # Verify via API
        if contacts:
            verifier_url = "https://adonisagents-production.up.railway.app/verify"
            payload = {
                "contacts": [
                    {
                        "id": str(i),
                        "name": c["name"],
                        "role": c["role"],
                        "hospital": c["hospital"]
                    }
                    for i, c in enumerate(contacts)
                ]
            }
            try:
                print("Calling LinkedIn Verifier API...")
                v_res = requests.post(verifier_url, json=payload, timeout=60)
                if v_res.ok:
                    v_results = v_res.json().get("results", [])
                    for v_item in v_results:
                        for c in contacts:
                            if c["name"] == v_item["name"] and c["role"] == v_item["role"]:
                                if v_item.get("status") == "verified" and v_item.get("suggestedUrl"):
                                    c["linkedin_url"] = v_item["suggestedUrl"]
                                break
                else:
                    print(f"Verifier API error: {v_res.status_code}")
            except Exception as e:
                print(f"Failed to call verifier API: {e}")

        if settings.post_signals_enabled and contacts_endpoint and hospital_id:
            existing_contacts = get_contacts(contacts_endpoint, hospital_id, settings.request_timeout_seconds, settings.signals_endpoint_token)
            
        for contact in contacts:
            full_name = contact["name"]
            role = contact["role"]
            payload = {
                "hospital_id": hospital_id,
                "full_name": full_name,
                "role": role,
                "prior_employer": contact["prior_employer"],
                "linkedin_url": contact["linkedin_url"],
                "source_url": contact["source"]
            }
            all_contacts.append(payload)
            
            if settings.post_signals_enabled and contacts_endpoint:
                existing_for_role = [c for c in existing_contacts if c.get("role") == role and c.get("is_active", True)]
                
                exact_match = None
                for c in existing_for_role:
                    if c.get("full_name") == full_name:
                        exact_match = c
                        break
                        
                if exact_match:
                    patch_payload = {
                        "role": role,
                    }
                    if contact["prior_employer"]:
                        patch_payload["prior_employer"] = contact["prior_employer"]
                    if contact["linkedin_url"]:
                        patch_payload["linkedin_url"] = contact["linkedin_url"]
                    res = patch_contact(
                        endpoint_url=contacts_endpoint,
                        contact_id=exact_match["id"],
                        payload=patch_payload,
                        timeout_seconds=settings.request_timeout_seconds,
                        bearer_token=settings.signals_endpoint_token
                    )
                    for c in existing_for_role:
                        if c["id"] != exact_match["id"]:
                            patch_contact(
                                endpoint_url=contacts_endpoint,
                                contact_id=c["id"],
                                payload={"is_active": False},
                                timeout_seconds=settings.request_timeout_seconds,
                                bearer_token=settings.signals_endpoint_token
                            )
                else:
                    for c in existing_for_role:
                        patch_contact(
                            endpoint_url=contacts_endpoint,
                            contact_id=c["id"],
                            payload={"is_active": False},
                            timeout_seconds=settings.request_timeout_seconds,
                            bearer_token=settings.signals_endpoint_token
                        )
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
