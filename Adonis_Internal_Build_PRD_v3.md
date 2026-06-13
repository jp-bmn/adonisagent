| INTERNAL Build Plan v3 Post-Midpoint Update | ADONIS ACCOUNT INTELLIGENCE TOOL Sprint to Demo Day June 3, 2026 · 3 weeks remaining · Demo Day June 24 |
| :-----------------------------------------: | :------------------------------------------------------------------------------------------------------ |

| Field                   | Details                                                       |
| :---------------------- | :------------------------------------------------------------ |
| Project lead            | Joel Philip — backend, architecture, Slack, deployment        |
| Frontend                | Juan Franco — dashboard UI, profiles, co-pilot interface      |
| Data                    | Michael Chabler — scrapers, signal extraction, PDF ingestion  |
| Reed meeting (demo)     | Tuesday, June 9, 2026 — working demo required                 |
| Internal build deadline | Wednesday, June 18, 2026 — full build done; debug week starts |
| Demo Day                | Wednesday, June 24, 2026                                      |

| Green light confirmed. Reed said: “Build the damn thing.” The BAA with Claude is signed. Adonis has enterprise API keys with centrally managed tokens. Cost is no longer a constraint. The question now is not what to build — it is how fast we can ship it. |
| :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

**1 · What Changed at the Midpoint Review**

**From the meeting with Reed (June 2\)**

- Claude BAA is signed. Adonis has an enterprise account with centrally managed tokens. Stop worrying about API call volume or cost. Use Sonnet for classification without hesitation. Use it for the co-pilot.

- Reed explicitly confirmed this will be used by his sales team weekly if it works. This is a real product, not a capstone exercise.

- Reed loved the wireframe. His words: “If it looks and works like that, you guys did a great job.” Juan should match that aesthetic exactly.

- Reed wants to expand beyond hospitals — provider groups and customer success are the next segments. The data model should be flexible enough to support that without a rewrite.

- Co-pilot (chat interface) got a green light from both Reed and Greg. It is no longer a stretch feature — it is a committed Phase 3 deliverable.

- Reed confirmed: someone at Adonis will maintain the tool after Demo Day. Write code that another developer can read and extend.

**From the progress report (June 3\)**

- Tasks 1, 2, 3 are done and deployed to Railway. The API is live and functional.

- Unplanned: Michael’s batch ingest endpoint is built, deployed, and tested. Michael can push signals right now.

- Tasks 4 and 5 (Slack bot \+ rules engine) are not started and are blocking everything downstream.

- The June 2 midpoint demo did not happen as planned — the Slack and digest features weren’t ready. The next client demo is June 9 and is a hard commitment.

**2 · Five Improvements Based on the Midpoint Review**

| 1 PRIORITY | Tasks 4 and 5 are the only two blocking the entire backend. Slack bot (Task 4\) and rules engine (Task 5\) should both be done before anything else. Everything — the digest, the classifier, the urgent alerts, the review queue — waits behind these two. Both can be built with no new credentials. Start here. |
| :--------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| 2 CLAUDE | The BAA is signed. API token cost is not a concern anymore. This changes two things: (1) use Claude Sonnet aggressively in the classifier — no need to use Haiku to save tokens; (2) the co-pilot moves from stretch to planned. Juan scaffolds the chat UI; Joel wires in the Claude API. Reed wants it and the keys are coming. |
| :------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| 3 DATA MODEL | Reed said the tool will expand to provider groups and customer success. Add account_type text NOT NULL DEFAULT 'hospital' to the hospitals table right now. It costs 30 seconds and a one-line migration. Retrofitting this after Demo Day when Adonis wants to use it for other segments will be expensive. |
| :----------: | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| 4 JUNE 9 DEMO | The team committed to a working demo on Tuesday June 9\. Be specific about what “working” means: one live Slack DM digest with real signals from Michael’s pipeline, the dashboard rendering signal cards with correct urgency color-coding, and the hospital list loading from the live API. Not everything — just enough to prove the core loop works. |
| :-----------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |

