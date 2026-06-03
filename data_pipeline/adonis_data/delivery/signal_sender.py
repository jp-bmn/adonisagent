"""HTTP sender for optional batch delivery to backend ingestion endpoints."""

from __future__ import annotations

from typing import Any

import requests


def post_signal_batch(
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
