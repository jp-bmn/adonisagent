| Adonis Account Intelligence Tool Internal Build PRD · v4 · Sprint to June 18, 2026 Owner: Joel Philip · Team: Juan Franco, Michael Chabler Client: Adonis AI (Reed Kalash) · Demo Day: June 24, 2026 |
| ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| ⚠ TEAM RULE — SCOPE BOUNDARIES ARE HARD. Your IDE must not auto-generate or suggest code in another team member's layer. Before pushing any branch, review every file changed. If a file does not belong to your layer, revert it. Overlapping changes are the primary source of CI failures and merge conflicts on this project. |
| :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

# **1\. Purpose & Scope**

This document defines all work required to reach build-complete status by June 18, 2026 — six days before Demo Day. It supersedes the sprint columns in v3 and incorporates feedback from the June 9 Reed demo. Every item is assigned to exactly one owner. If a task is not assigned to you, do not touch it.

| Build-complete means: all 19 backend tasks passing, all dashboard views functional, co-pilot (Hermes) responding with live signal context, and all 5 hospitals scraped and classified with valid data. |
| :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

# **2\. Team Roles & Layer Ownership**

Each team member owns a defined layer of the stack. Do not write, suggest, or merge code outside your layer without explicit agreement from the owner of that layer.

| Person                        | Layer                                                        | Files / Directories You Own                                                 | Do Not Touch                                      |
| :---------------------------- | :----------------------------------------------------------- | :-------------------------------------------------------------------------- | :------------------------------------------------ |
| **Joel Philip(Project Lead)** | Python FastAPI backendAgent orchestrationSlack delivery      | apps/api/\*\*app/services/\*\*app/routers/\*\*app/models/\*\*railway config | apps/web/\*\*scrapers/\*\*pnpm-workspace.yaml     |
| **Juan Franco**               | Next.js 14 frontendDashboard UIHermes co-pilot UI            | apps/web/\*\*components/\*\*app/api/copilot/route.ts                        | apps/api/\*\*app/services/\*\*supabase migrations |
| **Michael Chabler**           | Web scrapersSignal extractionPDF ingestionLinkedIn discovery | scrapers/\*\*scripts/ingestion/\*\*data pipelines                           | apps/web/\*\*app/routers/\*\*Slack bot files      |

# **3\. Reed Demo Feedback (June 9\) — What Must Change**

The following items came directly from Reed's review. All must be resolved before June 18\.

| Feedback Item                                                                              | Owner    | Action Required                                                                                                                                                                                |
| :----------------------------------------------------------------------------------------- | -------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Signal summaries are scraped first lines — Reed wants AI-generated 2-sentence summaries    | **Joel** | Claude classifier must generate a 2-sentence summary field before writing to DB. Michael's scraper provides raw text; Joel's classifier produces the summary.                                  |
| Stories should default to urgency sort, with toggle to change (hospital name, most recent) | **Juan** | Add sort toggle to signal feed. Default: urgency tier (urgent first). Toggle options: Most Recent, Hospital Name (A–Z). State persists per session.                                            |
| "AMS" abbreviation appearing in upper-right — cause unknown, must be investigated          | **Juan** | Identify the source of the AMS label. Likely a hardcoded string or API field rendering incorrectly. Fix or remove.                                                                             |
| Signal cards need category tags visible on each card                                       | **Juan** | Render signal_type as a visible pill/tag on each signal card (e.g. "Leadership Change", "M\&A Acquisition"). Use existing signal_type field from API.                                          |
| A general CIO article is being tagged to UAMS even when UAMS is not specifically mentioned | **Joel** | Tighten hospital attribution logic in the classifier. Hospital must be explicitly and actively discussed — not merely referenced once in passing. Add confidence penalty for weak attribution. |

# **4\. Open Bugs — All Must Be Resolved by June 18**

## **4.1 pnpm Lockfile Out of Sync \[Juan\]**

The CI pipeline fails with ERR_PNPM_OUTDATED_LOCKFILE because @anthropic-ai/sdk was added to apps/web/package.json but is not used — the Hermes co-pilot route calls the Anthropic API via raw fetch.

**Fix:**

- Remove @anthropic-ai/sdk from apps/web/package.json

- Run pnpm install at the monorepo root

- Commit the updated pnpm-lock.yaml

- Confirm CI passes before merging

## **4.2 null review_status Filtering Out New Signals \[Joel\]**

New signals arrive from the scraper with review_status \= null. The /signals endpoint filters these by default, causing the signal feed to show 0 results. The current frontend workaround (include_dismissed=true) is not acceptable long-term.

