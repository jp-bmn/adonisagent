# Architecture

System design and data flow for the Adonis Account Intelligence tool.

## Topology

```
┌─────────────────────────────────────────────────────────────────┐
│  AGENTS (apps/agents) - runs Mon/Wed/Fri 7 AM, Mondays 8 AM     │
│                                                                 │
│  ┌────────────────┐  ┌───────────┐  ┌────────────────────┐      │
│  │ Hospital       │  │ serper.dev│  │ Becker's via       │      │
│  │ newsrooms      │  │ /news     │  │ site: search       │      │
│  └────────┬───────┘  └─────┬─────┘  └─────────┬──────────┘      │
│           │                │                  │                 │
│           └────────────────┴──────────────────┘                 │
│                            │                                    │
│                  ┌─────────▼──────────┐                         │
│                  │ Score & classify   │                         │
│                  │  (Claude)          │                         │
│                  └─────────┬──────────┘                         │
│                            │                                    │
│                  ┌─────────▼──────────┐                         │
│                  │ Persist signals    │                         │
│                  │  (dedup by hash)   │                         │
│                  └─────────┬──────────┘                         │
│                            │                                    │
│                  ┌─────────▼──────────┐  Mondays only           │
│                  │ Build digest →     │                         │
│                  │  send via Resend   │                         │
│                  └─────────┬──────────┘                         │
└────────────────────────────┼────────────────────────────────────┘
                             │
                  ┌──────────▼──────────────┐
                  │  Supabase Postgres      │
                  │  hospitals · contacts   │
                  │  signals · digests      │
                  │  users · user_hospitals │
                  │  agent_runs             │
                  └──────────┬──────────────┘
                             │
┌────────────────────────────▼───────────────────────────────────┐
│  WEB (apps/web) - Next.js 15 App Router on Vercel              │
│                                                                │
│  /                      Signal feed (territory-filtered)       │
│  /hospitals             All accounts                           │
│  /hospitals/[id]        Profile + signal history               │
│  /alerts                Urgent feed                            │
│  /export                CSV download                           │
└────────────────────────────────────────────────────────────────┘

                  ┌─────────────────────┐
                  │ Danielle's inbox    │
                  │ (Monday digest)     │
                  └─────────────────────┘
```

## Data model

Five core tables in Postgres (see `packages/db/schema.sql`):

- **hospitals** — the prospect accounts
- **contacts** — revenue/finance leadership at each hospital
- **signals** — the unit of intelligence; every row links to a public source
- **users** — Danielle (admin) + 3 AEs
- **user_hospitals** — territory assignment (which AE owns which hospitals)
- **digests** — Monday email summaries; one per user per week
- **agent_runs** — observability for the scrape jobs

Shared TypeScript types in `packages/shared/src/types.ts` are the source of truth — schema and types stay aligned.

## Signal pipeline

For each raw news item:

1. **Fetch** — source-specific scrapers in `apps/agents/src/sources/` return `RawItem[]`
2. **Keyword filter** — drop obvious noise (equipment, clinical news, awards) before spending tokens
3. **LLM classify** — Claude maps the item to a `SignalCategory`, `priority`, score, headline, summary, rationale
4. **Dedup** — content hash on `(hospital_id, category, url)` prevents the same story from multiple sources double-counting
5. **Persist** — insert into `signals` table with `delivered_in_digest = false`
6. **Alert (urgent only)** — if priority is urgent and score ≥ 75, fire instant alert (Phase 2)

## Cadence

| Job | Cron | Action |
|---|---|---|
| Scrape | `0 7 * * 1,3,5` | Mon/Wed/Fri 7 AM — full pass through all sources |
| Digest | `0 8 * * 1` | Mondays 8 AM — build and email weekly digest |

Both configurable via env (`SCRAPE_CRON`, `DIGEST_CRON`). `TZ=America/New_York` by default.

## Hard constraints (enforced at architecture level)

- **No HubSpot client.** The codebase has no HubSpot SDK and never will during this build. List is loaded from `packages/db/seed.sql`; output is a CSV download.
- **No PHI.** No code path reads, stores, or transmits private patient data. Every persisted field is publicly sourced.
- **No internal Adonis network calls.** The system is fully external.
- **No LinkedIn scraping.** No code path hits linkedin.com directly. We only consume LinkedIn snippets via Google-indexed search results returned by serper.dev.

## Tech choices and trade-offs

| Choice | Why |
|---|---|
| TypeScript monorepo | One language across frontend and agents; cheaper context switching for a 3-person team |
| Supabase | Free tier covers our scale; Postgres is the right tool; built-in auth is there if we need it for Phase 2 |
| Next.js App Router | Server components fit dashboard read patterns; one deploy target on Vercel |
| Tailwind + bespoke design | Matches the visual mockup; no design-system import overhead |
| Claude (Anthropic SDK) | Pursuit provides API access; strong at structured-output classification |
| serper.dev | Named in the PRD as the primary news aggregator |
| Resend | Modern, low-friction transactional email; HTML templates render reliably |
| node-cron | In-process scheduling is enough for our cadence; no need for external orchestrators yet |

## Observability

- `agent_runs` table records every scrape job (start, finish, status, items, errors)
- `digests` table records every email sent (status, message id)
- Structured JSON logs to stdout (`src/lib/log.ts`) — pipe to whatever later

## Deployment (planned)

- `apps/web` → Vercel
- `apps/agents` → Railway or Fly.io (long-running worker; cron lives inside the process)
- Supabase → managed
- Secrets → Vercel + Railway env vars

## What's intentionally NOT here

- A queue (we don't need one at our scale; Postgres + cron is enough)
- A search index (Postgres FTS is fine for now; pgvector reserved for the Phase 3 co-pilot)
- Container orchestration (Railway handles it)
- A microservice split (one worker process; no service mesh)
