"""RSS ingestion helpers for healthcare trade press feeds."""

from __future__ import annotations

from typing import Any

import feedparser


def fetch_rss_entries(feed_url: str) -> list[dict[str, Any]]:
    parsed = feedparser.parse(feed_url)
    return list(parsed.entries or [])


def filter_entries_by_hospital(
    entries: list[dict[str, Any]],
    hospital_name: str,
) -> list[dict[str, Any]]:
    needle = hospital_name.lower()
    filtered: list[dict[str, Any]] = []

    for entry in entries:
        title = str(entry.get("title", ""))
        summary = str(entry.get("summary", ""))
        blob = f"{title} {summary}".lower()
        if needle in blob:
            filtered.append(entry)

    return filtered
