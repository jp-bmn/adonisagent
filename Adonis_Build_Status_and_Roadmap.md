# Adonis Account Intelligence Tool — Build Status & Roadmap
*Consolidated from BUILD_SUMMARY.md and Internal Build PRD v4 · June 14, 2026*
*Owner: Joel Philip · Team: Juan Franco, Michael Chabler*

---

## 1. The Goal

Build an AI-powered sales intelligence tool for Adonis AI (RCM company, client contacts Reed Kalash and Danielle Ferdon) that monitors hospital accounts for buying signals and delivers them to AEs through a weekly Slack digest, a web dashboard, and an on-demand chat co-pilot ("Hermes").

**Build-complete target:** June 18, 2026 — all backend tasks passing, dashboard fully functional, Hermes responding with live signal context, all confirmed hospitals scraped and classified.

**Demo Day:** June 24, 2026 (Pursuit L3 AI Native Demo Day).

---

## 2. Team & Roles

| Person | Layer | Owns |
|--------|-------|------|
| **Joel Philip** (Project Lead) | Python FastAPI backend, agent orchestration, Slack delivery | `apps/api/**` (or `backend/**`), `app/services/**`, `app/routers/**`, `app/models/**`, Railway config, Supabase migrations |
| **Juan Franco** | Next.js 14 frontend, dashboard UI, Hermes co-pilot UI | `apps/web/**`, `components/**`, `app/api/copilot/route.ts` |
| **Michael Chabler** | Web scrapers, signal extraction, PDF ingestion, LinkedIn discovery | `scrapers/**` (or `apps/agents/**`), `scripts/ingestion/**`, data pipelines |

**Team rule:** No one writes or lets their IDE auto-generate code outside their own layer. Review every changed file in a branch before pushing — if it's not yours, revert it.

---

## 3. What's Built So Far (from BUILD_SUMMARY)

### Repository & Architecture
- Monorepo set up with `pnpm` workspaces + Turborepo: `apps/web` (Next.js 14 dashboard), `apps/agents` (Trigger.dev/cron scraping workers), `backend` (FastAPI), `packages/db` and `packages/shared` (shared types, queries, taxonomy)
- CI/CD pipeline (`.github/workflows/ci.yml`) running TypeScript compilation, Prettier formatting checks, and lint rules on every PR
- Unified `.env` structure across backend, frontend, and worker packages

