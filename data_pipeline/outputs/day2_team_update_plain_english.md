# Teammate Update (Plain English)

Generated: 2026-06-06T17:20:19.941485+00:00

## What We Completed

- The pipeline run finished successfully across 5 hospitals in 7782 ms.
- It found 51 source articles and kept 9 candidate signals after filtering.
- The rules engine auto-prioritized 3 signals before fallback classification.
- Summary quality mode used this run: balanced.

## Quality and Filtering

- 42 signals were skipped for quality/duplication/recency reasons.
- Top skip reason: duplicate_source_url = 22
- Top skip reason: outside_recency_window = 11
- Top skip reason: no_topic_match = 5
- Top skip reason: noise_not_hospital_specific = 4

## Contact Lead QA

- Total leads identified: 13
- Recommended for manual review: 7
- Rejected low-confidence matches: 4

## Delivery Status

- Delivery enabled in this run: True
- Delivery completed in this run: True

## Blockers

- No config blocker detected for HOSPITAL_ID_MAP.

## Useful Artifacts

- Status snapshot: outputs/day2_status_snapshot.md
- Handoff summary: outputs/day2_handoff_summary.md
- Run log: outputs/day2_run_log.json
- Delivery status: outputs/day2_delivery_status.json
- Contact lead review: outputs/day2_contact_leads_review.md