| 5 JUNE 18 DEADLINE | Joel said in the meeting: “I want to make sure we get it done by the 18th.” That leaves June 18–23 as a five-day debug and polish window. The PRD now formalizes June 18 as the internal build-complete deadline. Everything must be merged and working by end of day June 18\. |
| :----------------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |

**3 · Current Status (as of June 3\)**

| Task                                       | Status          | Notes                                                |
| :----------------------------------------- | :-------------- | :--------------------------------------------------- |
| Task 1 — FastAPI skeleton \+ deployment    | **✅ Done**     | Railway live: adonisagents-production.up.railway.app |
| Task 2 — Supabase schema \+ seed data      | **✅ Done**     | 5 hospitals, 4 users, 5 assignments in DB            |
| Task 3 — Core hospital \+ signal endpoints | **✅ Done**     | 16/16 tests passing                                  |
| Bonus — Batch ingest (Michael’s endpoint)  | **✅ Done**     | Unplanned. Fuzzy match, dedup, bearer auth live      |
| Task 4 — Slack bot \+ send_dm()            | **🔴 Blocker**  | Blocks Tasks 8, 14, 16\. Build first.                |
| Task 5 — Rules engine                      | **🔴 Blocker**  | Blocks Task 7 (classifier). No credentials needed.   |
| Task 6 — Trigger.dev scheduler             | **Stub only**   | Admin endpoints exist as stubs                       |
| Task 7 — Claude classifier                 | **Not started** | Needs Tasks 4 \+ 5 first                             |
| Task 8 — Weekly digest formatter           | **Not started** | Needs Tasks 4 \+ 7                                   |
| Tasks 9–19                                 | **Not started** | See revised sprint plan below                        |

Railway API base URL: https://adonisagents-production.up.railway.app/api/v1

Swagger docs: GET /docs · Auth header: X-User-Id: \<ae_user_id_from_supabase\>

Michael’s batch endpoint: POST /api/v1/signals/batch · Bearer token: adonis-internal-dev-key-2026

**4 · Revised Sprint Plan — June 3 to June 24**

Three hard deadlines anchor the plan: June 9 (Reed demo), June 18 (build complete), June 24 (Demo Day). Items marked ◆ are Luminai enhancements.

| Days                              | Joel — Backend                                                                                                                                                                                                                                          | Juan — Frontend                                                                                                                        | Michael — Data                                                                                                                 |
| --------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | :------------------------------------------------------------------------------------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------- |
| **June 3–6**                      | Task 4: Slack bot — send_dm(), format_weekly_digest(), rate limiterTask 5: rules_engine() — all 8 deterministic rules \+ testsMigration: add account_type field to hospitals table                                                                      | Build hospital list page against live APIBuild signal cards (urgency color-coding)Match wireframe dark-teal aesthetic exactly          | Continue scraper pipeline for all 5 hospitalsPush real signals via batch endpoint to populate test data for Juan               |
| **June 9Reed demo**               | Task 7: Claude classifier (rules engine first, then Sonnet fallback)Task 8: Weekly digest — send_weekly_digest_to_all_aes()Demo prep: seed DB, verify live Slack DM fires                                                                               | Dashboard showing live signals from Michael’s dataHospital list sidebar functionalDemo-ready by 9 AM                                   | Signal quality report ready for demoAll 5 hospitals scraped at least onceClassification accuracy validated                     |
| **June 9–13**                     | ◆ Task 9: Signal review \+ approval endpointsTask 10: Territory-filtered API \+ auth middlewareTask 11: Contact storage endpointsTask 12: Run logging \+ GET /status live data                                                                          | ◆ Pending review queue UI (Danielle admin view)Territory-filtered views per AEContact profile displayAdmin ‘Last viewed’ column        | ◆ PDF ingestion (pdfplumber) for SEC \+ IRS filingsLinkedIn URL discovery via serper.devJob posting monitoring queries (basic) |
| **June 13–18**                    | Task 13: CSV export endpointTask 14: Immediate urgent alert DM◆ Task 15: UTM tracking \+ digest_viewsTask 16: Error handling \+ retry logicTask 17: Performance \+ indexesTask 18: Railway production deployTask 19: Monitoring \+ weekly health report | CSV export buttonDashboard polish \+ mobile layout◆ UTM capture → POST /digest-view◆ Co-pilot UI scaffold (Claude Sonnet)Final UX pass | Vendor dispute \+ AI adoption signalsFinal signal taxonomy refinementFalse positive analysis and tuning                        |
| **June 18TARGET: Build complete** | All endpoints liveAll tests passingProduction deploy verified                                                                                                                                                                                           | All dashboard views functionalCo-pilot responding to queries                                                                           | All 5 hospitals scraped \+ classifiedSignal quality validated                                                                  |
| **June 18–23Debug week**          | Bug fixes, edge case handlingLoad test \+ final index tuningDemo script written                                                                                                                                                                         | UI polish, load time optimizationDemo walkthrough rehearsed                                                                            | Data freshness verifiedFull run on all hospitals day before                                                                    |
| **June 24DEMO DAY**               | Production stableAll integrations live                                                                                                                                                                                                                  | Dashboard at full fidelityCo-pilot live                                                                                                | Data current as of June 23                                                                                                     |