**Fix:**

- Update the /signals endpoint query to treat review_status \= null as equivalent to pending

- Include null-status signals in the default response without requiring any flag

- Verify with the existing test suite — no new behavior should break approved/dismissed logic

## **4.3 ANTHROPIC_API_KEY Missing on Railway \[Joel\]**

The Hermes co-pilot returns a silent error in production because the API key is not set in the Railway environment. The route at apps/web/src/app/api/copilot/route.ts checks for this key on every request.

**Fix:**

- Add ANTHROPIC_API_KEY to the Railway deployment environment variables (key shared in Slack)

- Redeploy and confirm the co-pilot returns a response in the production environment

# **5\. Joel — Backend Tasks (June 10–18)**

These are the only files Joel should be modifying. All tasks must have passing tests before the June 18 cutoff.

| \#       | Task                                        | Acceptance Criteria                                                                                                                                                                   | Priority    |
| :------- | :------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------- |
| **B-01** | Bug Fix: null review_status filter          | GET /signals returns null-status signals in default response. No include_dismissed flag required. All existing tests still pass.                                                      | **BLOCKER** |
| **B-02** | Add ANTHROPIC_API_KEY to Railway env        | POST /api/v1/copilot returns a valid Claude response in production. Hermes chat bubble works end-to-end.                                                                              | **BLOCKER** |
| **B-03** | AI-generated 2-sentence summaries           | Claude classifier writes a summary field (2 sentences max) into the signals table on every classification run. Field is not a scraped first line.                                     | **HIGH**    |
| **B-04** | Tighter hospital attribution in classifier  | Signals are only attributed to a hospital if the hospital is explicitly and centrally discussed in the article. Add confidence penalty logic for weak attribution. Reduce false tags. | **HIGH**    |
| **B-05** | Hospital staff profiles — contacts endpoint | GET /api/v1/hospitals/{id}/contacts returns full contact records (name, role, prior_employer, linkedin_url, linkedin_verified). Territory auth enforced.                              | **HIGH**    |
| **B-06** | Review queue feedback loop — thumbs up/down | POST /signals/{id}/review accepts approved / dismissed. Dismissed signals are logged. Approval patterns feed back to classifier confidence thresholds over time.                      | **HIGH**    |
| **B-07** | Scraper usefulness range toggles            | Backend exposes configurable threshold params (min confidence, signal age window, tier filter) that the admin can set. Stored in config table or environment.                         | **MEDIUM**  |
| **B-08** | Urgent alert Slack DM                       | When a signal is classified as urgent, a Slack DM fires immediately to the relevant AE. Max 1 urgent DM per hospital per day enforced.                                                | **HIGH**    |
| **B-09** | CSV export endpoint                         | GET /api/v1/contacts/export returns a CSV of all contacts scoped to the requesting AE's territory.                                                                                    | **MEDIUM**  |
| **B-10** | agent_runs logging                          | Every scraper run writes a record to agent_runs: hospitals_checked, signals_found, signals_new, errors, duration_ms.                                                                  | **MEDIUM**  |

# **6\. Juan — Frontend Tasks (June 10–18)**

Juan owns apps/web/\*\* exclusively. Do not modify any backend Python files, Supabase migration files, or Railway configuration.

