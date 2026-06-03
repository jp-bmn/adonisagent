"""Find candidate LinkedIn profile URLs for contact leads via Serper web search."""

from __future__ import annotations

from dataclasses import dataclass
import re
from urllib.parse import urlparse

from adonis_data.clients.serper import SerperClient


def build_linkedin_query(full_name: str, hospital: str) -> str:
    return f"site:linkedin.com/in {full_name} {hospital}".strip()


_STOPWORDS = {
    "and",
    "the",
    "for",
    "with",
    "from",
    "new",
    "york",
    "health",
    "hospital",
    "memorial",
}


@dataclass(frozen=True)
class LinkedInDiscoveryResult:
    query: str
    linkedin_url: str
    match_score: float
    match_reason: str
    match_bucket: str


def _tokenize(text: str) -> list[str]:
    return [
        token
        for token in re.split(r"[^a-zA-Z0-9]+", text.lower())
        if token and len(token) > 1 and token not in _STOPWORDS
    ]


def classify_match_bucket(score: float, linkedin_url: str) -> str:
    if not linkedin_url:
        return "missing"
    if score >= 0.75:
        return "high"
    if score >= 0.50:
        return "medium"
    return "low"


def discover_best_linkedin_match(
    serper: SerperClient,
    full_name: str,
    hospital: str,
    num_results: int = 5,
) -> LinkedInDiscoveryResult:
    query = build_linkedin_query(full_name=full_name, hospital=hospital)
    results = serper.search_web(query=query, num_results=num_results)

    best_url = ""
    best_score = 0.0
    best_reason = "missing_linkedin_url"

    for item in results:
        link = str(item.get("link", "")).strip()
        if "linkedin.com/in/" not in link:
            continue

        title = str(item.get("title", ""))
        snippet = str(item.get("snippet", ""))
        score, reason = score_linkedin_match(
            full_name=full_name,
            hospital=hospital,
            linkedin_url=link,
            title=title,
            snippet=snippet,
        )
        if score > best_score:
            best_url = link
            best_score = score
            best_reason = reason

    return LinkedInDiscoveryResult(
        query=query,
        linkedin_url=best_url,
        match_score=round(best_score, 3),
        match_reason=best_reason,
        match_bucket=classify_match_bucket(best_score, best_url),
    )


def score_linkedin_match(
    full_name: str,
    hospital: str,
    linkedin_url: str,
    title: str = "",
    snippet: str = "",
) -> tuple[float, str]:
    if not linkedin_url:
        return 0.0, "missing_linkedin_url"

    parsed = urlparse(linkedin_url)
    path = parsed.path.lower()
    slug = path.replace("/in/", "").strip("/")

    name_parts = _tokenize(full_name)
    if not name_parts:
        return 0.2, "missing_name_parts"

    context_blob = " ".join([slug, title.lower(), snippet.lower()])
    name_hits = sum(1 for part in name_parts if part in context_blob)
    name_score = name_hits / len(name_parts)

    hospital_tokens = _tokenize(hospital)
    hospital_hits = sum(1 for token in hospital_tokens if token in context_blob)
    hospital_score = 0.0
    if hospital_tokens:
        hospital_score = hospital_hits / len(hospital_tokens)

    full_name_phrase = " ".join(name_parts)
    phrase_hit = full_name_phrase in " ".join([title.lower(), snippet.lower(), slug.replace("-", " ")])

    score = 0.1 + (0.70 * name_score) + (0.15 * hospital_score) + (0.05 if phrase_hit else 0.0)
    if name_hits == 0:
        score = max(0.0, score - 0.2)
    score = max(0.0, min(1.0, score))

    reason = (
        f"name_hits={name_hits}/{len(name_parts)}"
        f"|hospital_hits={hospital_hits}/{max(1, len(hospital_tokens))}"
    )
    if phrase_hit:
        reason += "|name_phrase_hit"
    return score, reason
