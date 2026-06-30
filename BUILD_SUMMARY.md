# Adonis Account Intelligence — Completed Build Summary

This document lists all the features, integrations, database schemas, and workflows implemented in the Adonis build.

---

## 🛠️ Repository & Architecture
- **GitHub Monorepo Structure**: Set up with `pnpm` workspaces and `Turborepo` containing:
  - `apps/web`: Next.js 14 dashboard app.
  - `apps/agents`: Trigger.dev/cron scraping workers.
  - `backend`: FastAPI API server.
  - `packages/db` & `packages/shared`: Shared types, queries, and taxonomy.
- **CI/CD Pipeline**: Configured `.github/workflows/ci.yml` to execute TypeScript compilation, formatting verification (Prettier), and linter rules on every pull request.
- **Environment Management**: Unified `.env` structure across backend, frontend, and worker packages.

---

## 🗄️ Database (Supabase / PostgreSQL)
- **Schema & Migrations**: Designed, migrated, and verified the relational schema ([001_initial_schema.sql](file:///Users/joel-bmn/adonisagent/backend/migrations/001_initial_schema.sql)):
  - `hospitals`: Profiles, website URLs, and account type support.
  - `ae_users`: Role permissions (admin vs AEs) and Slack credentials.
  - `hospital_ae_assignments`: Join table mapping AEs to territories.
  - `signals`: Confidence scores, review status, and metadata.
  - `contacts`, `digests`, `digest_views`, and `agent_runs`.
- **Database Seeding**: Python seed script ([seed_db.py](file:///Users/joel-bmn/adonisagent/backend/scripts/seed_db.py)) and count checker ([verify_seed.py](file:///Users/joel-bmn/adonisagent/backend/scripts/verify_seed.py)) seeded with 6 confirmed hospitals (NewYork-Presbyterian, UMass Memorial, Ascension, UAMS, CommonSpirit, Jefferson Health) mapped to Michael, David, and Jeff.

---

## ⚙️ Ingestion & Classification Pipeline
- **Hospital Scrapers**: Automated news scraping utilizing `serper.dev` and `NewsAPI` queries.
- **Deterministic Rules Engine**: Python rules engine evaluating 8 keyword pattern rules to bypass Claude AI for deterministic high-confidence signals (CRO executive hires, epic go-lives, restructuring, vendor disputes).
- **Claude AI Classifier**: Fallback classifier calling Claude 3.5 Sonnet, returning:
  - `signal_type` taxonomy (leadership change, hiring spike, epic go-live, post-go-live friction, vendor change, vendor dispute, restructuring, mergers, new launch, financial event, AI adoption outside RCM, automation wins, named owner, thought leadership).
  - `tier` (Urgent, Worth Knowing, Low).
  - `confidence_score` & one-sentence summary.
- **PDF Document Ingestion**: Integrates `pdfplumber` parsing to extract SEC 8-K filings and IRS Form 990 PDF text and identify financial events.
- **Deduplication**: Filters out duplicate signals within a rolling 30-day window.

---

## 🔌 FastAPI Backend Server
- **Core Endpoints**:
  - `GET /api/v1/hospitals`: Hospital list filterable by AE territory.
  - `GET /api/v1/hospitals/{id}/signals`: Ordered signal feed.
  - `GET /api/v1/status`: Rolling weekly trend calculations with KPI metrics (`urgent_delta` / `worth_knowing_delta` and direction `up`/`down`/`flat`).
  - `POST /api/v1/digest-view`: UTM open-tracking webhook.
  - `GET /api/v1/me` & `GET /api/v1/ae-users`: AE roster and individual open tracking.
  - `POST /api/v1/copilot`: Scaffolds LLM chat completions for territory insights.
  - `GET /api/v1/export/csv`: Bulk CSV downloader for signals.
- **Performance**: Added response-level TTL caching (`@ttl_cache(60.0)`) and CORS preflight caching.
- **Robustness**: 
  - Automated exponential backoff retry handler wrapping Claude API requests.
  - Global FastAPI exception handler dispatching unhandled 500 stack trace alerts to Danielle's Slack DM.

---

## 🎨 Next.js Frontend Dashboard
- **Sidebar & Roster Layout**: Fully responsive viewport rendering:
  - Left panel shows hospital list, filterable by Michael, David, or Jeff's territories.
  - Main signal feed display with color-coded urgency badges (Urgent red, Worth Knowing blue, Low gray) and source links.
- **Human-in-the-Loop Review Queue**: Admin dashboard for Danielle showing low-confidence signals (< 0.70) with direct Approve / Dismiss hooks.
- **UTM open-tracking**: Captured UTM query parameters on page load to POST visit data to `/digest-view`.
- **Roster & Activity Feed**: Renders the open/read metrics dashboard for AE user digests.
- **Hermes Chat Bubble**: Dynamic chat assistant interface anchored to the viewport.

---

## 💬 Slack Integration & Bot
- **Weekly Digest DM**: Compiles and sends a combined weekly digest DM to AEs every Monday morning, containing account grouping and UTM-tagged URLs.
- **Immediate Urgent Alerts**: Direct DMs sent to AEs in real-time when an `Urgent` signal is scraper-detected.
- **Digest Send Guard**: Enforces that the Monday digest only sends once Danielle's pending review queue is completely empty.

---

## 🧪 Testing & Verification
- Over **190 unit and integration tests** verifying:
  - Rules engine keyword matching and exceptions.
  - Route authentication and pagination.
  - End-to-end signal flow: classification -> gate check -> admin review queue -> weekly digest dispatch -> UTM view logging.
