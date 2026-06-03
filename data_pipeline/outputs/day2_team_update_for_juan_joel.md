# Adonis Data Update for Juan and Joel

Date: 2026-06-01
Owner: Michael

## Status

Data pipeline run completed successfully with tuned recency filtering.

## Current Metrics

- Articles found: 20
- Stored candidates: 11
- Skipped: 9
- Skip reasons:
  - outside_recency_window: 9
- Recency window: 365 days
- Dedup window: 30 days

## Hospital Coverage

- NewYork-Presbyterian: 5 candidates
- UMass Memorial: 6 candidates

## What Changed

- Added deduplication (source URL and title+hospital window).
- Added configurable recency filter.
- Added quality log and handoff reporting outputs.
- Added provisional classification (signal_type, tier, confidence) to unblock integration while waiting for full Claude path.
- Added structured run log output with rules-engine hit counts and duration.

## Artifacts

- Handoff summary: outputs/day2_handoff_summary.md
- Quality log JSON: outputs/day2_signal_quality_log.json
- Signal summary CSV: outputs/day2_signal_summary.csv
- Raw signal payload: outputs/day1_raw_signals.json
- Classified candidates: outputs/day2_classified_candidates.json
- Run log: outputs/day2_run_log.json

## Notes for Integration

- Candidates are raw signals only and are ready for the next step: rules-engine plus classifier.
- API contract can use current JSON payload shape while backend endpoints are finalized.
