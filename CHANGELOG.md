# Changelog

Week-by-week build notes. Not semver — this is a capstone, not a shipped product.

## Week 0 — Repo bootstrap (May 17–18)

- Initial monorepo scaffold: TypeScript, pnpm workspaces, Turborepo
- Supabase schema (hospitals, contacts, signals, users, digests, agent_runs)
- Signal taxonomy from the kickoff codified in `packages/shared/src/signals.ts`
- Seed data: 5 confirmed hospitals (NewYork-Presbyterian, UMass Memorial, Ascension, UAMS, CommonSpirit)
- Agent worker scaffold with Mon/Wed/Fri cron + Monday digest cron
- Email digest renderer (HTML + plain text)
- Next.js 15 web app with signal feed, hospital list, and hospital profile pages
- Docs: PRD, ARCHITECTURE, AGENTS, ROADMAP, this file
- GitHub workflow for lint + typecheck
- Issue + PR templates

## Week 1 — Progress

- Added KPI trend pill status delta fields (`urgent_delta`, `urgent_delta_direction`, `worth_knowing_delta`, `worth_knowing_delta_direction`) to backend `/status` endpoint and schemas.
- Added AE user `Jeff` to the database and assigned him to `Jefferson Health` to resolve his missing territory filter view.
- Synced database seeds, migrations (`001_initial_schema.sql`), and tests (`test_e2e.py`) to support the updated AE user roster.
