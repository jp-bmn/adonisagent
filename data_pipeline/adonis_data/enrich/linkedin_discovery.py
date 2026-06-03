"""Find candidate LinkedIn profile URLs for contact leads via Serper web search."""

from __future__ import annotations

import re
from urllib.parse import urlparse

from adonis_data.clients.serper import SerperClient


def build_linkedin_query(full_name: str, hospital: str) -> str:
    return f"site:linkedin.com/in {full_name} {hospital}".strip()


def discover_linkedin_url(
    serper: SerperClient,
    full_name: str,
    hospital: str,
    num_results: int = 5,
) -> tuple[str, str]:
    query = build_linkedin_query(full_name=full_name, hospital=hospital)
    results = serper.search_web(query=query, num_results=num_results)

    for item in results:
        link = str(item.get("link", "")).strip()
        if "linkedin.com/in/" in link:
            return query, link

    return query, ""


def score_linkedin_match(full_name: str, hospital: str, linkedin_url: str) -> tuple[float, str]:
    if not linkedin_url:
        return 0.0, "missing_linkedin_url"

    parsed = urlparse(linkedin_url)
    path = parsed.path.lower()
    slug = path.replace("/in/", "").strip("/")

    name_parts = [p.lower() for p in full_name.split() if p.strip()]
    if not name_parts:
        return 0.2, "missing_name_parts"

    name_hits = sum(1 for part in name_parts if part in slug)
    name_score = name_hits / len(name_parts)

    hospital_tokens = [
        token
        for token in re.split(r"[^a-zA-Z0-9]+", hospital.lower())
        if token and token not in {"health", "hospital", "memorial", "newyork", "new", "york"}
    ]
    hospital_hit = any(token in slug for token in hospital_tokens)

    score = 0.2 + (0.7 * name_score) + (0.1 if hospital_hit else 0.0)
    score = max(0.0, min(1.0, score))

    reason = f"name_hits={name_hits}/{len(name_parts)}"
    if hospital_hit:
        reason += "|hospital_token_hit"
    return score, reason
