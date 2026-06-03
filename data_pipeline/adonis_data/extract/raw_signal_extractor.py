"""Convert source items into normalized raw signal candidates."""

from __future__ import annotations

from typing import Any

from adonis_data.constants import TOPIC_KEYWORDS
from adonis_data.models import RawSignal


def _match_topics(text: str) -> list[str]:
    lowered = text.lower()
    matched: list[str] = []

    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            matched.append(topic)

    return matched


def from_serper_item(hospital: str, item: dict[str, Any]) -> RawSignal:
    title = str(item.get("title", "")).strip()
    snippet = str(item.get("snippet", "")).strip()
    link = str(item.get("link", "")).strip()
    published = str(item.get("date", "")).strip()
    source = str(item.get("source", "serper")).strip() or "serper"

    text = f"{title} {snippet}"
    return RawSignal(
        hospital=hospital,
        title=title,
        source=source,
        url=link,
        published_at=published,
        matched_topics=_match_topics(text),
        excerpt=snippet,
    )


def from_newsapi_item(hospital: str, item: dict[str, Any]) -> RawSignal:
    title = str(item.get("title", "")).strip()
    description = str(item.get("description", "")).strip()
    link = str(item.get("url", "")).strip()
    published = str(item.get("publishedAt", "")).strip()
    source = str(item.get("source", {}).get("name", "NewsAPI")).strip() or "NewsAPI"

    text = f"{title} {description}"
    return RawSignal(
        hospital=hospital,
        title=title,
        source=source,
        url=link,
        published_at=published,
        matched_topics=_match_topics(text),
        excerpt=description,
    )


def from_rss_item(hospital: str, source_name: str, item: dict[str, Any]) -> RawSignal:
    title = str(item.get("title", "")).strip()
    description = str(item.get("summary", "")).strip()
    link = str(item.get("link", "")).strip()
    published = str(item.get("published", "")).strip()

    text = f"{title} {description}"
    return RawSignal(
        hospital=hospital,
        title=title,
        source=source_name,
        url=link,
        published_at=published,
        matched_topics=_match_topics(text),
        excerpt=description,
    )


def from_serper_pdf_item(
    hospital: str,
    item: dict[str, Any],
    pdf_text: str,
    source_name: str,
) -> RawSignal:
    title = str(item.get("title", "")).strip() or "PDF filing"
    link = str(item.get("link", "")).strip()
    published = str(item.get("date", "")).strip()
    excerpt = " ".join(pdf_text.split()[:90]).strip()

    text = f"{title} {pdf_text}"
    return RawSignal(
        hospital=hospital,
        title=title,
        source=source_name,
        url=link,
        published_at=published,
        matched_topics=_match_topics(text),
        excerpt=excerpt,
    )
