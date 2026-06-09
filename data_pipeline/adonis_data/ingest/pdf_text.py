"""PDF text ingestion helpers for filing-style sources."""

from __future__ import annotations

from io import BytesIO

import pdfplumber
import requests


def extract_pdf_text(url: str, timeout_seconds: int = 20, max_words: int = 3000) -> str:
    response = requests.get(url, timeout=timeout_seconds)
    response.raise_for_status()

    chunks: list[str] = []
    with pdfplumber.open(BytesIO(response.content)) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            if text.strip():
                chunks.append(text.strip())

    full_text = "\n".join(chunks)
    words = full_text.split()
    if len(words) > max_words:
        return " ".join(words[:max_words])
    return full_text
