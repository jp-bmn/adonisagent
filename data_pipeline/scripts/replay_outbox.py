"""Replay queued outbox payloads to the configured ingestion endpoint."""

from __future__ import annotations

import json

from adonis_data.config import load_settings
from adonis_data.delivery.outbox import list_pending_payloads, mark_delivered
from adonis_data.delivery.signal_sender import post_signal_batch


def run() -> int:
    settings = load_settings()

    if not settings.signals_endpoint_url:
        print("Missing SIGNALS_ENDPOINT_URL in .env")
        return 1

    pending = list_pending_payloads(settings.outbox_dir)
    if not pending:
        print("No pending outbox payloads found.")
        return 0

    delivered_count = 0
    failed_count = 0

    for payload_file in pending:
        try:
            payload = json.loads(payload_file.read_text(encoding="utf-8"))
            result = post_signal_batch(
                endpoint_url=settings.signals_endpoint_url,
                payload=payload,
                timeout_seconds=settings.request_timeout_seconds,
                bearer_token=settings.signals_endpoint_token,
            )

            if result.get("ok"):
                mark_delivered(payload_file)
                delivered_count += 1
                print(f"Delivered: {payload_file.name}")
            else:
                failed_count += 1
                print(f"Failed ({result.get('status_code')}): {payload_file.name}")
        except Exception as exc:
            failed_count += 1
            print(f"Error delivering {payload_file.name}: {exc}")

    print(f"Replay complete. delivered={delivered_count} failed={failed_count}")
    return 0 if failed_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(run())
