"""NewsAPI client for backup and breadth in initial discovery."""

from __future__ import annotations

from typing import Any

from adonis_data.clients.http import get_json


class NewsApiClient:
    def __init__(self, api_key: str, timeout_seconds: int = 20) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def search_everything(self, query: str, page_size: int = 10) -> list[dict[str, Any]]:
        data = get_json(
            url="https://newsapi.org/v2/everything",
            params={
                "q": query,
                "apiKey": self._api_key,
                "language": "en",
                "sortBy": "publishedAt",
                "pageSize": page_size,
            },
            timeout_seconds=self._timeout_seconds,
        )
        return data.get("articles", [])
