# Roadmap

Week-by-week plan from kickoff to Demo Day. Updated when scope changes.

## Weeks 1–2 · Digest + dashboard live (May 19 – June 1)

**Goal:** A Monday email digest lands in Danielle's inbox with real signals from the 5 seed hospitals, and the dashboard shows the same data.

- [ ] Supabase project set up; schema + seed deployed
- [ ] Hospital newsroom scraper working for all 5 seed hospitals
- [ ] serper.dev source returning RCM-relevant news per hospital
- [ ] Becker's scraper via serper `site:` query
- [ ] LLM classifier wired to Claude, returning structured output
- [ ] Dedup working (no double-counted stories)
- [ ] Digest renderer producing readable HTML + plain text
- [ ] Resend wired; digest deliverable to a test inbox
- [ ] Dashboard signal feed page reads from DB
- [ ] Hospital list page reads from DB
- [ ] Hospital profile page shows real signals (no contacts yet)
- [ ] At least one full Mon/Wed/Fri scrape cycle completed end-to-end
- [ ] Signal quality reviewed with Danielle (precision feedback)

## June 2 · Midpoint review with Reed

**Goal:** Live demo of Phase 1; align on Phase 2 scope; confirm full hospital list; co-pilot feasibility decision.

Bring:

- Working dashboard URL
- Real Monday digest example (from the prior week's data)
- 1-page status doc with what's open
- Calendar invite for the rest of the cadence

## Weeks 3–4 · Full dashboard (June 3 – June 16)

**Goal:** All confirmed accounts loaded. Per-AE territory views working. Persistent profiles with leadership data.

- [ ] Full hospital list loaded (from Reed at midpoint)
- [ ] AE territory assignments configured (from Danielle)
- [ ] Per-rep filtered views in the dashboard
- [ ] Authentication for the 4 users (Danielle + 3 AEs)
- [ ] Contact ingestion — hospital leadership pages scraped
- [ ] "New" badge for recent leadership changes
- [ ] Signal history timeline on hospital profiles
- [ ] Per-rep digest variants (each AE gets only their territory)
- [ ] Urgent-signal instant alerts (email, possibly Slack if requested)

## Week 5 · Refinement + co-pilot start (June 17 – June 23)

**Goal:** Polish to a level where it could actually ship. Start co-pilot if ahead.

- [ ] HubSpot-ready CSV export
- [ ] Dashboard polish — typography, empty states, loading states
- [ ] Signal precision tuning (final pass with Danielle)
- [ ] End-to-end test with all 4 users
- [ ] Co-pilot prototype (chat interface, on-demand queries) — Phase 3 stretch
- [ ] Demo Day rehearsal Mon June 23 evening

## June 24 · Demo Day at Blackstone (6 PM)

- Live product running on real data
- Monday digest running on the actual cadence
- All four users with working accounts
- Backup recording in case of network issues
- 5-minute speech rehearsed

## After Demo Day

If Adonis wants to keep using it:

- Discuss handoff with Reed
- Document deployment + operating runbook
- Plan transition to their security review for any future internal integration

## Open items being tracked

- **AE territory assignments** — pending from Danielle (which hospitals to Michael/Jeff/David)
- **Source access** — confirm at midpoint which sources are reachable without paywall
- **Co-pilot scope** — formal commit/no-commit decision at the midpoint
- **Full hospital list** — Reed delivers before midpoint

## Risks

| Risk                                          | Mitigation                                                          |
| --------------------------------------------- | ------------------------------------------------------------------- |
| Source scraping breaks (sites change layouts) | Multiple source paths per hospital; LLM tolerant of input variation |
| LLM cost overrun                              | Cheap-first filtering before LLM call; cap at ~75 calls/week        |
| Signal quality too low                        | Mid-build Danielle review week 2; tune scoring before midpoint      |
| AE territory data slips                       | Build with placeholder territories; swap when delivered             |
| One teammate blocked / unavailable            | Pair on critical-path items; document everything; keep PRs small    |
