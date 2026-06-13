"""Run the data pipeline on a schedule with reliability guardrails."""

from __future__ import annotations

import argparse
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable

from scripts.generate_team_update import run as run_team_update
from scripts.preflight_live_post import run as run_preflight
from scripts.run_contact_linkedin_discovery import run as run_contact_discovery
from scripts.run_day1_collection import run as run_day1_collection


@dataclass(frozen=True)
class RetryResult:
    ok: bool
    attempts: int
    last_error: str


class LockAcquisitionError(RuntimeError):
    pass


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _is_stale_lock(lock_payload: dict[str, Any], stale_lock_minutes: int) -> bool:
    acquired_text = str(lock_payload.get("acquired_at_utc", "")).strip()
    if not acquired_text:
        return True

    try:
        acquired_at = datetime.fromisoformat(acquired_text)
    except ValueError:
        return True

    if acquired_at.tzinfo is None:
        acquired_at = acquired_at.replace(tzinfo=timezone.utc)

    return acquired_at < (_utc_now() - timedelta(minutes=stale_lock_minutes))


def _acquire_lock(lock_path: Path, stale_lock_minutes: int) -> None:
    lock_path.parent.mkdir(parents=True, exist_ok=True)

    if lock_path.exists():
        existing = _read_json(lock_path)
        if _is_stale_lock(existing, stale_lock_minutes=stale_lock_minutes):
            lock_path.unlink(missing_ok=True)
        else:
            owner = existing.get("pid", "unknown")
            acquired_at = existing.get("acquired_at_utc", "unknown")
            raise LockAcquisitionError(
                f"Scheduler lock already held (pid={owner}, acquired_at_utc={acquired_at})."
            )

    payload = {
        "pid": os.getpid(),
        "acquired_at_utc": _utc_now().isoformat(),
    }
    _write_json(lock_path, payload)


def _release_lock(lock_path: Path) -> None:
    lock_path.unlink(missing_ok=True)


def _append_scheduler_event(log_path: Path, event: dict[str, Any]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, separators=(",", ":")) + "\n")


def _run_with_retries(
    task: Callable[[], None],
    attempts: int,
    backoff_seconds: int,
) -> RetryResult:
    max_attempts = max(1, attempts)
    last_error = ""
    for attempt in range(1, max_attempts + 1):
        try:
            task()
            return RetryResult(ok=True, attempts=attempt, last_error="")
        except Exception as exc:  # noqa: BLE001 - scheduler should keep control on task failures
            last_error = str(exc)
            if attempt < max_attempts:
                sleep_seconds = max(0, backoff_seconds) * attempt
                if sleep_seconds:
                    time.sleep(sleep_seconds)

    return RetryResult(ok=False, attempts=max_attempts, last_error=last_error)


def _run_pipeline_cycle(
    quality_mode: str | None,
    run_contact: bool,
    skip_preflight: bool,
    skip_endpoint_check: bool,
) -> None:
    if not skip_preflight:
        preflight_code = run_preflight(check_endpoint=not skip_endpoint_check)
        if preflight_code == 2:
            raise RuntimeError("Preflight failed with readiness=BLOCKED.")

    run_day1_collection(quality_mode_override=quality_mode)
    if run_contact:
        run_contact_discovery()
    run_team_update()


def run(
    interval_minutes: int,
    max_runs: int,
    retry_attempts: int,
    retry_backoff_seconds: int,
    quality_mode: str | None,
    run_contact: bool,
    skip_preflight: bool,
    skip_endpoint_check: bool,
    continue_on_failure: bool,
    lock_path: str,
    stale_lock_minutes: int,
    scheduler_log_path: str,
) -> int:
    lock = Path(lock_path)
    scheduler_log = Path(scheduler_log_path)

    _acquire_lock(lock, stale_lock_minutes=stale_lock_minutes)
    try:
        run_index = 0
        while True:
            run_index += 1
            started = _utc_now()

            retry_result = _run_with_retries(
                task=lambda: _run_pipeline_cycle(
                    quality_mode=quality_mode,
                    run_contact=run_contact,
                    skip_preflight=skip_preflight,
                    skip_endpoint_check=skip_endpoint_check,
                ),
                attempts=retry_attempts,
                backoff_seconds=retry_backoff_seconds,
            )

            ended = _utc_now()
            duration_ms = int((ended - started).total_seconds() * 1000)

            event = {
                "run_index": run_index,
                "started_at_utc": started.isoformat(),
                "ended_at_utc": ended.isoformat(),
                "duration_ms": duration_ms,
                "ok": retry_result.ok,
                "attempts_used": retry_result.attempts,
                "last_error": retry_result.last_error,
                "quality_mode": quality_mode or "default",
                "run_contact": run_contact,
                "skip_preflight": skip_preflight,
                "skip_endpoint_check": skip_endpoint_check,
            }
            _append_scheduler_event(scheduler_log, event)

            if not retry_result.ok and not continue_on_failure:
                return 2

            if max_runs > 0 and run_index >= max_runs:
                return 0 if retry_result.ok else 2

            if interval_minutes <= 0:
                return 0 if retry_result.ok else 2

            time.sleep(max(1, interval_minutes * 60))
    finally:
        _release_lock(lock)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run scheduled pipeline with reliability guardrails.")
    parser.add_argument(
        "--interval-minutes",
        type=int,
        default=60,
        help="Minutes between runs (default: 60).",
    )
    parser.add_argument(
        "--max-runs",
        type=int,
        default=1,
        help="Maximum runs before exit (default: 1). Use 0 for continuous mode.",
    )
    parser.add_argument(
        "--retry-attempts",
        type=int,
        default=3,
        help="Attempt count per cycle on failure (default: 3).",
    )
    parser.add_argument(
        "--retry-backoff-seconds",
        type=int,
        default=20,
        help="Base retry backoff seconds, multiplied by attempt number.",
    )
    parser.add_argument(
        "--quality-mode",
        choices=["open", "balanced", "strict"],
        help="Optional quality mode override for scheduled runs.",
    )
    parser.add_argument(
        "--run-contact-discovery",
        action="store_true",
        help="Also run contact and LinkedIn discovery each cycle.",
    )
    parser.add_argument(
        "--skip-preflight",
        action="store_true",
        help="Skip preflight check before each cycle.",
    )
    parser.add_argument(
        "--skip-endpoint-check",
        action="store_true",
        help="Skip endpoint reachability check during preflight.",
    )
    parser.add_argument(
        "--continue-on-failure",
        action="store_true",
        help="Continue scheduling even after a failed cycle.",
    )
    parser.add_argument(
        "--lock-path",
        default="outputs/scheduler.lock",
        help="Scheduler lock file path.",
    )
    parser.add_argument(
        "--stale-lock-minutes",
        type=int,
        default=240,
        help="Treat lock as stale after this many minutes (default: 240).",
    )
    parser.add_argument(
        "--scheduler-log-path",
        default="outputs/day2_scheduler_log.jsonl",
        help="Path to scheduler event log (jsonl).",
    )
    args = parser.parse_args()

    return run(
        interval_minutes=args.interval_minutes,
        max_runs=args.max_runs,
        retry_attempts=args.retry_attempts,
        retry_backoff_seconds=args.retry_backoff_seconds,
        quality_mode=args.quality_mode,
        run_contact=args.run_contact_discovery,
        skip_preflight=args.skip_preflight,
        skip_endpoint_check=args.skip_endpoint_check,
        continue_on_failure=args.continue_on_failure,
        lock_path=args.lock_path,
        stale_lock_minutes=args.stale_lock_minutes,
        scheduler_log_path=args.scheduler_log_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