| \#       | Task                                              | Acceptance Criteria                                                                                                                                                                  | Priority    |
| :------- | :------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **F-01** | Bug Fix: pnpm lockfile — remove @anthropic-ai/sdk | Remove package from apps/web/package.json. Run pnpm install. Commit updated lockfile. CI passes.                                                                                     | **BLOCKER** |
| **F-02** | Investigate and fix 'AMS' label in upper-right    | Identify source of AMS string. Either render correct value from API or remove. No unexplained abbreviations visible in the UI.                                                       | **BLOCKER** |
| **F-03** | Rename CoPilot → Hermes everywhere                | Chat bubble label reads 'Hermes'. Chat header reads 'Hermes'. No instances of 'CoPilot' remain in the UI.                                                                            | **HIGH**    |
| **F-04** | Category tags on signal cards                     | Each signal card displays a pill showing its signal_type (e.g. 'Leadership Change', 'M\&A'). Uses existing signal_type field. Color-coded by tier.                                   | **HIGH**    |
| **F-05** | Sort toggle on signal feed                        | Default sort is urgency (urgent first, then worth_knowing). Toggle allows switching to Most Recent or Hospital Name A–Z. State persists per session.                                 | **HIGH**    |
| **F-06** | Category filter on signal feed                    | Dropdown or chip filter allows rep to filter feed by one or more signal_type values. Integrates with existing territory filter.                                                      | **HIGH**    |
| **F-07** | TerritorySelector component                       | Dropdown reads AE list from /hospitals. Shows all AEs plus 'All accounts'. Updating selection filters signal feed via ae_id query param. Replaces hardcoded 'Admin (Danielle)' chip. | **HIGH**    |
| **F-08** | Hermes: inject live signal context                | copilot/route.ts fetches latest 50 signals from Railway API on each request. Formats them into a readable summary and injects into Claude system prompt. Responses are signal-aware. | **HIGH**    |
| **F-09** | Review queue UI — thumbs up/down                  | Admin dashboard shows pending signals. Each card has approve / dismiss controls that call POST /signals/{id}/review. Dismissed count visible to admin.                               | **MEDIUM**  |
| **F-10** | Hospital staff profiles view                      | Clicking a hospital reveals a contacts tab with profile cards: name, role, prior employer, LinkedIn URL (shown as link). Data from GET /hospitals/{id}/contacts.                     | **HIGH**    |
| **F-11** | CSV export button                                 | Admin view has an 'Export Contacts' button that calls GET /contacts/export and triggers a CSV download.                                                                              | **MEDIUM**  |
| **F-12** | UTM tracking — digest view capture                | Dashboard captures utm_source, utm_medium, digest_id on page load and POSTs to /digest-view. 'Last viewed' timestamp visible per AE in admin panel.                                  | **MEDIUM**  |

# **7\. Michael — Data Tasks (June 10–18)**

Michael owns all scraper logic, signal ingestion pipelines, and LinkedIn discovery. Do not modify app/routers, app/services, or any frontend files.

| \#       | Task                                                    | Acceptance Criteria                                                                                                                                                                                 | Priority    |
| :------- | :------------------------------------------------------ | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| **D-01** | 3+ validated signals per hospital, all 5 hospitals      | Each hospital (NewYork-Presbyterian, UMass Memorial, Ascension, UAMS, Jefferson Health) has at least 3 signals in the DB with real source URLs, correct signal_type, and confidence_score ≥ 0.75.   | **BLOCKER** |
| **D-02** | Stricter attribution — hospital must be central subject | Scraper pre-filter: discard articles where the hospital appears only once or only as a passing reference. Articles must be primarily about the hospital. Coordinate with Joel on classifier tuning. | **HIGH**    |
| **D-03** | LinkedIn URL discovery for contacts                     | For each contact in the contacts table, attempt LinkedIn URL discovery. Populate linkedin_url. Set linkedin_verified \= false. Do not connect to HubSpot.                                           | **HIGH**    |
| **D-04** | PDF ingestion — SEC 8-K and IRS 990                     | When serper.dev returns a .pdf URL, pipeline runs extract_pdf_text() via pdfplumber before sending to classification. Extracted text stored and classified correctly.                               | **HIGH**    |
| **D-05** | Vendor / AI adoption signal coverage                    | Scrapers actively surface vendor_change, ai_adoption_outside_rcm, and automation_proof signals across all 5 hospital accounts. At least 1 of each type in the DB.                                   | **MEDIUM**  |
| **D-06** | Signal quality validation — no false positives          | Review all signals currently in DB. Remove or re-classify any that are misattributed (hospital mentioned once or not the central subject). Work with Joel on confidence threshold.                  | **HIGH**    |
| **D-07** | CommonSpirit — hold until Danielle confirms             | Do not build or run any CommonSpirit scraper until Danielle confirms which division David targets. Flag in Slack if confirmation is not received by June 13\.                                       | **NOTE**    |

# **8\. Cross-Team Dependencies**

These handoffs require explicit communication before the receiving owner can proceed. Do not assume the upstream task is done — confirm in Slack.

| Dependency                                                 | Producer    | Consumer | Handoff Requirement                                                                                                                                                                |
| :--------------------------------------------------------- | ----------- | -------- | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 2-sentence AI summary field in DB                          | **Joel**    | **Juan** | Joel confirms summary column is populated for all existing signals. Juan then renders it on signal cards — no changes to the API contract needed.                                  |
| null review_status bug fix                                 | **Joel**    | **Juan** | Joel deploys the fix to Railway. Juan removes the include_dismissed=true workaround from all frontend API calls.                                                                   |
| Contacts endpoint live on Railway                          | **Joel**    | **Juan** | Joel confirms GET /hospitals/{id}/contacts returns data in production. Juan builds the staff profiles tab against that endpoint.                                                   |
| Review queue POST /signals/{id}/review endpoint            | **Joel**    | **Juan** | Joel confirms endpoint is live and returns 200\. Juan wires approve/dismiss buttons to it.                                                                                         |
| Signal data quality (3+ per hospital, correct attribution) | **Michael** | **Joel** | Michael pushes clean signals via batch endpoint. Joel confirms classifier is receiving and processing them correctly. Both verify DB state together.                               |
| Raw article text from scraper for summarization            | **Michael** | **Joel** | Michael's batch payload must include the raw article body (or a full excerpt) so Joel's classifier can generate the 2-sentence summary. Agree on field name before implementation. |

