"""Move failed outbox payloads back into pending queue for replay."""

from __future__ import annotations

from pathlib import Path

from adonis_data.config import load_settings


def run() -> int:
    settings = load_settings()
    outbox_dir = Path(settings.outbox_dir)
    failed_dir = outbox_dir / "failed"

    if not failed_dir.exists():
        print("No failed outbox directory found.")
        return 0

    failed_payloads = sorted(failed_dir.glob("*_failed.json"))
    if not failed_payloads:
        print("No failed payloads to requeue.")
        return 0

    requeued = 0
    for failed_file in failed_payloads:
        pending_name = failed_file.name.replace("_failed.json", "_signal_batch.json")
        pending_file = outbox_dir / pending_name
        failed_file.rename(pending_file)

        error_file = failed_file.with_suffix(".error.txt")
        if error_file.exists():
            error_file.unlink()

        requeued += 1
        print(f"Requeued: {pending_file.name}")

    print(f"Requeue complete. payloads={requeued}")
    return 0


if __name__ == "__main__":
    raise SystemExit(run())
