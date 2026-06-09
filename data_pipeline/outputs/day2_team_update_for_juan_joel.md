# Adonis Data Update for Juan and Joel

Date: 2026-06-04
Owner: Michael

## Status

Pipeline run completed and live endpoint delivery is now validated in production test flow.

## Current Metrics

- Hospitals checked: 2
- Articles found: 20
- Classified candidates: 6
- Signals new: 6
- Signals skipped: 14
- Rules-engine hits: 3
- Run duration: 4966 ms

## Skip Breakdown

- no_topic_match: 2
- noise_not_hospital_specific: 3
- outside_recency_window: 8
- duplicate_source_url: 1

## Delivery Validation (Joel Endpoint)

- Delivery enabled: true
- Endpoint configured: true
- HTTP status: 200
- Delivered: true
- Signals in payload: 6
- API response: inserted=2, duplicates=4, rejected=0
- Outbox file: outputs/outbox/20260604T155651Z_signal_batch.json

## Daily Diff

- New: 6
- Removed: 4
- Unchanged: 0
- Tier changed: 0

## Executive Brief Summary

- Threshold: 0.70
- Max items: 3
- Included: 3
- Excluded below threshold: 0
- Excluded by max items: 3

## Artifacts

- Handoff summary: outputs/day2_handoff_summary.md
- Run log: outputs/day2_run_log.json
- Delivery status: outputs/day2_delivery_status.json
- Ingest payload example: outputs/day2_signal_ingest_example_payload.json
- Classified candidates: outputs/day2_classified_candidates.json
- Contact lead review: outputs/day2_contact_leads_review.md
- Client preview (light): outputs/day2_client_feed_preview.html
- Client preview (dark): outputs/day2_client_feed_preview_dark.html

## Notes for Integration

- Endpoint contract and auth path are confirmed operational with POST delivery.
- Duplicate handling is working server-side (source_url + hospital_id conflict path).
- Outbox remains enabled as fallback for replay/recovery.