**5 · June 9 Demo Scope — What “Working” Means**

Reed committed to attending a demo on June 9\. These are the six things that must work. Nothing else is required for that meeting.

| What to show                                                                    | Who owns it     | Must-have?   |
| :------------------------------------------------------------------------------ | :-------------- | :----------- |
| Dashboard loads with all 5 hospitals in the left sidebar                        | Juan            | Yes          |
| Clicking a hospital shows its signal cards with urgency color-coding (red/blue) | Juan            | Yes          |
| At least 3 real signals from Michael’s pipeline visible in the dashboard        | Michael         | Yes          |
| One live Slack DM fires to a test user showing the digest format                | Joel            | Yes          |
| Signal cards link to source URLs (real Becker’s or newsroom links)              | Michael \+ Juan | Yes          |
| GET /status returns live run data in the dashboard footer                       | Joel            | Nice to have |
| Pending review queue visible in Danielle’s admin view                           | Juan \+ Joel    | Nice to have |
| Co-pilot chat UI (even if not connected to live data yet)                       | Juan            | Nice to have |

**6 · Remaining Role Assignments**

Only the work that is not yet started. Done tasks are not repeated here.

**Joel — Backend (next priority order)**

|   JOEL   | NEXT: Create Slack App at api.slack.com — get SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET. Add to Railway env vars. Takes 5 minutes.                                                                         |
| :------: | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **JOEL** | Task 4: Build slack_service.py — send_dm(), format_weekly_digest() with UTM-tagged links, send_urgent_alert(), rate limiter (10 DMs/min). Test with a real DM to yourself.                                |
| **JOEL** | Task 5: Build rules_engine() — 8 deterministic rules that fire before Claude. Returns {tier, confidence} or None. Full pytest coverage. No credentials needed.                                            |
| **JOEL** | Migration: ALTER TABLE hospitals ADD COLUMN account_type text NOT NULL DEFAULT 'hospital'. Run in Supabase. Confirms extensibility for provider groups Reed mentioned.                                    |
| **JOEL** | Task 7: Build classify_signal() — call rules_engine() first; if None, call Claude Sonnet (claude-sonnet-4-20250514). Return {signal_type, tier, confidence_score, title, summary, classification_source}. |
| **JOEL** | Task 8: Build digest_service.py — send_weekly_digest_to_all_aes(), digest send guard (blocks if pending review queue \> 0, DMs Danielle first), admin summary DM.                                         |
| **JOEL** | ◆ Task 9: Signal review endpoints — POST /signals/{id}/review (approve/dismiss), update digest send guard to block until queue clear.                                                                     |
| **JOEL** | Task 10: Territory auth — get_required_user(), get_admin_user() middleware applied to all endpoints. GET /me. GET /ae-users with last_viewed_digest field.                                                |
| **JOEL** | Tasks 11–19: Contact storage, run logging, CSV export, urgent alert DM, UTM tracking, error handling, performance, Railway deploy, monitoring. See v2 PRD for full task prompts.                          |

