# Adonis Backend Ingestion Contract for Joel

Date: 2026-06-01
Producer: Michael data pipeline
Consumer: Joel FastAPI + Supabase layer

## Purpose

Define the payload Michael sends to Joel for signal storage and run logging.

## Current Source Artifact

- outputs/day1_raw_signals.json
- outputs/day2_signal_quality_log.json

## Endpoint Recommendations

1. POST /signals/batch
- Description: ingest multiple signal candidates from one run.

2. POST /agent-runs
- Description: persist run-level quality and skip metrics.

## POST /signals/batch Request

Top-level object:

- run_context: object
  - run_at_utc: string, ISO-8601
  - source_pipeline_version: string
  - recency_days: integer
  - dedup_days: integer
  - hospitals: string[]
- signals: array of signal objects

Signal object fields:

- hospital_name: string
- title: string
- source_name: string
- source_url: string
- published_at_raw: string
- excerpt: string
- matched_topics: string[]
- extraction_stage: string
- dedup_applied: boolean
- recency_applied: boolean

Example signal mapping from current data:

- hospital_name <- hospital
- source_name <- source
- source_url <- url
- published_at_raw <- published_at

## POST /signals/batch Response

- run_id: string
- received_count: integer
- inserted_count: integer
- duplicate_count: integer
- rejected_count: integer
- rejected: array
  - index: integer
  - reason: string

## POST /agent-runs Request

- run_at_utc: string
- hospitals_checked: integer
- articles_found: integer
- classified_candidates: integer
- signals_new: integer
- signals_skipped: integer
- skip_reasons: object map string->integer
- rules_engine_hits: integer
- duration_ms: integer
- errors: array of strings

Current run values from Michael output:

- hospitals_checked: 2
- articles_found: 20
- classified_candidates: 20
- signals_new: 11
- signals_skipped: 9
- skip_reasons.outside_recency_window: 9
- rules_engine_hits: 0 (not integrated yet)

## Validation Rules

1. Reject signal if source_url is empty.
2. Reject signal if title is empty.
3. Allow published_at_raw as free text for now.
4. Normalize source_url server-side before DB write.
5. Enforce dedup in DB by source_url unique index where possible.

## SQL Alignment Notes

Target PRD table: signals

Populate now:

- hospital_id (resolver from hospital_name)
- title
- summary (from excerpt for now)
- source_url
- source_name
- published_date (nullable parser)
- signal_type (placeholder until classifier)
- tier (placeholder until rules engine/classifier)
- confidence_score (nullable until classifier)
- review_status (nullable until classifier)

## Immediate Integration Plan

1. Joel creates POST /signals/batch stub accepting this shape.
2. Michael adds HTTP sender in next step to call stub.
3. Joel maps to DB with temporary placeholders for classification fields.
4. Team validates one full write/read cycle before midpoint demo.
