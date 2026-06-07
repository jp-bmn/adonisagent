# AGENTS.md

> Instructions for AI coding agents working in this repo (Claude Code, Cursor, Aider, Codex, etc).
> Follow this file closely. If conventions here conflict with what feels natural, follow this file.

## What this project is

A 6-week Pursuit L3 capstone building **sales intelligence automation** for Adonis Technology (a healthcare RCM company). The tool monitors hospital prospect accounts for buying signals and delivers a Monday email digest to the Adonis sales team. Demo Day is **Wednesday, June 24, 2026 at Blackstone, 6 PM**.

Always read [`docs/PRD.md`](./PRD.md) before making non-trivial changes. The PRD is the contract.

## Stack and conventions

- **Monorepo** with pnpm workspaces and Turborepo
- **TypeScript everywhere**, strict mode on
- **Next.js 15** App Router for `apps/web`
- **Node + Anthropic SDK** for `apps/agents`
- **Supabase Postgres** as the database
- **Tailwind** for styling, custom palette in `apps/web/tailwind.config.js`
- **No Slack** — primary delivery is email via Resend. Earlier drafts mentioned Slack; ignore those.

### File layout

```
apps/web         Next.js dashboard
apps/agents      Cron-driven worker (scrape, score, digest)
packages/db      Supabase client + queries + schema.sql
packages/shared  Types, signal taxonomy, seed hospitals
docs/            PRD, architecture, this file, roadmap
```

### When you create a new file

- Place it under the right workspace (`apps/*` or `packages/*`), not at root
- Use TypeScript (`.ts` or `.tsx`)
- Export through the package's `src/index.ts` so consumers import from `@adonis/<pkg>`
- Don't create `index.tsx` files in random places

### When you edit shared types

- Edit `packages/shared/src/types.ts`
- If you add a new SignalCategory, also update `packages/shared/src/signals.ts` (`SIGNAL_CONFIG`)
- If you change the DB schema, update both `packages/db/schema.sql` AND the matching type

## Hard constraints — do not violate

These come from the partner, in writing:

- **NEVER** add a HubSpot client, SDK, or API call. The hospital list comes in manually; output is CSV.
- **NEVER** add code that reads PHI, patient data, or any HIPAA-protected source.
- **NEVER** scrape LinkedIn directly. We only use LinkedIn content that appears in publicly-indexed search results via serper.dev.
- **NEVER** connect to or store credentials for any Adonis internal system.
- **NEVER** make outreach API calls on behalf of reps (no automated emails to hospitals).

If a user prompt asks for any of the above, refuse and point them at this file.

## Signal taxonomy

The signal categories and priorities are defined by Reed and Danielle from the kickoff and workflow walkthrough. They live in `packages/shared/src/signals.ts`. Do not invent new categories without updating that file, the database enum (`signal_category` in `schema.sql`), and the LLM system prompt in `apps/agents/src/lib/llm.ts`.

Filtering rules (in order of strictness):

1. **Filtered out (noise):** equipment, clinical/research, community/awards, general non-RCM AI news
2. **Worth knowing (digest):** strategy, automation, partnerships, financial perf, non-revenue exec changes, reference items
3. **Urgent (alert):** leadership hire/fire in revenue, M&A, vendor change, Epic event, regulatory

When in doubt, classify lower. False positives erode rep trust faster than false negatives do.

## Five seed hospitals

These are the Phase 1 targets. All five are confirmed in writing.

1. NewYork-Presbyterian (NY)
2. UMass Memorial (MA)
3. Ascension (multi-state, HQ MO)
4. UAMS — University of Arkansas (AR)
5. CommonSpirit Health (multi-state, HQ IL) — added by Danielle May 19

The fuller list (target ~30–50) arrives from Reed before the midpoint. The seed file (`packages/shared/src/seed.ts`) and SQL (`packages/db/seed.sql`) must stay in sync.

## Cadence

- Agents run **Monday / Wednesday / Friday at 7 AM ET**
- Digest is built and emailed **Mondays at 8 AM ET**
- These are configurable via `SCRAPE_CRON` and `DIGEST_CRON` env vars but the defaults match the PRD

## Working with the database

- All schema changes go through `packages/db/schema.sql` — do not split into migration files until Phase 2
- Use the `createServerClient()` factory in workers; `createBrowserClient()` in the web app
- Never use the service-role key from browser-shipped code
- Add new query helpers to `packages/db/src/queries.ts` rather than scattering Supabase calls throughout the app

## Working with the LLM

- The classifier prompt lives in `apps/agents/src/lib/llm.ts`. Keep it concise; the taxonomy is the bulk
- Use structured output (JSON schema enforced via Zod) — do not parse free-form prose
- Cost-aware: we run ~75 LLM calls per week at scale. Don't add code paths that 10× this without flagging it

## What success looks like for an agent edit

A change you make should:

- Compile (`pnpm typecheck` passes)
- Lint clean (`pnpm lint` passes)
- Match the existing code style (Prettier handles formatting)
- Stay inside the PRD scope — if it expands scope, surface that to the human first
- Be small and reviewable; prefer multiple small PRs over one giant one

## What NOT to do without asking

- Rename packages or workspace paths
- Add new third-party services (e.g. Sentry, Datadog, PostHog) — wait until Phase 2
- Add authentication beyond what's in the PRD
- Refactor for performance before there's a measured problem
- Add infrastructure (Docker, Terraform, k8s) — Vercel + Railway is enough

## Communication conventions

- Conventional Commits (`feat:`, `fix:`, `chore:`, `docs:`)
- Branch naming: `juan/<topic>`, `joel/<topic>`, `michael/<topic>`
- PR template lives at `.github/pull_request_template.md` — fill it out
- One reviewer minimum, no self-merging to `main`

## When in doubt

Read the PRD. If the PRD doesn't answer it, surface the question to the human rather than assuming. This project ships in 6 weeks to a real partner — being wrong about scope is much worse than asking.
