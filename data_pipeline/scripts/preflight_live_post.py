"""Preflight checks for safe live posting from the data pipeline.

This script validates local configuration before running live batch delivery.
It does not post any signals.
"""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import requests

from adonis_data.config import load_settings
from adonis_data.constants import HOSPITAL_QUERIES


@dataclass(frozen=True)
class CheckResult:
    level: str
    name: str
    detail: str


def _upsert_env_values_missing_only(env_path: Path, defaults: dict[str, str]) -> list[str]:
    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    changed: list[str] = []
    for key, value in defaults.items():
        line_value = f"{key}={value}"
        replaced = False
        for index, current in enumerate(lines):
            if current.startswith(f"{key}="):
                _ = index
                replaced = True
                break
        if not replaced:
            if lines and lines[-1].strip() != "":
                lines.append("")
            lines.append(line_value)
            changed.append(key)

    if changed:
        env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    return changed


def _maybe_apply_autofix(autofix_env: bool, env_path: str) -> CheckResult | None:
    if not autofix_env:
        return None

    # Only write non-secret, conservative defaults. Never auto-fill credentials.
    defaults = {
        "POST_SIGNALS_ENABLED": "false",
        "OUTBOX_ENABLED": "true",
        "REQUEST_TIMEOUT_SECONDS": "20",
        "QUALITY_MODE": "balanced",
    }
    changed = _upsert_env_values_missing_only(Path(env_path), defaults)
    if changed:
        return CheckResult(
            "PASS",
            "env_autofix",
            f"Updated {env_path}: {', '.join(changed)}",
        )

    return CheckResult("PASS", "env_autofix", f"No updates needed in {env_path}")


def _parse_hospital_id_map(raw_value: str) -> dict[str, str]:
    if not raw_value.strip():
        return {}

    try:
        payload: Any = json.loads(raw_value)
    except json.JSONDecodeError:
        return {}

    if not isinstance(payload, dict):
        return {}

    parsed: dict[str, str] = {}
    for hospital_name, hospital_id in payload.items():
        key = str(hospital_name).strip()
        value = str(hospital_id).strip()
        if key and value:
            parsed[key] = value
    return parsed


def _mask_token(token: str) -> str:
    if not token:
        return "(empty)"
    if len(token) <= 6:
        return "***"
    return f"{token[:3]}...{token[-3:]}"


def _check_endpoint_reachable(endpoint_url: str, token: str, timeout_seconds: int) -> CheckResult:
    if not endpoint_url:
        return CheckResult("FAIL", "endpoint_reachability", "SIGNALS_ENDPOINT_URL is empty")

    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.options(endpoint_url, headers=headers, timeout=timeout_seconds)
        # 2xx/4xx both prove reachability here; network failure is what we care about.
        if 200 <= response.status_code < 500:
            return CheckResult(
                "PASS",
                "endpoint_reachability",
                f"OPTIONS {endpoint_url} reachable (status={response.status_code})",
            )
        return CheckResult(
            "WARN",
            "endpoint_reachability",
            f"OPTIONS {endpoint_url} returned status={response.status_code}",
        )
    except requests.RequestException as exc:
        return CheckResult(
            "FAIL",
            "endpoint_reachability",
            f"Could not reach endpoint: {exc}",
        )


