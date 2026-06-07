# PRD · Account Intelligence Tool
## Build Plan v3 · Post-Midpoint Update

> **Status:** Active — post-midpoint update.
> **Source:** Reflects midpoint review with Reed Kalash (June 2, 2026) and progress report (June 3, 2026).
> **Date:** June 3, 2026

| Field | Details |
|---|---|
| Project lead | Joel Philip — backend, architecture, Slack, deployment |
| Frontend | Juan Franco — dashboard UI, profiles, co-pilot interface |
| Data | Michael Chabler — scrapers, signal extraction, PDF ingestion |
| Reed demo | Tuesday, June 9, 2026 — working demo required |
| Internal build deadline | Wednesday, June 18, 2026 — full build done; debug week starts |
| Demo Day | Wednesday, June 24, 2026 at Blackstone |

Green light confirmed. Reed said: "Build the damn thing." The BAA with Claude is signed. Adonis has enterprise API keys with centrally managed tokens. Cost is no longer a constraint.

---

## 1 · What Changed at the Midpoint Review

- Claude BAA is signed. Use Sonnet aggressively — no token cost concerns.
- Reed confirmed this will be used by his sales team weekly. This is a real product.
- Reed loved the wireframe: "If it looks and works like that, you guys did a great job."
- Reed wants to expand beyond hospitals — provider groups and customer success are next segments. Data model must be flexible.
- Co-pilot got a green light from Reed and Greg. It is now a **committed Phase 3 deliverable**, not a stretch feature.
- Someone at Adonis will maintain the tool after Demo Day. Write readable, extensible code.

---

## 2 · Who It's For

| User | Role |
|---|---|
| **Danielle Ferdon** | Partnerships / senior BDR. Admin view across all accounts. Compiles the weekly digest and sends it to the relevant AE each Monday. |
| **Michael** (AE) | Territory-filtered dashboard, his hospital accounts only. Receives Danielle's Monday digest. |
| **Jeff** (AE) | Same as above, separate territory. |
| **David** (AE) | Same as above, separate territory. |

---

## 3 · What We're Building

### Phase 1 · Dashboard + Monday email digest
Dashboard displays every account, every signal, and the full news history — filtered by territory for each AE, full visibility for Danielle. Signals are color-coded by urgency. Every Monday morning, agents run a full sweep and compile a digest. Danielle receives it, reviews it, and forwards to each AE.

### Phase 2 · Territory views + persistent profiles
Each AE's dashboard is personalized to their hospital list. Hospital profile pages accumulate a running signal history. Danielle retains admin view across all accounts.

### Phase 3 · Co-pilot — committed deliverable
A chat interface on the dashboard. Danielle or an AE can ask questions ("What happened with NYP this week?"), request historical backtracking, and prompt the co-pilot to draft the weekly digest. Targets completion by June 18.

---

## 4 · What the Tool Monitors

| Tier | Coverage |
|---|---|
| **Urgent** (instant alert) | New revenue or finance leader hired or departed (CRO, CFO, VP Revenue Cycle, Director RCM) · Merger, acquisition, or system expansion · Revenue-cycle vendor or outsourcing change · Epic or EHR go-live, migration, or expansion · Financial-review or regulatory event · Significant hiring of billing or RCM operations staff |
| **Worth knowing** (weekly digest) | Revenue-cycle strategy or performance changes · RCM automation or AI initiatives · Partnerships and joint ventures · Financial performance and margin pressure · Leadership changes outside revenue · Meeting-prep reference items |
| **Filtered out** | Equipment and facility purchases · Clinical or research program news · Community events, philanthropy, and awards · General AI news not specific to revenue cycle |

---

## 5 · Scope

| The tool will | The tool will not |
|---|---|
| Monitor the agreed hospital list — agents run 2–3x weekly | Connect to or write to HubSpot |
| Send a Monday morning email digest to Danielle for distribution | Access any private, patient, or PHI / HIPAA-protected data |
| Provide a web dashboard with territory-filtered views | Scrape LinkedIn or replicate Sales Navigator |
| Build hospital profiles: account name, signal bullets, source links | Send outreach emails on behalf of reps |
| Export a HubSpot-ready CSV on demand | Monitor hospitals outside the agreed list |

---

## 6 · Current Status (as of June 3)

