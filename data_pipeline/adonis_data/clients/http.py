"""Shared HTTP helper with consistent errors and timeouts."""

from __future__ import annotations

from typing import Any

import requests


def post_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: int,
) -> dict[str, Any]:
    response = requests.post(url, headers=headers, json=payload, timeout=timeout_seconds)
    response.raise_for_status()
    return response.json()


def get_json(url: str, params: dict[str, Any], timeout_seconds: int) -> dict[str, Any]:
    response = requests.get(url, params=params, timeout=timeout_seconds)
    response.raise_for_status()
    return response.json()
