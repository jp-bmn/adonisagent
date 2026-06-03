"""serper.dev client used for Google-like news discovery."""

from __future__ import annotations

from typing import Any

from adonis_data.clients.http import post_json


class SerperClient:
    def __init__(self, api_key: str, timeout_seconds: int = 20) -> None:
        self._api_key = api_key
        self._timeout_seconds = timeout_seconds

    def search_news(self, query: str, num_results: int = 10) -> list[dict[str, Any]]:
        payload = {"q": query, "num": num_results}
        headers = {
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json",
        }
        data = post_json(
            url="https://google.serper.dev/news",
            headers=headers,
            payload=payload,
            timeout_seconds=self._timeout_seconds,
        )
        return data.get("news", [])

    def search_web(self, query: str, num_results: int = 10) -> list[dict[str, Any]]:
        payload = {"q": query, "num": num_results}
        headers = {
            "X-API-KEY": self._api_key,
            "Content-Type": "application/json",
        }
        data = post_json(
            url="https://google.serper.dev/search",
            headers=headers,
            payload=payload,
            timeout_seconds=self._timeout_seconds,
        )
        return data.get("organic", [])
