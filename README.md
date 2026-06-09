# Adonis Account Intelligence Tool

Adonis agentic sales intelligence dashboard — L3 AI Native Project.

## Components

- **[Backend Service](file:///Users/joel-bmn/adonisagent/backend/README.md)**: FastAPI service, hybrid rules-and-AI classification engine, Supabase database client, and Slack notification dispatches.

# Adonis Account Intelligence

> Sales intelligence automation for the Adonis hospital prospecting team.
> Pursuit L3 AI Native Demo Day · June 24, 2026 at Blackstone

## What this is

An automated system that monitors a curated list of hospital prospects for buying signals — new revenue leadership, M&A, vendor changes, Epic go-lives, regulatory events — and delivers them to the Adonis team in three forms:

1. **Monday morning email digest** to Danielle, who forwards to each AE
2. **Web dashboard** with territory-filtered views per AE
3. **Persistent hospital profiles** that accumulate signal history over time

The tool replaces **Glean** (the internal AI tool the team uses reactively, only before scheduled calls) with continuous, proactive monitoring. See [`docs/PRD.md`](docs/PRD.md) for the full product requirements.

## Users

| User                | Role                                                                    |
| ------------------- | ----------------------------------------------------------------------- |
| **Danielle Ferdon** | Admin view across all accounts; compiles and forwards the Monday digest |
| **Michael**         | AE — territory-filtered dashboard, his accounts only                    |
| **Jeff**            | AE — territory-filtered dashboard, his accounts only                    |
| **David**           | AE — territory-filtered dashboard, his accounts only                    |

## Seed hospitals (Phase 1)

1. NewYork-Presbyterian
2. UMass Memorial
3. Ascension
4. University of Arkansas (UAMS)
5. CommonSpirit Health

## Team

- **Juan Franco** — frontend, design system, dashboard UX
- **Michael Chabler** — partner communications
- **Joel Philip** — backend, agent pipeline, scoping, project management

Partner: Adonis Technology, Inc. · Primary contact: Reed Kalash · SME: Danielle Ferdon

## Repo layout

```
adonisagent/
├── apps/
│   ├── web/                  Next.js dashboard, hospital list, profiles
│   └── agents/               Mon/Wed/Fri scrape pipeline + Monday digest email
├── packages/
│   ├── db/                   Supabase schema + query helpers
│   └── shared/               Types, signal taxonomy, seed data
├── docs/
│   ├── PRD.md                Final product requirements
│   ├── ARCHITECTURE.md       System design and data flow
│   ├── AGENTS.md             Instructions for AI coding agents
│   └── ROADMAP.md            Week-by-week plan
├── .github/
│   ├── workflows/ci.yml      Lint + typecheck on every PR
│   ├── ISSUE_TEMPLATE/       Bug + feature templates
│   └── pull_request_template.md
├── README.md
├── CHANGELOG.md              Week-by-week build notes
└── CLAUDE.md                 Pointer to AGENTS.md
```

## Quick start

Requirements: Node 20+, pnpm 9+, a Supabase project.

```bash
pnpm install
cp .env.example .env.local
# fill in env values - see comments in .env.example

# In your Supabase SQL editor:
#   1. run packages/db/schema.sql
#   2. run packages/db/seed.sql

pnpm dev
```

This starts `apps/web` at http://localhost:3000 and the agent worker in watch mode.

Manual jobs:

```bash
pnpm --filter @adonis/agents scrape:once         # one full pass through sources
pnpm --filter @adonis/agents digest:preview      # render digest to stdout
```

## Build status

- [x] Repo structure + tooling
- [x] Supabase schema for hospitals, contacts, signals, users, digests
- [x] Signal taxonomy from kickoff (urgent / standard / noise)
- [x] Five seed hospitals loaded
- [x] Three web pages (signal feed, hospital list, profile)
- [x] Agent worker scaffold with cron scheduling
- [x] Email digest renderer (HTML + plain text)
- [ ] Real scraping logic per source (hospital newsrooms, serper.dev, Becker's)
- [ ] LLM classification wired to Claude
- [ ] Digest delivery wired to Resend
- [ ] Per-AE territory filtering (Phase 2)
- [ ] Persistent hospital profiles with signal history (Phase 2)
- [ ] Co-pilot chat interface (Phase 3 stretch)

## Hard constraints (from the partner)

These do not move:

- **No HubSpot connection.** Hospital list comes in manually; output is a CSV they upload.
- **Public sources only.** No PHI, HIPAA-protected, or paywalled data.
- **No LinkedIn scraping.** Sales Navigator complements this tool; it does not replace it.
- **No internal Adonis systems.** Tool is fully standalone for the build window.

## Timeline

| Date                      | Milestone                                    |
| ------------------------- | -------------------------------------------- |
| May 19                    | ✅ Danielle workflow walkthrough             |
| Weeks 1–2                 | Digest + dashboard live for 5 seed hospitals |
| **Tue Jun 2, 3:00 PM ET** | **Midpoint review with Reed**                |
| Weeks 3–4                 | Full dashboard, per-AE territory views       |
| Week 5                    | Refinement + co-pilot prototype if ahead     |
| **Wed Jun 24, 6 PM**      | **Demo Day at Blackstone**                   |

## Communication

- **All external email to Adonis goes through Greg first.** Period.
- Internal: GitHub Issues for tracked work, Slack for coordination.
- Reed prefers email; 2–3 status emails/week + monthly meeting.

## License

Private — Pursuit capstone project. Not for distribution.
