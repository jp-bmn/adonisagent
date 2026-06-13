"""Replay queued outbox payloads to the configured ingestion endpoint."""

from __future__ import annotations

import json
import time

from adonis_data.config import load_settings
from adonis_data.delivery.outbox import list_pending_payloads, mark_delivered, move_to_failed
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
    moved_to_failed_count = 0

    for payload_file in pending:
        last_error = ""
        try:
            payload = json.loads(payload_file.read_text(encoding="utf-8"))

            delivered = False
            for attempt in range(1, settings.replay_max_attempts + 1):
                result = post_signal_batch(
                    endpoint_url=settings.signals_endpoint_url,
                    payload=payload,
                    timeout_seconds=settings.request_timeout_seconds,
                    bearer_token=settings.signals_endpoint_token,
                )

                if result.get("ok"):
                    mark_delivered(payload_file)
                    delivered_count += 1
                    delivered = True
                    print(f"Delivered: {payload_file.name} (attempt {attempt})")
                    break

                status_code = result.get("status_code")
                last_error = f"HTTP {status_code}: {result.get('response_text', result.get('response_json', ''))}"
                if attempt < settings.replay_max_attempts:
                    time.sleep(settings.replay_backoff_seconds)

            if not delivered:
                failed_count += 1
                failed_file = move_to_failed(payload_file, last_error or "Replay failed after retries")
                moved_to_failed_count += 1
                print(f"Failed and moved to failed queue: {failed_file.name}")
        except Exception as exc:
            failed_count += 1
            failed_file = move_to_failed(payload_file, str(exc))
            moved_to_failed_count += 1
            print(f"Error delivering {payload_file.name}: {exc}. Moved to {failed_file.name}")

    print(
        "Replay complete. "
        f"delivered={delivered_count} failed={failed_count} moved_to_failed={moved_to_failed_count}"
    )
    return 0 if failed_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(run())
