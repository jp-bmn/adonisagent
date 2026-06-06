# CLAUDE.md

This file is for Claude Code. The full agent instructions live in [`docs/AGENTS.md`](docs/AGENTS.md). Read that first.

## Quick reference

- **What we're building:** Sales intelligence tool for Adonis (healthcare RCM). 5 hospitals. Email digest + dashboard. Demo June 24 at Blackstone.
- **PRD:** [`docs/PRD.md`](docs/PRD.md) — read before any meaningful change.
- **Architecture:** [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- **Stack:** TypeScript monorepo · Next.js 15 · Supabase · Claude · Resend · serper.dev

## Hard rules (do not violate)

1. No HubSpot connection ever
2. No PHI, no HIPAA data
3. No LinkedIn scraping
4. No internal Adonis systems
5. No automated outreach to hospitals on behalf of reps

See `docs/AGENTS.md` for the full set of conventions, naming rules, signal taxonomy, and seed hospitals.