| Task | Status | Notes |
|---|---|---|
| Task 1 — FastAPI skeleton + deployment | ✅ Done | Railway live: adonisagents-production.up.railway.app |
| Task 2 — Supabase schema + seed data | ✅ Done | 5 hospitals, 4 users, 5 assignments in DB |
| Task 3 — Core hospital + signal endpoints | ✅ Done | 16/16 tests passing |
| Bonus — Batch ingest (Michael's endpoint) | ✅ Done | Fuzzy match, dedup, bearer auth live |
| Task 4 — Slack bot + send_dm() | 🔴 Blocker | Blocks Tasks 8, 14, 16 |
| Task 5 — Rules engine | 🔴 Blocker | Blocks Task 7 (classifier) |
| Task 6 — Trigger.dev scheduler | Stub only | Admin endpoints exist as stubs |
| Task 7 — Claude classifier | Not started | Needs Tasks 4 + 5 first |
| Task 8 — Weekly digest formatter | Not started | Needs Tasks 4 + 7 |
| Tasks 9–19 | Not started | See sprint plan below |

Railway API base URL: `https://adonisagents-production.up.railway.app/api/v1`
Swagger docs: `GET /docs` · Auth header: `X-User-Id: <ae_user_id_from_supabase>`
Michael's batch endpoint: `POST /api/v1/signals/batch` · Bearer token: `adonis-internal-dev-key-2026`

---

## 7 · Revised Sprint Plan — June 3 to June 24

| Days | Joel — Backend | Juan — Frontend | Michael — Data |
|---|---|---|---|
| June 3–6 | Task 4: Slack bot · Task 5: rules_engine() · Migration: add account_type field | Hospital list + signal feed against live API · Dark-teal aesthetic · Signal cards with urgency color-coding | Scraper pipeline for all 5 hospitals · Push real signals via batch endpoint |
| **June 9 Reed demo** | Task 7: Claude classifier · Task 8: Weekly digest · Demo prep: seed DB, verify live Slack DM | Dashboard showing live signals · Hospital list functional · Demo-ready by 9 AM | Signal quality report · All 5 hospitals scraped · Classification accuracy validated |
| June 9–13 | ◆ Task 9: Signal review endpoints · Task 10: Territory-filtered API + auth · Task 11: Contact storage · Task 12: Run logging + GET /status | ◆ Pending review queue UI · Territory-filtered views per AE · Contact profile display | ◆ PDF ingestion · LinkedIn URL discovery · Job posting monitoring |
| June 13–18 | Task 13: CSV export · Task 14: Urgent alert DM · ◆ Task 15: UTM tracking · Tasks 16–19: error handling, performance, deploy, monitoring | CSV export button · Dashboard polish + mobile · ◆ UTM capture · ◆ Co-pilot UI (Claude Sonnet) · Final UX pass | Vendor dispute + AI adoption signals · Signal taxonomy refinement · False positive analysis |
| **June 18** | All endpoints live · All tests passing · Production deploy verified | All dashboard views functional · Co-pilot responding to queries | All 5 hospitals scraped + classified · Signal quality validated |
| June 18–23 | Bug fixes · Load test · Demo script | UI polish · Load time optimization · Demo walkthrough rehearsed | Data freshness verified · Full run on all hospitals day before |
| **June 24 Demo Day** | Production stable · All integrations live | Dashboard at full fidelity · Co-pilot live | Data current as of June 23 |

---

## 8 · June 9 Demo Scope — What "Working" Means

| What to show | Owner | Must-have? |
|---|---|---|
| Dashboard loads with all 5 hospitals in the left sidebar | Juan | Yes |
| Clicking a hospital shows signal cards with urgency color-coding | Juan | Yes |
| At least 3 real signals from Michael's pipeline visible | Michael | Yes |
| One live Slack DM fires to a test user showing digest format | Joel | Yes |
| Signal cards link to real source URLs | Michael + Juan | Yes |
| GET /status returns live run data in the dashboard footer | Joel | Nice to have |
| Pending review queue visible in Danielle's admin view | Juan + Joel | Nice to have |
| Co-pilot chat UI (even if not connected to live data yet) | Juan | Nice to have |

---

## 9 · Role Assignments — Remaining Work

### Joel — Backend
1. Create Slack App at api.slack.com — get SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET. Add to Railway env vars.
2. **Task 4:** Build slack_service.py — send_dm(), format_weekly_digest() with UTM-tagged links, send_urgent_alert(), rate limiter (10 DMs/min).
3. **Task 5:** Build rules_engine() — 8 deterministic rules before Claude. Returns {tier, confidence} or None. Full pytest coverage.
4. **Migration:** `ALTER TABLE hospitals ADD COLUMN account_type text NOT NULL DEFAULT 'hospital'`
5. **Task 7:** Build classify_signal() — rules_engine() first; if None, call Claude Sonnet. Return {signal_type, tier, confidence_score, title, summary, classification_source}.
6. **Task 8:** Build digest_service.py — send_weekly_digest_to_all_aes(), digest send guard (blocks if pending review queue > 0), admin summary DM.
7. **◆ Task 9:** Signal review endpoints — POST /signals/{id}/review (approve/dismiss).
8. **Task 10:** Territory auth — get_required_user(), get_admin_user() middleware. GET /me. GET /ae-users with last_viewed_digest field.
9. **Tasks 11–19:** Contact storage, run logging, CSV export, urgent alert DM, UTM tracking, error handling, performance, Railway deploy, monitoring.

### Juan — Frontend
1. Hospital list page + signal feed against live Railway API.
2. Signal cards: urgency badge (red Urgent, teal Update), summary, source link, hospital name, date.
3. Hospital profile page: contact table (name, role, prior employer, website, LinkedIn URL with verified badge) + signal history feed.
4. **◆ Pending review queue:** Danielle's admin view with badge count, confidence score, Approve / Dismiss buttons calling POST /signals/{id}/review.
5. Territory views: Danielle sees all accounts; each AE sees only their territory via X-User-Id header.
6. **◆ Co-pilot chat UI:** Collapsible panel, text input + message history, calls POST /api/v1/copilot Joel builds.
7. **◆ Closed-loop visibility:** On page load, check UTM params + digest_id. If present, POST /digest-view. Show 'Last viewed' timestamp per AE in Danielle's admin roster.
8. CSV export button: calls GET /export/csv, triggers download.

### Michael — Data
1. Push real signals for all 5 hospitals via batch endpoint — Joel and Juan need real data now.
2. Integrate rules_engine() into classification pipeline before every Claude API call.
3. Every signal POST must include: hospital_id, signal_type, tier, confidence_score, title (10 words max), summary (one sentence), source_url, source_name, published_date.
4. **◆ PDF ingestion:** when serper.dev returns a .pdf URL, call extract_pdf_text() via pdfplumber. Pass first 3,000 words to classifier.
5. LinkedIn URL discovery: serper.dev query 'site:linkedin.com/in [name] [hospital]'. Store as linkedin_url with linkedin_verified=false.
6. Hospital leadership scraping: scrape official leadership pages for CEO, CFO, CRO, VP Revenue Cycle. POST to /api/v1/contacts.
7. **Phase 2:** Job posting monitoring via serper.dev. Trigger rcm_hiring_spike if 3+ postings in 7 days.

---

## 10 · Co-pilot Specification — Committed Feature

| Component | Owner | Detail |
|---|---|---|
| Chat UI panel | Juan | Collapsible panel on the dashboard. Text input + scrollable message history. Adonis brand styling. |
| POST /api/v1/copilot | Joel | Accepts {user_id, message, context_hospital_id (optional)}. Builds system prompt with user's territory + recent signals. Calls Claude Sonnet. Returns {reply, sources: [{signal_id, title}]}. |
| System prompt | Joel | "You are Adonis Intel, a sales intelligence assistant. The user is {ae_name}, an account executive covering {hospital_names}. Their most recent signals: {last 5 signals}. Answer questions concisely. Cite sources by hospital name and date." |
| Scope limit | Joel | Co-pilot only has access to signals in the database. Does not run new searches. Grounded in stored data to avoid hallucinations. |

---

## 11 · Live API Reference

| Endpoint | What it returns |
|---|---|
| GET /api/v1/hospitals | All 5 hospitals with AE assignments joined |
| GET /api/v1/hospitals/{id}/signals | Signal feed for one hospital (supports tier + limit params) |
| GET /api/v1/signals?ae_id={id} | All signals for an AE's territory |
| GET /api/v1/signals/pending-review | Low-confidence signals awaiting Danielle's approval |
| POST /api/v1/signals | Create a new signal |
| GET / | Health check — confirms database connected |

Auth header for all requests: `X-User-Id: <uuid from ae_users table>`
Swagger UI: `https://adonisagents-production.up.railway.app/docs`

### Signal fields required from Michael's pipeline

| Field | Type | Notes |
|---|---|---|
| hospital_id | uuid | Must match a hospital ID from GET /hospitals |
| signal_type | string | One of the 14 allowed types |
| tier | string | urgent \| worth_knowing \| filtered_out |
| confidence_score | float | 0.0–1.0. If < 0.70, goes to Danielle's review queue automatically |
| title | string | 10 words max |
| summary | string | One sentence — what happened and why it matters to an RCM sales rep |
| source_url | string | Must be a real URL. Omit signal if source unavailable. |
| source_name | string | e.g. 'Becker's Hospital Review', 'NYP Newsroom', 'SEC Filing' |
| published_date | date | YYYY-MM-DD format |

---

## 12 · What Success Looks Like

Danielle opens her inbox on Monday morning and has a pre-organized digest ready to forward to each AE — without touching Glean, without searching a single website.

- Danielle no longer re-queries Glean before calls — the digest has already done the work
- AEs enter every call aware of the most recent signal for that account
- Urgent signals surface within 24 hours of public reporting
- The Monday digest posts every week with zero manual research required
- Any account can be fully briefed in under 60 seconds from the dashboard

---

*INTERNAL — NOT FOR CLIENT DISTRIBUTION*
*Joel Philip (lead) · Juan Franco · Michael Chabler · Pursuit L3 AI Native Demo Day · June 3, 2026*