**Juan — Frontend (next priority order)**

|   JUAN   | This week: Build the hospital list sidebar and signal feed against the live Railway API. Use the dark-teal aesthetic from the wireframe Reed loved. This is the highest-leverage thing for the June 9 demo.                                          |
| :------: | :--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **JUAN** | Signal cards: urgency badge (red for Urgent, blue for Worth Knowing, gray for low), one-sentence summary, source link, hospital name, date. Match the wireframe card design.                                                                         |
| **JUAN** | Hospital profile page: contact table (name, role, prior employer, website link, LinkedIn URL with verified badge). Signal history feed below.                                                                                                        |
| **JUAN** | ◆ Pending review queue: Danielle’s admin view shows a badge count of unreviewed signals. Each card in the queue shows confidence score, summary, and Approve / Dismiss buttons calling POST /signals/{id}/review.                                    |
| **JUAN** | Territory views: Danielle sees all accounts. Each AE sees only their territory. Driven by X-User-Id header already implemented in the backend.                                                                                                       |
| **JUAN** | ◆ Co-pilot chat UI: A collapsible panel at the bottom of the dashboard. Text input \+ message history. Calls Claude API via a /api/copilot endpoint Joel builds. User can ask: ‘What happened with NYP this week?’ or ‘Summarize David’s territory.’ |
| **JUAN** | ◆ Closed-loop visibility: On dashboard page load, check for UTM params and digest_id. If present, POST /digest-view. In Danielle’s admin AE roster, show ‘Last viewed’ timestamp per AE.                                                             |
| **JUAN** | CSV export button: Calls GET /export/csv, downloads the file. No new page needed. One button on the dashboard toolbar.                                                                                                                               |

**Michael — Data (next priority order)**

|   MICHAEL   | This week: push real signals for all 5 hospitals via the batch endpoint. Joel and Juan need real data to build and test against. This is the most impactful thing Michael can do right now.                    |
| :---------: | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **MICHAEL** | Integrate rules_engine() (Joel’s) into the classification pipeline before every Claude API call. If rules_engine returns a result, store it and skip Claude.                                                   |
| **MICHAEL** | Ensure every signal POST includes: hospital_id, signal_type, tier, confidence_score, title (10 words max), summary (one sentence), source_url (real URL), source_name, published_date.                         |
| **MICHAEL** | ◆ PDF ingestion: when serper.dev returns a .pdf URL (SEC 8-K, IRS 990), call extract_pdf_text() using pdfplumber. Pass first 3,000 words to the classifier. Set source_name to ‘SEC Filing’ or ‘IRS Form 990’. |
| **MICHAEL** | LinkedIn URL discovery: for each contact in the DB, serper.dev query ‘site:linkedin.com/in \[name\] \[hospital\]’. Store top result as linkedin_url with linkedin_verified=false.                              |
| **MICHAEL** | Hospital leadership scraping: scrape official leadership pages for CEO, CFO, CRO, VP Revenue Cycle. POST to /api/v1/contacts via the API.                                                                      |
| **MICHAEL** | Phase 2 — job posting monitoring: serper.dev queries for RCM job postings. Trigger rcm_hiring_spike signal if 3+ postings detected in 7 days. Build this after the core scraper is validated.                  |
| **MICHAEL** | Signal quality log after each run: articles found, classified, rules engine hits, stored, skipped (with skip reasons). Share the log with Joel so it feeds into the agent_runs table.                          |

