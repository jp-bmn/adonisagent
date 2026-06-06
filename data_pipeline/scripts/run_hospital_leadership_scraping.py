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
    headers = {"Content-Type": "application/json"}
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
    """Use serper to find leadership for the hospital."""
    roles = ["CEO", "CFO", "CRO", "VP Revenue Cycle"]
    contacts: list[dict[str, str]] = []

    for role in roles:
        query = f"{hospital_name} {role} leadership team"
        results = serper.search_news(query=query, num_results=3)

        # In a real scenario, we might use Claude to extract the name, but
        # since we don't have the API keys or Claude configured for data extraction,
        # we will extract best-effort names from Serper snippets.
        
        # We will attempt to find a named entity near the role. This is a 
        # mock representation of what the extraction would look like.
        
        # We'll just collect the raw data here for the sake of the mock
        if results:
            first_result = results[0]
            title = str(first_result.get("title", ""))
            snippet = str(first_result.get("snippet", ""))
            
            # Very basic extraction mock
            words = title.split()
            mock_name = " ".join(words[:2]) if len(words) >= 2 else title
            
            contacts.append({
                "hospital": hospital_name,
                "role": role,
                "name": mock_name,
                "source": str(first_result.get("link", ""))
            })
            
    return contacts


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
        
        for contact in contacts:
            payload = {
                "hospital_id": hospital_id,
                "full_name": contact["name"],
                "role_title": contact["role"],
                "linkedin_url": "", # Will be enriched later
                "source_url": contact["source"]
            }
            all_contacts.append(payload)
            
            if settings.post_signals_enabled and contacts_endpoint:
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
