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

## Week 1 — TBD

Add notes here as work lands.
