# Adonis Data Pipeline (Michael)

This folder contains Michael's data-layer build work. The current scope is Week 1 Day 1 setup and first raw signal extraction.

## Day 1 Scope

1. serper.dev and NewsAPI client setup.
2. Query templates for NewYork-Presbyterian and UMass Memorial.
3. RSS ingestion for Becker's Hospital Review, Modern Healthcare, and Fierce Healthcare.
4. First raw signal extraction run to JSON output.

## Setup

1. Create and activate a virtual environment.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

2. Install packages:

```bash
pip install -r requirements.txt
```

3. Copy env template and add keys:

```bash
cp .env.example .env
```

Required keys:

1. `SERPER_API_KEY`
2. `NEWSAPI_API_KEY`

Optional tuning values:

1. `RECENCY_DAYS` (default `90`)
2. `DEDUP_DAYS` (default `30`)
3. `POST_SIGNALS_ENABLED` (default `false`)
4. `SIGNALS_ENDPOINT_URL` (Joel stub URL when available)
5. `SIGNALS_ENDPOINT_TOKEN` (optional bearer token)
6. `REQUEST_TIMEOUT_SECONDS` (default `20`)
7. `OUTBOX_ENABLED` (default `true`)
8. `OUTBOX_DIR` (default `outputs/outbox`)
9. `NOISE_GUARD_ENABLED` (default `true`)
10. `NOISE_KEYWORDS` (comma-separated headline filters)
11. `ALLOWLIST_ENABLED` (default `true`)
12. `ALLOWLIST_DOMAINS` (comma-separated trusted domains)
13. `ALLOWLIST_SOURCES` (comma-separated trusted source names)
14. `EXECUTIVE_BRIEF_MIN_CONFIDENCE` (default `0.70`)
15. `EXECUTIVE_BRIEF_MAX_ITEMS` (default `3`)
16. `EXECUTIVE_BRIEF_INCLUDE_URGENT_OVERRIDE` (default `true`)
17. `PDF_INGESTION_ENABLED` (default `true`)
18. `PDF_MAX_WORDS` (default `3000`)
19. `REPLAY_MAX_ATTEMPTS` (default `3`)
20. `REPLAY_BACKOFF_SECONDS` (default `2`)
21. `LINKEDIN_MIN_MATCH_SCORE` (default `0.20`)
22. `LINKEDIN_RECOMMENDED_MATCH_SCORE` (default `0.75`)
23. `HOSPITAL_ID_MAP` (JSON object mapping hospital name to backend hospital UUID)
24. `QUALITY_MODE` (`open` | `balanced` | `strict`; default `balanced`)

## Run Day 1 Collection

From this directory (`data_pipeline`), run:

```bash
python -m scripts.run_day1_collection
```

Optional per-run override for summary quality behavior:

```bash
python -m scripts.run_day1_collection --quality-mode open
python -m scripts.run_day1_collection --quality-mode balanced
python -m scripts.run_day1_collection --quality-mode strict
```

Run contact and LinkedIn discovery from classified candidates:

```bash
python -m scripts.run_contact_linkedin_discovery
```

Run a one-command refresh for all non-endpoint artifacts:

```bash
python -m scripts.refresh_non_endpoint_artifacts
```

Build `HOSPITAL_ID_MAP` automatically from the live API (requires a valid
`X-User-Id` UUID from Supabase `ae_users`):

```bash
python -m scripts.build_hospital_id_map --user-id <ae_user_uuid> --write-env
```

Run a live posting pass after IDs are set:

```bash
POST_SIGNALS_ENABLED=true OUTBOX_ENABLED=true python -m scripts.run_day1_collection
```

Run preflight checks before posting live batches:

```bash
python -m scripts.preflight_live_post
```

Opt-in env autofix mode (fills missing non-secret conservative defaults only; existing values are preserved):

```bash
python -m scripts.preflight_live_post --autofix-env
```

Generate only the status snapshot and test page:

```bash
python -m scripts.generate_status_snapshot
```

Generate a client-facing feed preview page (from classified signals):

```bash
python -m scripts.generate_client_feed_preview
```

View the test page locally:

1. Open `outputs/day2_test_page.html` in your browser, or
2. Run `python -m http.server 8000` from `data_pipeline` and open:
	- `http://localhost:8000/outputs/day2_test_page.html`
3. Run `python -m scripts.open_test_page` to open it directly (auto-generates the page if missing).

Client preview page:

1. Open `outputs/day2_client_feed_preview.html` in your browser.
2. With local server on port 8000, use:
	- `http://localhost:8000/outputs/day2_client_feed_preview.html`
3. Dark variant:
	- `outputs/day2_client_feed_preview_dark.html`
4. Preserved original light version:
	- `outputs/day2_client_feed_preview_light_v1.html`

Output file:

1. `outputs/day1_raw_signals.json`
2. `outputs/day2_signal_quality_log.json`
3. `outputs/day2_handoff_summary.md`
4. `outputs/day2_signal_summary.csv`
5. `outputs/day2_signal_ingest_example_payload.json`
6. `outputs/day2_delivery_status.json`
7. `outputs/outbox/*_signal_batch.json` (queued payloads)
8. `outputs/day2_classified_candidates.json`
9. `outputs/day2_run_log.json`
10. `outputs/day2_daily_diff.json`
11. `outputs/day2_daily_diff.md`
12. `outputs/day2_executive_brief.md`
13. `outputs/day2_executive_brief_audit.json`
14. `outputs/day2_contact_leads.json`
15. `outputs/day2_contact_leads_review.md`
16. `outputs/day2_contact_leads_review.csv`
17. `outputs/day2_status_snapshot.md`
18. `outputs/day2_test_page.html`
19. `outputs/day2_client_feed_preview.html`
20. `outputs/day2_client_feed_preview_dark.html`
21. `outputs/day2_client_feed_preview_light_v1.html`

## Notes

1. This run intentionally stops at raw candidate extraction.
2. Rules engine, Claude classification, and DB writes are later milestones.
3. The quality log includes counts and skip reasons to support Week 1 signal-quality review.
4. Deduplication applies URL and title+hospital rules with a configurable window.
5. Recency filtering skips parseable items older than the configured recency window.
6. Delivery POST is optional and disabled by default until Joel provides an endpoint URL.
7. When outbox is enabled, each run queues a send-ready payload locally.
8. Provisional classification is included to keep frontend and backend integration moving before Claude integration.
9. Daily diff reports show new, removed, unchanged, and tier-changed signals versus the prior run.
10. Executive brief summarizes top account updates in plain language for quick team sharing.
11. Noise guard removes broad tracker/roundup headlines so reports stay account-specific.
12. Allowlist protects trusted domains/sources from being filtered by noise rules.
13. Executive brief audit records inclusion/exclusion decisions by reason.
14. Broad tracker pages from trusted sources still require explicit target-hospital mention.
15. Provisional confidence applies quality penalties for very short titles/excerpts to reduce weak signal ranking.
16. Executive brief only includes signals at or above the configured confidence threshold.
17. Urgent signals can be force-included in the brief even below threshold when override is enabled.
18. Serper PDF results are parsed with pdfplumber and routed as filing-derived signals.
19. Handoff summary now includes a lead QA snapshot (review counts and top rejected examples) when `outputs/day2_contact_leads.json` is present.
20. Conservative summary quality gate prefers informative one-sentence summaries and avoids ultra-short fragments.

## Replay Outbox Later

Once Joel shares `SIGNALS_ENDPOINT_URL`, you can deliver all queued payloads:

```bash
python -m scripts.replay_outbox
```

Successful replays are renamed from `*_signal_batch.json` to `*_delivered.json`.
Failed replay payloads are moved to `outputs/outbox/failed` with a sidecar error file.

To requeue failed payloads for another replay attempt:

```bash
python -m scripts.requeue_failed_outbox
```

Contact lead output includes `linkedin_match_score`, `match_reason`,
`match_bucket`, and `recommended_for_manual_review` to prioritize manual
verification. A ranked review table is written to
`outputs/day2_contact_leads_review.md` and a CSV queue to
`outputs/day2_contact_leads_review.csv`. LinkedIn URLs below
`LINKEDIN_MIN_MATCH_SCORE` are auto-cleared and captured in
`rejected_matches` inside `outputs/day2_contact_leads.json` for auditability.