def run(check_endpoint: bool = True, autofix_env: bool = False, env_path: str = ".env") -> int:
    autofix_result = _maybe_apply_autofix(autofix_env=autofix_env, env_path=env_path)
    settings = load_settings()

    results: list[CheckResult] = []
    if autofix_result is not None:
        results.append(autofix_result)

    if settings.post_signals_enabled:
        results.append(CheckResult("PASS", "post_signals_enabled", "POST_SIGNALS_ENABLED=true"))
    else:
        results.append(
            CheckResult(
                "FAIL",
                "post_signals_enabled",
                "POST_SIGNALS_ENABLED=false (live posting is currently disabled)",
            )
        )

    if settings.quality_mode in {"open", "balanced", "strict"}:
        results.append(
            CheckResult(
                "PASS",
                "quality_mode_used",
                f"QUALITY_MODE={settings.quality_mode}",
            )
        )
    else:
        results.append(
            CheckResult(
                "WARN",
                "quality_mode_used",
                f"Unexpected QUALITY_MODE={settings.quality_mode}; expected open|balanced|strict",
            )
        )

    if settings.signals_endpoint_url:
        results.append(
            CheckResult(
                "PASS",
                "signals_endpoint_url",
                f"Configured: {settings.signals_endpoint_url}",
            )
        )
    else:
        results.append(CheckResult("FAIL", "signals_endpoint_url", "SIGNALS_ENDPOINT_URL is empty"))

    if settings.signals_endpoint_token:
        results.append(
            CheckResult(
                "PASS",
                "signals_endpoint_token",
                f"Configured token: {_mask_token(settings.signals_endpoint_token)}",
            )
        )
    else:
        results.append(
            CheckResult(
                "WARN",
                "signals_endpoint_token",
                "SIGNALS_ENDPOINT_TOKEN is empty (request may be rejected by backend)",
            )
        )

    if settings.outbox_enabled:
        results.append(CheckResult("PASS", "outbox_enabled", "OUTBOX_ENABLED=true"))
    else:
        results.append(
            CheckResult(
                "WARN",
                "outbox_enabled",
                "OUTBOX_ENABLED=false (failed posts will not be queued for replay)",
            )
        )

    raw_hospital_id_map = os.getenv("HOSPITAL_ID_MAP", "")
    parsed_hospital_id_map = _parse_hospital_id_map(raw_hospital_id_map)

    if raw_hospital_id_map and not parsed_hospital_id_map:
        results.append(
            CheckResult(
                "FAIL",
                "hospital_id_map_json",
                "HOSPITAL_ID_MAP is present but not valid JSON object",
            )
        )
    elif parsed_hospital_id_map:
        results.append(
            CheckResult(
                "PASS",
                "hospital_id_map_json",
                f"HOSPITAL_ID_MAP contains {len(parsed_hospital_id_map)} entries",
            )
        )
    else:
        results.append(CheckResult("FAIL", "hospital_id_map_json", "HOSPITAL_ID_MAP is empty"))

    expected_hospitals = list(HOSPITAL_QUERIES.keys())
    missing_hospitals = [h for h in expected_hospitals if h not in parsed_hospital_id_map]
    if missing_hospitals:
        results.append(
            CheckResult(
                "FAIL",
                "hospital_id_map_coverage",
                "Missing IDs for: " + ", ".join(missing_hospitals),
            )
        )
    else:
        results.append(
            CheckResult(
                "PASS",
                "hospital_id_map_coverage",
                "Hospital ID map covers all configured hospitals",
            )
        )

    if check_endpoint:
        results.append(
            _check_endpoint_reachable(
                endpoint_url=settings.signals_endpoint_url,
                token=settings.signals_endpoint_token,
                timeout_seconds=settings.request_timeout_seconds,
            )
        )

    print("Live Post Preflight")
    print("=" * 20)
    for result in results:
        print(f"[{result.level}] {result.name}: {result.detail}")

    fail_count = sum(1 for result in results if result.level == "FAIL")
    warn_count = sum(1 for result in results if result.level == "WARN")

    print("\nSummary")
    print(f"- fail_count: {fail_count}")
    print(f"- warn_count: {warn_count}")

    if fail_count:
        print("- readiness: BLOCKED")
        return 2

    if warn_count:
        print("- readiness: READY_WITH_WARNINGS")
        return 1

    print("- readiness: READY")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight checks for live signal posting.")
    parser.add_argument(
        "--skip-endpoint-check",
        action="store_true",
        help="Skip network reachability check for SIGNALS_ENDPOINT_URL.",
    )
    parser.add_argument(
        "--autofix-env",
        action="store_true",
        help="Opt-in: write non-secret conservative defaults to .env before checks.",
    )
    parser.add_argument(
        "--env-path",
        default=".env",
        help="Path to .env file used when --autofix-env is enabled.",
    )
    args = parser.parse_args()
    return run(
        check_endpoint=not args.skip_endpoint_check,
        autofix_env=args.autofix_env,
        env_path=args.env_path,
    )


if __name__ == "__main__":
    raise SystemExit(main())
