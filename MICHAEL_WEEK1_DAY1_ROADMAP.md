# Michael Roadmap - Week 1 Day 1 (Monday)

Date: 2026-06-01
Owner: Michael Chabler (Data)

## Scope For Today (From PRD)

1. Set up serper.dev and NewsAPI integration points.
2. Build test queries for NYP and UMass.
3. Set up RSS ingestion for Becker's Hospital Review.
4. Run first raw signal extraction test and capture outputs.

## Monday Deliverables

1. Data ingestion scaffold committed in this workspace.
2. Working API clients for serper.dev and NewsAPI with shared HTTP handling.
3. RSS ingestion module with source + hospital keyword filtering.
4. Query templates for:
   - NewYork-Presbyterian
   - UMass Memorial
5. Raw signal extraction pipeline that outputs normalized candidate signals to JSON.
6. Setup/run docs and env var template.

## Out Of Scope Today

1. Rules engine integration.
2. Claude classification and confidence scoring.
3. PDF ingestion.
4. LinkedIn discovery.
5. Deduplication and DB writes.

## Build Plan

1. Create Python project skeleton under `data_pipeline`.
2. Add typed clients:
   - `SerperClient`
   - `NewsApiClient`
3. Add RSS fetch + parse module using `feedparser`.
4. Add extraction logic that converts raw items into `RawSignal` objects with:
   - hospital
   - title
   - source
   - url
   - published_at
   - matched_topics
   - excerpt
5. Add a single entry script that runs all three sources and writes:
   - `outputs/day1_raw_signals.json`
6. Document commands and environment variables.

## Risks and Mitigations

1. API keys not present yet.
   - Mitigation: script validates keys and fails with actionable messages.
2. RSS field variability.
   - Mitigation: parser falls back across common fields and handles missing values.
3. Noisy keyword matches.
   - Mitigation: topic keyword map is explicit and easy to tune.

## Definition Of Done For Monday

1. `python -m data_pipeline.scripts.run_day1_collection` works with valid keys.
2. Output JSON contains candidate signals for NYP and/or UMass from at least one source.
3. Code and docs are clear enough to continue Week 1 Tuesday without refactor.