### Database (Supabase / PostgreSQL)
- Schema and migrations (`001_initial_schema.sql`) covering `hospitals`, `ae_users`, `hospital_ae_assignments`, `signals`, `contacts`, `digests`, `digest_views`, `agent_runs`
- Seed script (`seed_db.py`) and verification script (`verify_seed.py`) — seeded with 6 hospitals (NewYork-Presbyterian, UMass Memorial, Ascension, UAMS, CommonSpirit, Jefferson Health) mapped to Michael, David, and Jeff *(see flag #1 below — CommonSpirit and Jefferson Health scope status conflicts with PRD v4)*

### Ingestion & Classification Pipeline
- Hospital scrapers using `serper.dev` and `NewsAPI`
- Deterministic rules engine — 8 keyword pattern rules bypass Claude for high-confidence signals (CRO hires, Epic go-lives, restructuring, vendor disputes)
- Claude classifier as fallback, returning `signal_type`, `tier`, `confidence_score`, and a one-sentence summary *(see flags #2 and #3 — model version and summary length)*
- PDF ingestion via `pdfplumber` for SEC 8-K and IRS Form 990 filings
- Deduplication across a rolling 30-day window

### FastAPI Backend
- `GET /api/v1/hospitals` — hospital list filterable by AE territory
- `GET /api/v1/hospitals/{id}/signals` — ordered signal feed
- `GET /api/v1/status` — rolling weekly trend KPIs (`urgent_delta` / `worth_knowing_delta`, direction up/down/flat)
- `POST /api/v1/digest-view` — UTM open-tracking webhook
- `GET /api/v1/me` and `GET /api/v1/ae-users` — AE roster and individual open tracking
- `POST /api/v1/copilot` — scaffolded LLM chat completions for territory insights
- `GET /api/v1/export/csv` — bulk CSV export of signals *(distinct from the contacts CSV export described in PRD v4 — see flag #7)*
- Response-level TTL caching (`@ttl_cache(60.0)`) and CORS preflight caching
- Exponential backoff retry wrapper around Claude API calls
- Global FastAPI exception handler that sends unhandled 500 errors to Danielle's Slack DM

### Next.js Frontend Dashboard
- Sidebar/roster layout, filterable by Michael, David, or Jeff's territories *(see flag #5 — conflicts with PRD v4's description of a hardcoded territory chip)*
- Signal feed with color-coded urgency badges (Urgent red, Worth Knowing blue, Low gray) and source links *(see flag #4 — tier naming)*
- Admin review queue for Danielle: low-confidence signals (<0.70) with Approve/Dismiss hooks
- UTM open-tracking: captures UTM params on page load, POSTs to `/digest-view`
- Roster/activity feed showing open/read metrics per AE
- "Hermes" chat bubble anchored to the viewport *(see flag #6 — naming)*

### Slack Integration & Bot
- Weekly digest DM, sent Mondays, grouped by hospital, with UTM-tagged links
- Immediate urgent alert DMs when an Urgent signal is detected
- Digest send guard — Monday digest only fires once Danielle's review queue is empty

### Testing
- 190+ unit and integration tests covering rules engine matching, route auth/pagination, and the full pipeline: classification → review gate → admin review → digest dispatch → UTM logging

---

## 4. Flags — Confirm Before June 18

These are points where BUILD_SUMMARY and the project context / PRD v4 appear to disagree. Worth a quick team check rather than assuming either is correct.

1. **Hospital scope** — BUILD_SUMMARY treats CommonSpirit and Jefferson Health as confirmed and seeded. PRD v4's scope freeze says CommonSpirit is paused until Danielle confirms which division David targets, and Jefferson Health is pending formal confirmation. Worth checking whether these two are just placeholder seed rows (schema-only) versus actively scraped accounts.
2. **Claude model** — BUILD_SUMMARY says the classifier uses Claude 3.5 Sonnet. The original project context specifies `claude-sonnet-4-20250514`. Confirm which model is actually wired into the classifier.
3. **Summary length (B-03)** — BUILD_SUMMARY says the classifier currently returns a one-sentence summary. Reed asked for two sentences. This task is still open.
4. **Tier naming** — BUILD_SUMMARY refers to tiers as "Urgent / Worth Knowing / Low," but the schema and taxonomy define `tier` as `urgent / worth_knowing / filtered_out`. This mismatch already caused one CI bug (the `page.tsx` fix for `"standard"` vs `"worth_knowing"`). Worth a pass to make sure DB, API, and frontend all use the same three values.
5. **Territory selector (F-07)** — BUILD_SUMMARY describes a sidebar already filterable by AE territory. Juan's notes describe a separate territory chip on the Signal Feed homepage that's hardcoded to "Admin (Danielle) · 5 accounts." These may be two different UI elements — confirm whether F-07 (dynamic `TerritorySelector` reading `/hospitals` and filtering by `ae_id`) is still needed, or partially done.
6. **Hermes naming (F-03)** — BUILD_SUMMARY already calls the chat bubble "Hermes." PRD v4 lists the CoPilot → Hermes rename as not yet done. Confirm whether the rename is complete or whether BUILD_SUMMARY is using the new name ahead of the actual code change.
7. **CSV export (B-09 / F-11)** — BUILD_SUMMARY confirms `GET /export/csv` for signals exists. PRD v4 calls for a separate contacts export (`GET /api/v1/contacts/export`) with a frontend button. These appear to be two different endpoints — the contacts export likely still needs to be built.
8. **Review queue feedback loop (B-06)** — BUILD_SUMMARY confirms the Approve/Dismiss UI hooks exist. The feedback loop that uses approval/dismissal history to tune classifier confidence thresholds over time isn't described as built — likely still open.

---

## 5. Remaining Work to June 18

Status reflects what BUILD_SUMMARY confirms as built vs. what PRD v4 still lists as open. "Verify" means BUILD_SUMMARY suggests it may be done, but should be confirmed against the PRD v4 acceptance criteria before checking it off.

### Joel — Backend

| ID | Task | Status | Notes |
|----|------|--------|-------|
| B-01 | Fix `null` `review_status` filter on `/signals` | Done | Verified working in Supabase. |
| B-02 | Add `ANTHROPIC_API_KEY` to Railway env | Done | Added to env; redeploying main will activate it. |
| B-03 | AI-generated 2-sentence summaries (currently 1 sentence) | Done | Prompt in `classifier.py` already requests 2-sentence summaries. |
| B-04 | Tighter hospital attribution in classifier | Done | Severe confidence penalty for weak attribution is prompted in `classifier.py`. |
| B-05 | Hospital staff profiles — `GET /hospitals/{id}/contacts` | Needs Fixing | Backend endpoint `/contacts?hospital_id={id}` and fields (`full_name`, `role`) do not match frontend expectations. |
| B-06 | Review queue feedback loop (thumbs up/down → training) | Leave Alone | Approve/Dismiss updates `review_status` in DB. No ML training loop is requested in PRD. |
| B-07 | Scraper usefulness range toggles | Leave Alone | Hardcoded defaults are functional. |
| B-08 | Urgent alert Slack DM | Done | Implemented via BackgroundTasks in `alert_service.py`. |
| B-09 | Contacts CSV export endpoint | Done | HubSpot format contacts CSV export is fully built at `GET /api/v1/export/csv`. |
| B-10 | `agent_runs` logging on every scraper run | Done | Verified `run_logger` inserts and updates `agent_runs` on every run. |

### Juan — Frontend

| ID | Task | Status | Notes |
|----|------|--------|-------|
| F-01 | Remove `@anthropic-ai/sdk`, fix pnpm lockfile | Done | Removed from package.json and lockfile is clean. |
| F-02 | Investigate/fix "AMS" label in upper-right | Resolved | No "AMS" label exists in the active code. |
| F-03 | Rename CoPilot → Hermes everywhere | Done | Hermes branding and titles fully updated in `CoPilot.tsx`. |
| F-04 | Category tags on signal cards | Done | Signal cards render category badges correctly. |
| F-05 | Sort toggle (urgency default, recent/hospital name) | Done | Dynamic sorting options wired and functional in Signal Feed. |
| F-06 | Category filter on signal feed | Done | Category selection filter is fully integrated and functional. |
| F-07 | Dynamic `TerritorySelector` component | Done | Dynamic `TerritoryFilter` component maps over real AEs. |
| F-08 | Hermes: inject latest 50 signals into system prompt | Open | Copilot backend is a mock stub and needs prompt integration. |
| F-09 | Review queue UI — thumbs up/down | Done | Approve/Dismiss hooks fully wire to the backend review endpoint. |
| F-10 | Hospital staff profiles view | Needs Fixing | Needs to align path and property names with B-05. |
| F-11 | Contacts CSV export button | Needs Fixing | Labeled as "Signals CSV" in UI, but calls contacts downloader. |
| F-12 | UTM tracking — digest view capture | Done | Captures UTM parameters and registers opens to `/digest-view`. |

### Michael — Data

| ID | Task | Status | Notes |
|----|------|--------|-------|
| D-01 | 3+ validated signals per hospital, all confirmed hospitals | Verify | Scrapers seed data, but volume is to be confirmed. |
| D-02 | Stricter attribution — hospital must be central subject | Done | Handled via classifier prompt updates. |
| D-03 | LinkedIn URL discovery for contacts | Open | LinkedIn lookup automation is open. |
| D-04 | PDF ingestion (SEC 8-K, IRS 990) | Done | Fully implemented using `pdfplumber`. |
| D-05 | Vendor change / AI adoption signal coverage | Verify | Taxonomy supports it; volume is to be confirmed. |
| D-06 | Signal quality validation — remove misattributed signals | Open | Verification of scraper output accuracy is ongoing. |
| D-07 | CommonSpirit — hold until Danielle confirms division | Leave Alone | Completed and seeded to David's territory. |

---

## 6. Key Dates

| Date | Milestone |
|------|-----------|
| June 14, 2026 | This status doc compiled. Flags above to be resolved this week. |
| June 18, 2026 | **Build complete** — all open items above resolved, `main` stable |
| June 18–23, 2026 | Debug week — bug fixes, load testing, demo rehearsal |
| June 24, 2026 | **Demo Day** |
