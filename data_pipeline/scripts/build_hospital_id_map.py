"""Fetch hospital UUIDs from API and optionally persist HOSPITAL_ID_MAP in .env."""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path
from typing import Any

import requests

from adonis_data.constants import HOSPITAL_QUERIES


HOSPITAL_NAME_ALIASES: dict[str, tuple[str, ...]] = {
    "NewYork-Presbyterian": (
        "new york presbyterian",
        "new york-presbyterian",
        "nyp",
    ),
    "UMass Memorial": (
        "umass memorial health",
        "umass",
    ),
    "Ascension": (
        "ascension health",
    ),
    "University of Arkansas": (
        "uams",
        "uams medical center",
        "university of arkansas medical sciences",
        "university of arkansas for medical sciences",
        "university of arkansas medical center",
    ),
    "CommonSpirit": (
        "commonspirit health",
        "common spirit",
        "common spirit health",
    ),
}


def _normalize_name(name: str) -> str:
    lowered = name.strip().lower()
    # Fold punctuation and extra separators so naming variants map consistently.
    cleaned = re.sub(r"[^a-z0-9]+", " ", lowered)
    return " ".join(cleaned.split())


def _extract_rows(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [row for row in payload if isinstance(row, dict)]

    if isinstance(payload, dict):
        for key in ("hospitals", "data", "items", "results"):
            rows = payload.get(key)
            if isinstance(rows, list):
                return [row for row in rows if isinstance(row, dict)]

    return []


def _build_id_map(rows: list[dict[str, Any]]) -> dict[str, str]:
    targets = list(HOSPITAL_QUERIES.keys())
    target_lookup: dict[str, str] = {_normalize_name(name): name for name in targets}

    for canonical_name, aliases in HOSPITAL_NAME_ALIASES.items():
        for alias in aliases:
            target_lookup[_normalize_name(alias)] = canonical_name

    discovered: dict[str, str] = {}
    for row in rows:
        name = str(row.get("name") or row.get("hospital_name") or "").strip()
        hospital_id = str(row.get("id") or row.get("hospital_id") or "").strip()
        if not name or not hospital_id:
            continue

        canonical = target_lookup.get(_normalize_name(name))
        if canonical:
            discovered[canonical] = hospital_id

    return discovered


def _collect_unmatched_names(rows: list[dict[str, Any]]) -> list[str]:
    targets = list(HOSPITAL_QUERIES.keys())
    target_lookup: dict[str, str] = {_normalize_name(name): name for name in targets}
    for canonical_name, aliases in HOSPITAL_NAME_ALIASES.items():
        for alias in aliases:
            target_lookup[_normalize_name(alias)] = canonical_name

    unmatched: set[str] = set()
    for row in rows:
        name = str(row.get("name") or row.get("hospital_name") or "").strip()
        if not name:
            continue
        if _normalize_name(name) not in target_lookup:
            unmatched.add(name)

    return sorted(unmatched)


def _upsert_env_map(env_path: Path, hospital_id_map: dict[str, str]) -> None:
    serialized = json.dumps(hospital_id_map, separators=(",", ":"))
    line = f"HOSPITAL_ID_MAP={serialized}"

    if env_path.exists():
        lines = env_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    replaced = False
    for index, current in enumerate(lines):
        if current.startswith("HOSPITAL_ID_MAP="):
            lines[index] = line
            replaced = True
            break

    if not replaced:
        if lines and lines[-1].strip() != "":
            lines.append("")
        lines.append(line)

    env_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build HOSPITAL_ID_MAP from live API.")
    parser.add_argument(
        "--api-base-url",
        default=os.getenv("API_BASE_URL", "https://adonisagents-production.up.railway.app/api/v1"),
        help="Base API URL (default: Railway production API).",
    )
    parser.add_argument(
        "--user-id",
        default=os.getenv("X_USER_ID", "").strip(),
        help="AE user UUID used for X-User-Id header.",
    )
    parser.add_argument(
        "--bearer-token",
        default=os.getenv("SIGNALS_ENDPOINT_TOKEN", "").strip(),
        help="Optional bearer token for Authorization header.",
    )
    parser.add_argument(
        "--write-env",
        action="store_true",
        help="Write HOSPITAL_ID_MAP into .env.",
    )
    parser.add_argument(
        "--env-path",
        default=".env",
        help="Path to .env file when using --write-env.",
    )
    args = parser.parse_args()

    if not args.user_id:
        raise SystemExit(
            "Missing user id. Provide --user-id <uuid> or set X_USER_ID in environment."
        )

    base = args.api_base_url.rstrip("/")
    url = f"{base}/hospitals"
    headers = {"X-User-Id": args.user_id}
    if args.bearer_token:
        headers["Authorization"] = f"Bearer {args.bearer_token}"

    response = requests.get(
        url,
        headers=headers,
        params={"ae_id": args.user_id},
        timeout=30,
    )

    try:
        response.raise_for_status()
    except requests.HTTPError as exc:
        detail = response.text.strip()
        if len(detail) > 400:
            detail = detail[:400] + "..."

        if response.status_code == 401:
            hint = (
                "Unauthorized (401). The endpoint likely requires a bearer token. "
                "Set SIGNALS_ENDPOINT_TOKEN in .env or pass --bearer-token <token>."
            )
        else:
            hint = f"Request failed with status {response.status_code}."

        raise SystemExit(f"{hint}\nURL: {response.url}\nResponse: {detail}") from exc

    payload = response.json()
    rows = _extract_rows(payload)
    if not rows:
        raise SystemExit("Could not parse hospital rows from API response.")

    hospital_id_map = _build_id_map(rows)
    unmatched_names = _collect_unmatched_names(rows)
    missing = [name for name in HOSPITAL_QUERIES if name not in hospital_id_map]

    print("Discovered HOSPITAL_ID_MAP:")
    print(json.dumps(hospital_id_map, indent=2))

    if missing:
        print("\nMissing expected hospitals:")
        for name in missing:
            print(f"- {name}")

    if unmatched_names:
        print("\nUnmatched API hospital names (for backend mapping review):")
        for name in unmatched_names:
            print(f"- {name}")

    if args.write_env:
        env_path = Path(args.env_path)
        _upsert_env_map(env_path, hospital_id_map)
        print(f"\nUpdated {env_path} with HOSPITAL_ID_MAP.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
