"""Extract leadership contact leads from classified signal text."""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ContactLead:
    full_name: str
    hospital: str
    role_hint: str
    source_title: str


ROLE_PATTERNS: tuple[str, ...] = (
    "CEO",
    "CFO",
    "CRO",
    "CRCO",
    "Chief Revenue Officer",
    "Chief Financial Officer",
    "Chief Executive Officer",
    "VP Revenue Cycle",
    "Vice President Revenue Cycle",
)

_STOP_NAMES = {
    "New York",
    "Health Care",
    "Revenue Cycle",
    "United States",
}

_BAD_NAME_TOKENS = {
    "healthcare",
    "health",
    "supply",
    "chain",
    "clinical",
    "collaboration",
    "tracker",
    "updates",
    "deals",
    "no",
    "rank",
    "ranks",
    "gorilla",
    "epic",
    "new",
    "york",
    "reveals",
    "how",
    "willy",
    "wonka",
}

_CONTACT_SIGNAL_MARKERS = (
    "ceo",
    "cfo",
    "cro",
    "chief",
    "vp revenue cycle",
    "vice president",
    "named",
    "appointed",
    "joins",
    "step down",
    "resign",
)


def _extract_name_candidates(text: str) -> list[str]:
    # Capture simple First Last patterns from signal titles.
    matches = re.findall(r"\b([A-Z][a-z]+ [A-Z][a-z]+)\b", text)
    return [m.strip() for m in matches if m.strip() and m.strip() not in _STOP_NAMES]


def _extract_role_adjacent_names(text: str) -> list[str]:
    role_pattern = r"(?:CEO|CFO|CRO|CRCO|Chief [A-Za-z ]+|VP Revenue Cycle|Vice President Revenue Cycle)"
    patterns = [
        rf"{role_pattern}[^A-Za-z]+([A-Z][a-z]+ [A-Z][a-z]+)",
        rf"([A-Z][a-z]+ [A-Z][a-z]+)\s+Named\s+{role_pattern}",
        rf"([A-Z][a-z]+ [A-Z][a-z]+),\s+{role_pattern}",
    ]
    results: list[str] = []
    for pattern in patterns:
        for match in re.findall(pattern, text):
            results.append(match.strip())
    return results


def _is_person_like(full_name: str) -> bool:
    parts = full_name.split()
    if len(parts) != 2:
        return False

    lowered = [part.lower() for part in parts]
    if any(part in _BAD_NAME_TOKENS for part in lowered):
        return False

    return all(part.isalpha() and len(part) >= 2 for part in parts)


def _looks_like_contact_signal(title: str) -> bool:
    lowered = title.lower()
    return any(marker in lowered for marker in _CONTACT_SIGNAL_MARKERS)


def _role_hint(title: str) -> str:
    lowered = title.lower()
    for role in ROLE_PATTERNS:
        if role.lower() in lowered:
            return role
    return "leadership"


def extract_contact_leads(classified_signals: list[dict[str, object]]) -> list[ContactLead]:
    leads: list[ContactLead] = []
    seen: set[tuple[str, str]] = set()

    for signal in classified_signals:
        title = str(signal.get("title", "")).strip()
        hospital = str(signal.get("hospital", "")).strip()
        if not title or not hospital:
            continue

        if not _looks_like_contact_signal(title):
            continue

        name_candidates = _extract_role_adjacent_names(title)
        if not name_candidates:
            name_candidates = _extract_name_candidates(title)

        hint = _role_hint(title)
        for full_name in name_candidates:
            if not _is_person_like(full_name):
                continue

            key = (full_name.lower(), hospital.lower())
            if key in seen:
                continue
            seen.add(key)
            leads.append(
                ContactLead(
                    full_name=full_name,
                    hospital=hospital,
                    role_hint=hint,
                    source_title=title,
                )
            )

    return leads
