# Adonis Frontend Data Contract for Juan

Date: 2026-06-01
Producer: Michael data pipeline outputs + Joel API
Consumer: Juan dashboard views

## Purpose

Define minimal response shapes Juan can build against now, before full classifier integration.

## Dashboard Signal Feed Contract

Recommended endpoint:

- GET /signals?ae_id={id}&tier={optional}

Response shape:

- signals: array
  - id: string
  - hospital_name: string
  - title: string
  - one_sentence_summary: string
  - source_name: string
  - source_url: string
  - published_at: string
  - tier: string
  - signal_type: string
  - confidence_score: number or null
  - matched_topics: string[]

Temporary mapping until classifier is live:

- one_sentence_summary <- excerpt
- tier <- worth_knowing
- signal_type <- inferred from matched_topics first item, else unknown
- confidence_score <- null

## Hospital Sidebar Contract

Recommended endpoint:

- GET /hospitals?ae_id={id}

Response shape:

- hospitals: array
  - id: string
  - name: string
  - signal_count_last_run: integer

Current counts from latest run:

- NewYork-Presbyterian: 5
- UMass Memorial: 6

## Hospital Profile Contract

Recommended endpoint:

- GET /hospital-profile?hospital_id={id}

Response shape:

- hospital:
  - id: string
  - name: string
  - website_url: string
- contacts: array
  - id: string
  - full_name: string
  - role: string
  - prior_employer: string
  - linkedin_url: string
  - linkedin_verified: boolean
- recent_signals: array (same shape as feed item)

Note:

- contacts are not ingested yet in this pipeline milestone.
- Juan can scaffold table states and empty-state copy now.

## Admin Metrics Card Contract

Recommended endpoint:

- GET /runs/latest

Response shape:

- run_at_utc: string
- articles_found: integer
- stored_candidates: integer
- skipped_count: integer
- skip_reasons: object map string->integer
- recency_days: integer
- dedup_days: integer

Current values for design/testing:

- articles_found: 20
- stored_candidates: 11
- skipped_count: 9
- skip_reasons.outside_recency_window: 9
- recency_days: 365
- dedup_days: 30

## UI Guidance for Current Data

1. Treat tier as provisional until rules engine + classifier arrive.
2. Display published_at as raw text with fallback Unknown date.
3. Always render source link button when source_url exists.
4. Add a small badge Provisional Data on cards until classification fields are live.

## Immediate Integration Plan

1. Juan builds signal card component against the response shape above.
2. Joel serves temporary mapping from current stored raw fields.
3. Michael continues producing stable raw inputs per run.
4. Team swaps provisional fields with classifier outputs in next milestone.
