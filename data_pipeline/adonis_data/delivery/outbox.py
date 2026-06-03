"""Local outbox queue for payloads waiting to be delivered to backend."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def queue_payload(outbox_dir: str, payload: dict[str, Any]) -> Path:
    folder = Path(outbox_dir)
    folder.mkdir(parents=True, exist_ok=True)
    file_path = folder / f"{_utc_stamp()}_signal_batch.json"
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return file_path


def list_pending_payloads(outbox_dir: str) -> list[Path]:
    folder = Path(outbox_dir)
    if not folder.exists():
        return []
    return sorted(folder.glob("*_signal_batch.json"))


def mark_delivered(payload_file: Path) -> Path:
    delivered_file = payload_file.with_name(payload_file.name.replace("_signal_batch.json", "_delivered.json"))
    payload_file.rename(delivered_file)
    return delivered_file