**7 · Co-pilot Specification — Now a Committed Feature**

The co-pilot is a chat interface on the dashboard that lets Danielle and AEs ask questions about their accounts. Reed and Greg gave a green light. Claude API keys are coming from Greg. This is Phase 3, targeting completion by June 18\.

| Component            | Owner | Detail                                                                                                                                                                                                                                                                                  |
| :------------------- | :---- | :-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Chat UI panel        | Juan  | Collapsible panel on the dashboard. Text input \+ scrollable message history. Adonis brand styling.                                                                                                                                                                                     |
| POST /api/v1/copilot | Joel  | Accepts {user_id, message, context_hospital_id (optional)}. Builds a system prompt with the user’s territory hospitals and recent signals. Calls Claude Sonnet. Returns {reply, sources: \[{signal_id, title}\]}.                                                                       |
| System prompt        | Joel  | You are Adonis Intel, a sales intelligence assistant. The user is {ae_name}, an account executive covering {hospital_names}. Their most recent signals: {last 5 signals from their territory}. Answer questions about their accounts concisely. Cite sources by hospital name and date. |
| Example queries      | Both  | 'What happened with NYP this week?' / 'Summarize David’s territory' / 'Which accounts had leadership changes in May?' / 'Draft a follow-up note about UMass Memorial’s RCM outsourcing announcement'                                                                                    |
| Scope limit          | Joel  | Co-pilot only has access to signals already in the database. It does not run new searches. Keep it grounded in stored data to avoid hallucinations and cost spikes.                                                                                                                     |

**8 · Team Handover Notes**

**What Juan can build against today**

The following endpoints are live on Railway and ready for frontend integration:

| Endpoint                           | What it returns                                              |
| :--------------------------------- | :----------------------------------------------------------- |
| GET /api/v1/hospitals              | All 5 hospitals with AE assignments joined                   |
| GET /api/v1/hospitals/{id}/signals | Signal feed for one hospital (supports tier \+ limit params) |
| GET /api/v1/signals?ae_id={id}     | All signals for an AE’s territory                            |
| GET /api/v1/signals/pending-review | Low-confidence signals awaiting Danielle’s approval          |
| POST /api/v1/signals               | Create a new signal (Michael uses this via batch endpoint)   |
| GET /                              | Health check — confirms database connected                   |

Auth header for all requests: X-User-Id: \<uuid from ae_users table\>

Swagger UI: https://adonisagents-production.up.railway.app/docs

**What Michael’s pipeline needs to send**

Michael’s batch endpoint is live. Every signal his scraper sends should include these fields:

| Field            | Type   | Notes                                                                      |
| :--------------- | :----- | :------------------------------------------------------------------------- | ------------- | ------------ |
| hospital_id      | uuid   | Must match a hospital ID from GET /hospitals                               |
| signal_type      | string | One of the 14 allowed types (see Section 9 of v2 PRD)                      |
| tier             | string | urgent                                                                     | worth_knowing | filtered_out |
| confidence_score | float  | 0.0–1.0. If \< 0.70, signal goes to Danielle’s review queue automatically. |
| title            | string | 10 words max                                                               |
| summary          | string | One sentence — what happened and why it matters to an RCM sales rep        |
| source_url       | string | Must be a real URL. Omit signal if source is unavailable.                  |
| source_name      | string | e.g. ‘Becker’s Hospital Review’, ‘NYP Newsroom’, ‘SEC Filing’              |
| published_date   | date   | YYYY-MM-DD format. Use scrape date if article date is unknown.             |

**INTERNAL — NOT FOR CLIENT DISTRIBUTION**

Joel Philip (lead) · Juan Franco · Michael Chabler · Pursuit L3 AI Native Demo Day · June 3, 2026
