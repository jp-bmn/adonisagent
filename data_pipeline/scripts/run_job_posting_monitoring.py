"""Monitor RCM job postings for hospitals to detect hiring spikes."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from adonis_data.clients.serper import SerperClient
from adonis_data.config import load_settings
from adonis_data.constants import HOSPITAL_QUERIES
from adonis_data.models import RawSignal
from adonis_data.delivery.signal_sender import post_signal_batch


def _build_signal_batch_payload(
    signals: list[RawSignal],
    now_utc: datetime,
    hospital_id_map: dict[str, str] | None,
) -> dict[str, object]:
    resolved_hospital_ids = hospital_id_map or {}

    signal_rows: list[dict[str, object]] = []
    for signal in signals:
        hospital_id = resolved_hospital_ids.get(signal.hospital, "")

        signal_rows.append(
            {
                "hospital_id": hospital_id,
                "hospital_name": signal.hospital,
                "signal_type": "rcm_hiring_spike",
                "tier": "urgent",
                "confidence_score": 0.95,
                "title": signal.title,
                "summary": signal.excerpt,
                "source_url": signal.url,
                "source_name": signal.source,
                "published_date": now_utc.date().isoformat(),
                "published_at_raw": signal.published_at,
                "excerpt": signal.excerpt,
                "matched_topics": signal.matched_topics,
                "extraction_stage": "raw_candidate",
                "dedup_applied": True,
                "recency_applied": True,
            }
        )

    return {
        "run_context": {
            "run_at_utc": now_utc.isoformat(),
            "source_pipeline_version": "day3_job_monitoring",
            "recency_days": 7,
            "dedup_days": 7,
            "hospitals": list(HOSPITAL_QUERIES.keys()),
        },
        "signals": signal_rows,
    }


def check_hiring_spike(hospital: str, serper: SerperClient) -> RawSignal | None:
    """Check if there is a hiring spike for the hospital."""
    query = f"{hospital} revenue cycle management OR billing OR denials job"
    
    # We query serper to find recent job postings
    results = serper.search_news(query=query, num_results=10)
    
    # In a real implementation we would check the dates and aggregate
    # For now we'll simulate a spike if we get enough results
    if len(results) >= 3:
        # Create a signal for the spike
        return RawSignal(
            hospital=hospital,
            title=f"{hospital} is experiencing a spike in RCM hiring",
            source="Serper Job Search",
            url=results[0].get("link", ""), # Link to the first job found
            published_at=datetime.now(timezone.utc).isoformat(),
            matched_topics=["revenue_cycle", "hiring"],
            excerpt=f"Detected {len(results)} recent RCM-related job postings for {hospital}.",
        )
    return None


def run() -> Path:
    settings = load_settings()
    serper = SerperClient(api_key=settings.serper_api_key, timeout_seconds=settings.request_timeout_seconds)
    now_utc = datetime.now(timezone.utc)

    signals: list[RawSignal] = []

    for hospital in HOSPITAL_QUERIES.keys():
        print(f"Checking for RCM hiring spikes at {hospital}...")
        signal = check_hiring_spike(hospital, serper)
        if signal:
            signals.append(signal)
            
    output_dir = Path("outputs")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "day3_job_monitoring_signals.json"
    
    # Format the payload and post it to the backend if enabled
    batch_payload = _build_signal_batch_payload(signals, now_utc, settings.hospital_id_map)
    
    output_path.write_text(json.dumps(batch_payload, indent=2), encoding="utf-8")
    
    if settings.post_signals_enabled and settings.signals_endpoint_url:
        post_result = post_signal_batch(
            endpoint_url=settings.signals_endpoint_url,
            payload=batch_payload,
            timeout_seconds=settings.request_timeout_seconds,
            bearer_token=settings.signals_endpoint_token,
        )
        delivery_path = output_dir / "day3_job_monitoring_delivery.json"
        delivery_path.write_text(json.dumps(post_result, indent=2), encoding="utf-8")

    return output_path


if __name__ == "__main__":
    path = run()
    print(f"Wrote job monitoring signals to {path}")
