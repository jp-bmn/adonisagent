# Adonis - Integration Instructions for Joel

Date: 2026-06-01
From: Michael

## What Is Ready On My Side

1. Pipeline collects and filters raw signal candidates.
2. Batch payload is generated every run at:
   - outputs/day2_signal_ingest_example_payload.json
3. Optional sender is implemented and tested (POST delivery works).
4. Delivery result is logged every run at:
   - outputs/day2_delivery_status.json
   - outputs/day2_run_log.json
5. Outbox queue is active, so payloads are safely queued while waiting for your URL:
   - outputs/outbox
6. Contact lead triage output is generated each run for manual validation:
   - outputs/day2_contact_leads.json
   - outputs/day2_contact_leads_review.md
   - outputs/day2_contact_leads_review.csv
   - Low-score filtered candidates are captured under `rejected_matches` in outputs/day2_contact_leads.json

## What I Need From You

1. A stub ingestion endpoint URL for testing (example: https://<host>/signals/batch).
2. Auth requirement details:
   - If bearer token is required, share token format and scope.
3. Expected response shape for success and validation errors.

## Endpoint Contract I Implemented

POST payload top-level fields:

1. run_context
2. signals

Each signal includes:

1. hospital_name
2. title
3. source_name
4. source_url
5. published_at_raw
6. excerpt
7. matched_topics
8. extraction_stage
9. dedup_applied
10. recency_applied

Reference doc:

- outputs/day2_backend_ingestion_contract_joel.md

## How I Will Hit Your Stub Once You Share URL

I will set in my local .env:

1. POST_SIGNALS_ENABLED=true
2. SIGNALS_ENDPOINT_URL=<your_stub_url>
3. SIGNALS_ENDPOINT_TOKEN=<optional_if_required>
4. REQUEST_TIMEOUT_SECONDS=20

Then run:

1. source .venv/bin/activate
2. python -m scripts.run_day1_collection
3. python -m scripts.replay_outbox (flushes queued payloads)

## What We Will Validate Together

1. HTTP status is 200/201.
2. Your API receives all sent signals.
3. Your response includes inserted/duplicate/rejected counts.
4. Delivery log on my side shows delivered=true.
5. Lead review queue keeps only above-threshold LinkedIn candidates (low-score URLs are auto-cleared).

## Artifacts To Review

1. outputs/day2_team_update_for_juan_joel.md
2. outputs/day2_handoff_summary.md
3. outputs/day2_signal_quality_log.json
4. outputs/day2_signal_summary.csv
5. outputs/day2_backend_ingestion_contract_joel.md
6. outputs/day2_signal_ingest_example_payload.json
7. outputs/day2_contact_leads_review.md
8. outputs/day2_contact_leads_review.csv
9. outputs/day2_contact_leads.json (see rejected_matches section)
