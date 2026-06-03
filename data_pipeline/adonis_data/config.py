"""Environment and shared configuration helpers."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    serper_api_key: str
    newsapi_api_key: str
    request_timeout_seconds: int = 20
    recency_days: int = 90
    dedup_days: int = 30
    post_signals_enabled: bool = False
    signals_endpoint_url: str = ""
    signals_endpoint_token: str = ""
    outbox_enabled: bool = True
    outbox_dir: str = "outputs/outbox"
    noise_guard_enabled: bool = True
    noise_keywords: tuple[str, ...] = ()
    allowlist_enabled: bool = True
    allowlist_domains: tuple[str, ...] = ()
    allowlist_sources: tuple[str, ...] = ()
    executive_brief_min_confidence: float = 0.70
    executive_brief_max_items: int = 3
    executive_brief_include_urgent_override: bool = True
    pdf_ingestion_enabled: bool = True
    pdf_max_words: int = 3000
    replay_max_attempts: int = 3
    replay_backoff_seconds: int = 2
    linkedin_min_match_score: float = 0.20
    linkedin_recommended_match_score: float = 0.75


def load_settings() -> Settings:
    load_dotenv()

    serper_api_key = os.getenv("SERPER_API_KEY", "").strip()
    newsapi_api_key = os.getenv("NEWSAPI_API_KEY", "").strip()
    recency_days = int(os.getenv("RECENCY_DAYS", "90").strip() or "90")
    dedup_days = int(os.getenv("DEDUP_DAYS", "30").strip() or "30")
    post_signals_enabled = os.getenv("POST_SIGNALS_ENABLED", "false").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    signals_endpoint_url = os.getenv("SIGNALS_ENDPOINT_URL", "").strip()
    signals_endpoint_token = os.getenv("SIGNALS_ENDPOINT_TOKEN", "").strip()
    request_timeout_seconds = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20").strip() or "20")
    outbox_enabled = os.getenv("OUTBOX_ENABLED", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    outbox_dir = os.getenv("OUTBOX_DIR", "outputs/outbox").strip() or "outputs/outbox"
    noise_guard_enabled = os.getenv("NOISE_GUARD_ENABLED", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    raw_noise_keywords = os.getenv(
        "NOISE_KEYWORDS",
        "tracker,live updates,deals tracker,layoffs,newsletter roundup",
    )
    noise_keywords = tuple(
        keyword.strip().lower() for keyword in raw_noise_keywords.split(",") if keyword.strip()
    )
    allowlist_enabled = os.getenv("ALLOWLIST_ENABLED", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    raw_allowlist_domains = os.getenv(
        "ALLOWLIST_DOMAINS",
        "nyp.org,umassmemorial.org,modernhealthcare.com,fiercehealthcare.com,beckershospitalreview.com",
    )
    allowlist_domains = tuple(
        domain.strip().lower() for domain in raw_allowlist_domains.split(",") if domain.strip()
    )
    raw_allowlist_sources = os.getenv(
        "ALLOWLIST_SOURCES",
        "NewYork-Presbyterian,UMass Memorial,Modern Healthcare,Fierce Healthcare,Becker's Hospital Review",
    )
    allowlist_sources = tuple(
        source.strip().lower() for source in raw_allowlist_sources.split(",") if source.strip()
    )
    executive_brief_min_confidence = float(
        os.getenv("EXECUTIVE_BRIEF_MIN_CONFIDENCE", "0.70").strip() or "0.70"
    )
    executive_brief_max_items = int(os.getenv("EXECUTIVE_BRIEF_MAX_ITEMS", "3").strip() or "3")
    executive_brief_include_urgent_override = os.getenv(
        "EXECUTIVE_BRIEF_INCLUDE_URGENT_OVERRIDE", "true"
    ).strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    pdf_ingestion_enabled = os.getenv("PDF_INGESTION_ENABLED", "true").strip().lower() in {
        "1",
        "true",
        "yes",
        "on",
    }
    pdf_max_words = int(os.getenv("PDF_MAX_WORDS", "3000").strip() or "3000")
    replay_max_attempts = int(os.getenv("REPLAY_MAX_ATTEMPTS", "3").strip() or "3")
    replay_backoff_seconds = int(os.getenv("REPLAY_BACKOFF_SECONDS", "2").strip() or "2")
    linkedin_min_match_score = float(
        os.getenv("LINKEDIN_MIN_MATCH_SCORE", "0.20").strip() or "0.20"
    )
    linkedin_recommended_match_score = float(
        os.getenv("LINKEDIN_RECOMMENDED_MATCH_SCORE", "0.75").strip() or "0.75"
    )

    if not serper_api_key:
        raise ValueError("Missing SERPER_API_KEY. Add it to data_pipeline/.env.")
    if not newsapi_api_key:
        raise ValueError("Missing NEWSAPI_API_KEY. Add it to data_pipeline/.env.")

    return Settings(
        serper_api_key=serper_api_key,
        newsapi_api_key=newsapi_api_key,
        request_timeout_seconds=request_timeout_seconds,
        recency_days=recency_days,
        dedup_days=dedup_days,
        post_signals_enabled=post_signals_enabled,
        signals_endpoint_url=signals_endpoint_url,
        signals_endpoint_token=signals_endpoint_token,
        outbox_enabled=outbox_enabled,
        outbox_dir=outbox_dir,
        noise_guard_enabled=noise_guard_enabled,
        noise_keywords=noise_keywords,
        allowlist_enabled=allowlist_enabled,
        allowlist_domains=allowlist_domains,
        allowlist_sources=allowlist_sources,
        executive_brief_min_confidence=executive_brief_min_confidence,
        executive_brief_max_items=executive_brief_max_items,
        executive_brief_include_urgent_override=executive_brief_include_urgent_override,
        pdf_ingestion_enabled=pdf_ingestion_enabled,
        pdf_max_words=pdf_max_words,
        replay_max_attempts=replay_max_attempts,
        replay_backoff_seconds=replay_backoff_seconds,
        linkedin_min_match_score=linkedin_min_match_score,
        linkedin_recommended_match_score=linkedin_recommended_match_score,
    )