# **9\. June 18 — Definition of Done**

Build-complete is declared when every item below is true simultaneously. Each owner is responsible for self-verifying their items and confirming in the team Slack channel.

| Owner       | Criterion                                                                                        | Done? |
| ----------- | :----------------------------------------------------------------------------------------------- | ----- |
| **Joel**    | All backend tasks B-01 through B-10 pass. Test suite at 100% (target: 200+ tests).               | \[ \] |
| **Joel**    | Railway production URL returns healthy responses on all 16 core endpoints.                       | \[ \] |
| **Joel**    | null review_status bug is fixed and include_dismissed workaround is no longer needed.            | \[ \] |
| **Joel**    | Claude classifier generates 2-sentence summaries for all new signals.                            | \[ \] |
| **Joel**    | Hospital attribution tightened — no signals tagged to hospitals they don't clearly cover.        | \[ \] |
| **Joel**    | Urgent Slack DMs fire correctly for tier=urgent signals. Max 1 per hospital per day enforced.    | \[ \] |
| **Juan**    | All frontend tasks F-01 through F-12 are complete. CI is green on Juan's branch.                 | \[ \] |
| **Juan**    | pnpm lockfile is clean. @anthropic-ai/sdk removed. No frozen-lockfile CI errors.                 | \[ \] |
| **Juan**    | CoPilot label is removed everywhere. Hermes label is correct in bubble and chat header.          | \[ \] |
| **Juan**    | Signal cards show category pill tags and sort toggle works correctly.                            | \[ \] |
| **Juan**    | TerritorySelector replaces hardcoded Danielle chip. AE selection filters the feed.               | \[ \] |
| **Juan**    | Hermes returns signal-aware responses — fetches 50 signals and injects into system prompt.       | \[ \] |
| **Michael** | All 5 hospitals have 3+ validated signals in the DB with real source URLs.                       | \[ \] |
| **Michael** | No misattributed signals — each signal's hospital is clearly the primary subject of the article. | \[ \] |
| **Michael** | LinkedIn URLs populated for all contacts currently in the DB.                                    | \[ \] |
| **Michael** | PDF ingestion pipeline is operational for SEC 8-K and IRS 990 documents.                         | \[ \] |
| **All**     | main branch is stable. No failing CI checks. No merge conflicts open.                            | \[ \] |
| **All**     | Demo script rehearsed. All 6 demo-day criteria from the project context pass end-to-end.         | \[ \] |

# **10\. Scope Freeze**

The following items are explicitly out of scope for the June 18 build-complete milestone. They are planned but will not block Demo Day.

- **CommonSpirit scraper:** Paused. Do not build until Danielle confirms which division David targets.

- **HubSpot integration:** Tool outputs CSV only. No direct HubSpot API connection will be built.

- **Hermes email drafting:** Co-pilot chat only. No outreach email generation.

- **New signal searches via Hermes:** Hermes queries stored signals only. It does not trigger new scraper runs.

- **Jefferson Health:** Pending formal confirmation from Danielle. Do not build scrapers.

# **11\. Key Dates**

| Date              | Milestone                                                                                                                 |
| :---------------- | :------------------------------------------------------------------------------------------------------------------------ |
| **June 10, 2026** | This PRD distributed. Blockers B-01, B-02, F-01, F-02 begin today.                                                        |
| **June 13, 2026** | Mid-sprint check. All BLOCKER items resolved. Cross-team handoffs confirmed in Slack. Michael's signal quality validated. |
| **June 18, 2026** | **BUILD COMPLETE. All 18 definition-of-done criteria met. main is stable. Debug week begins.**                            |
| **June 18–23**    | Debug week. Bug fixes, load testing, demo script rehearsal, data freshness check.                                         |
| **June 24, 2026** | **DEMO DAY. Pursuit L3 AI Native Demo Day. Production stable. Dashboard at full fidelity. Data current as of June 23\.**  |

Adonis Account Intelligence Tool · Internal Build PRD v4 · INTERNAL — NOT FOR CLIENT DISTRIBUTION
