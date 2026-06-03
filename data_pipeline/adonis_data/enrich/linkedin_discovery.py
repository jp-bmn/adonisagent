"""Find candidate LinkedIn profile URLs for contact leads via Serper web search."""

from __future__ import annotations

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
