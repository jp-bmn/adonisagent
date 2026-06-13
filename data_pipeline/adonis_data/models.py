"""Domain models used by ingestion and extraction steps."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class RawSignal:
    hospital: str
    title: str
    source: str
    url: str
    published_at: str
    matched_topics: list[str]
    excerpt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
