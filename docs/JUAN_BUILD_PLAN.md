# Juan's Build Plan — Frontend Lead

## June 3 → June 24 · Demo Day at Blackstone

**Sources:** PRD (May 2026) + PRD Addendum v1 (June 2 midpoint). Where they conflict, addendum wins.

**My role:** Frontend / design lead. Dashboard, profile pages, signal UI, auth shell, export.
Not my work: agent pipeline, Supabase provisioning, scraper, digest email (Joel + Michael).

**Key dates**
| Date | Gate |
|------|------|
| June 10 (Tue) | Working demo for Reed — first hard deadline |
| June 17 (Tue) | Feature freeze — polish week starts |
| June 18 (Wed) | Danielle returns from PTO — territory assignments arrive |
| June 24 (Wed, 6 PM) | Demo Day at Blackstone |

**Branch naming:** `feat/t-XX-<topic>` · One PR per task · No direct pushes to main

---

## What's built vs. stubbed right now

**Real:** monorepo scaffold · shared types · signal taxonomy · seed data · DB query helpers
(`packages/db/src/queries.ts`) · Next.js layout + sidebar · page shells for all 5 routes

**Stubbed:** every page reads from the `SEED_HOSPITALS` constant — no Supabase client exists
in the web app · no signal card component · no urgency colors rendered · sidebar has no active
state · `/alerts` and `/export` are literal placeholder divs · no auth · no territory filter

---

## Week 1 — June 3–10 · Reed demo prep

> **Goal:** A live dashboard Reed can click through on June 10.
> These are the only tasks that must be done before Tuesday. Everything else can wait.

---

- [ ] **T-01 · Nav active state**
  - **Branch:** `feat/t-01-nav-active-state`
  - **What:** Add `usePathname()` to `Nav` in `layout.tsx`. Active link gets
    `bg-white/10 text-white`; idle links stay `hover:bg-white/5`. Needs a small
    `"use client"` boundary since `usePathname` is a client hook.
  - **Why here:** Unblocked, 30 minutes, and every demo screenshot looks broken without it.
  - **Needs from team:** Nothing.
  - **Estimate:** 30 min

---

- [ ] **T-02 · Signal card component**
  - **Branch:** `feat/t-02-signal-card`
  - **What:** Build `<SignalCard>` at `apps/web/src/components/SignalCard.tsx`.
    Props: `Signal` type from `@adonis/shared`. Renders:
    - Urgency badge — `urgent` = red (`bg-urgentBg text-urgent`), `standard` = blue
    - Headline + 2–3 sentence summary + rationale
    - Source link (opens in new tab), hospital name tag, `detected_at` date
    - Category label (e.g. "Leadership hire", "Epic event")

    Seed the component file with 2–3 hardcoded sample signals in a `__preview__` block
    at the bottom so it renders without a DB connection during development.
    Export through `src/components/index.ts`.

  - **Why here:** Everything downstream depends on this component — feed, alerts, profile.
    Build it first so the demo can show real-looking UI even if Michael's scraper hasn't
    run yet.
  - **Needs from team:** Nothing. Color tokens are already in `tailwind.config.js`.
  - **Estimate:** 3 h

---

- [ ] **T-03 · Supabase client in web app**
  - **Branch:** `feat/t-03-supabase-client`
  - **What:** Install `@supabase/ssr` and `@supabase/supabase-js` in `apps/web`.
    Create `apps/web/src/lib/supabase.ts` with:
    - `createServerClient()` — for Server Components and API routes
    - `createBrowserClient()` — for any future client components that need it

    Copy `.env.example` → `.env.local` and fill in values from Michael.

  - **Why here:** Every DB-wired page below depends on this. Cannot wire a single
    real query without it.
  - **Needs from Michael (ask now):**
    - `SUPABASE_URL`
    - `SUPABASE_ANON_KEY`
    - Confirmation that `schema.sql` + seed SQL has been deployed to the project
  - **Estimate:** 1 h once env vars are in hand

---

- [ ] **T-04 · Signal feed — live data**
  - **Branch:** `feat/t-04-signal-feed-live`
  - **What:** Wire `app/page.tsx` to call `listSignals(db, { limit: 20 })` from
    `packages/db/src/queries.ts`. Replace the static empty state with a rendered list
    of `<SignalCard>` components. Populate the 4 KPI tiles with real DB counts:
    - "Urgent this week" — signals where priority = urgent AND detected_at ≥ 7 days ago
    - "Updates this week" — standard signals, same window
    - "Accounts monitored" — count of hospitals
    - "Sources scanned" — count from most recent `agent_runs` row

    Show "Last refreshed" timestamp from the most recent `agent_runs` entry.
    Keep the seed-data empty state for when the DB returns zero rows.

  - **Why here:** This is the first thing Reed sees. Real signals = demo is 80% won.
  - **Needs from Michael:** T-03 complete + at least one scrape cycle run with signals
    in the DB.
  - **Estimate:** 2 h

---

- [ ] **T-05 · Hospitals list — live data**
  - **Branch:** `feat/t-05-hospitals-live`
  - **What:** Wire `app/hospitals/page.tsx` to call `listHospitals(db)` instead of
    `SEED_HOSPITALS`. Add two new columns to the table:
    - "Signals (7d)" — count of signals for that hospital in the past 7 days
    - An urgency dot (red) if any urgent signal exists in the past 7 days

    Keep `SEED_HOSPITALS` as the fallback if the DB fetch errors.

  - **Why here:** Reed will navigate here from the feed. Real counts make it credible.
  - **Needs from Michael:** T-03 complete.
  - **Estimate:** 2 h

---

- [ ] **T-06 · Hospital profile — live data**
  - **Branch:** `feat/t-06-hospital-profile-live`
  - **What:** Wire `app/hospitals/[id]/page.tsx` to the DB:
    - `getHospital(db, id)` for hospital metadata
    - `listSignals(db, { hospitalIds: [id] })` for signal history — render as
      `<SignalCard>` list
    - `listContactsForHospital(db, id)` for leadership section — show name,
      `role_title_raw`, `source_url` link. If contacts table is empty, show:
      "Leadership contacts loading — the agent is gathering data." (not an error)
  - **Why here:** Reed will click into at least one hospital. Signal history must
    show something real. Contacts can be empty with a good message.
  - **Needs from Michael:** T-03 complete + at least one scrape cycle run.
  - **Estimate:** 2 h

---

### Demo data — do this as soon as T-03 lands, not as a last resort

- [ ] **T-06b · Demo seed signals**
  - **Branch:** `feat/t-06b-demo-seed-signals`
  - **What:** Insert 8–10 realistic placeholder signals across all 5 seed hospitals
    directly into the DB using a SQL script at `packages/db/demo-seed.sql`. Do not
    wait to find out whether Michael's scraper is ready — seed it the moment T-03 is
    merged. Real scraped signals and seed signals coexist fine; if the pipeline runs
    before Tuesday the demo just has more data.

    Signal mix to cover:
    - At least 1 `LEADERSHIP_HIRE` (urgent) — e.g. new CFO at UMass Memorial
    - At least 1 `EPIC_EVENT` (urgent) — e.g. Epic go-live at CommonSpirit
    - At least 1 `VENDOR_CHANGE` (urgent) — e.g. RCM vendor swap at Ascension
    - 2–3 `FINANCIAL_PERFORMANCE` or `STRATEGY_CHANGE` (standard)
    - 1 `REFERENCE_MATERIAL` (standard) — Becker's article
    - Spread across all 5 hospitals so every row on `/hospitals` has a signal count

    Use real source URLs from Becker's or hospital newsrooms. Match the exact
    `Signal` schema from `packages/shared/src/types.ts`. Mark `delivered_in_digest`
    and `alert_fired` as `false`.

  - **Why:** Reed cannot see all-empty states. The scraper is Michael's pipeline with
    multiple moving parts — treat it as a bonus, not the plan.
  - **Needs from Michael:** T-03 complete (Supabase provisioned + env vars shared).
  - **Estimate:** 1.5 h

---

## Week 2 — June 10–17 · Full dashboard

> **Goal:** Everything committed in Phases 1 + 2 shipped and working before the freeze.
> Per the addendum, Phase 1 and 2 collapse into one sprint ending June 17.

---

- [ ] **T-07 · Alerts page**
  - **Branch:** `feat/t-07-alerts-page`
  - **What:** Build out `app/alerts/page.tsx`. Call
    `listSignals(db, { priority: 'urgent' })`. Render `<SignalCard>` list sorted by
    recency. Add "past 30 days" filter chip. Show urgent count next to the Alerts
    link in the sidebar.
  - **Why here:** `<SignalCard>` already exists and `listSignals` with priority filter
    is already in `queries.ts` — this is cheap to build once T-04 is done. Urgent
    signal visibility is central to the PRD value prop.
  - **Needs from team:** T-04 complete.
  - **Estimate:** 2 h

---

- [ ] **T-08 · Territory filter UI**
  - **Branch:** `feat/t-08-territory-filter`
  - **What:** Add a territory selector to the signal feed header (replacing the
    hardcoded "Admin (Danielle)" chip). Options: `All accounts` · `Michael` ·
    `Jeff` · `David`. Implement as a URL search param (`?ae=michael`) so it works
    with server components and is shareable. Filter calls `listHospitalsForUser()`
    and scopes `listSignals()` to those hospital IDs.

    **Territory data note:** Danielle is OOO until June 18 — territory assignments
    (which hospitals → Michael/Jeff/David) arrive after the feature freeze. Build the
    UI and filtering logic now using placeholder hospital assignments so the UI is
    fully functional. Wire real assignments when Danielle delivers during polish week.

  - **Needs from Michael:** `users` table + `user_hospitals` junction populated
    (even with placeholder territory data). Ask Michael to seed placeholder assignments
    by June 10.
  - **Estimate:** 2 h

---

- [ ] **T-09 · Contact badges**
  - **Branch:** `feat/t-09-contact-badges`
  - **What:** Polish the contacts section on the hospital profile. For each contact:
    show `full_name`, `role_title_raw`, `start_date` if known, `prior_employer` if
    known, and `source_url` as a linked "source" pill. Add a green `NEW` badge when
    `is_recent_change === true`. Sort by role importance: CRO → CFO →
    VP_REV_CYCLE → COO → CIO → CEO → OTHER.
  - **Why here:** "People first, organization second" is the PRD's stated philosophy.
    This is the most valuable section on a profile page for a rep about to make a call.
  - **Needs from Michael:** Contact ingestion running — contacts table must have rows.
  - **Estimate:** 2 h

---

- [ ] **T-10 · Signal history timeline**
  - **Branch:** `feat/t-10-signal-timeline`
  - **What:** Upgrade the hospital profile signal list into a visual timeline. Group
    signals by week with date headers ("This week", "Last week", then specific dates).
    Add a vertical connector line and a color dot per signal matching its urgency.
    Card body stays `<SignalCard>`.
  - **Why here:** "Persistent profiles that accumulate a running signal history over
    time" is explicit Phase 2 scope. The timeline makes the persistence legible — and
    Reed praised the visual direction, so polish matters here.
  - **Needs from team:** T-06 complete.
  - **Estimate:** 2 h

---

- [ ] **T-11 · Auth — login page + session**
  - **Branch:** `feat/t-11-auth-login`
  - **What:** `/login` page with Supabase Auth email+password sign-in. Next.js
    middleware that redirects unauthenticated users to `/login`. Logged-in user's
    name and role shown in sidebar footer (replace the hardcoded "Danielle" chip).
    Territory filter (T-08) auto-sets to the AE's assigned territory on login; admin
    sees all.
  - **Why here:** The 4 users need separate logins for Demo Day. Danielle (admin)
    sees everything; each AE sees only their hospitals.
  - **Needs from Michael:** Supabase Auth enabled on the project + 4 user records
    created in the `users` table with matching Supabase Auth accounts.
  - **Estimate:** 3 h

---

- [ ] **T-12 · Export — HubSpot CSV download**
  - **Branch:** `feat/t-12-export-csv`
  - **What:** Build `app/export/page.tsx` with a download button. Add an API route
    at `app/api/export/route.ts` that queries all signals + contacts and streams a
    CSV response. Columns: hospital name · contact name · role · signal headline ·
    category · source URL · detected date. Add a date-range selector (this week /
    this month / all time) on the page.
  - **Why here:** "Export a HubSpot-ready CSV on demand" is explicit PRD scope.
  - **Needs from team:** T-03 complete (Supabase client).
  - **Estimate:** 2 h

---

- [ ] **T-13 · Chat assistant (co-pilot)**
  - **Branch:** `feat/t-13-chat-assistant`
  - **What:** The chat interface promoted from stretch to committed at the June 2
    midpoint. Call it "chat assistant" in all UI copy — Reed initially confused
    "Copilot" with Microsoft Copilot (addendum §4).

    **UI:** A slide-in chat panel accessible from any page via a button in the
    sidebar footer (or a fixed `?` icon). Message list + streaming input box.
    Render assistant messages as they stream in — don't wait for the full response.
    Each assistant message renders inline source citations as clickable links.

    **API route:** `app/api/chat/route.ts` — calls the Anthropic SDK with streaming
    - tool use. Pass the logged-in user's role and territory in the system prompt on
      every request so the assistant naturally scopes to what they should see (admin
      sees everything, an AE sees only their hospitals).

    **Tools the assistant can call** (each tool calls the existing DB query helpers
    in `packages/db/src/queries.ts`):
    - `query_signals` — `listSignals()` filtered by hospital, category, date range
    - `get_hospital_profile` — `getHospital()` + `listContactsForHospital()`
    - `list_recent_signals` — `listSignals({ since, priority })`
    - `draft_digest` — assembles signals into a formatted email digest for review

    **Source citation rule:** Every answer that references a signal must include the
    `source_url`. If the model can't cite a source, it says so rather than asserting.

  - **Why here:** Committed Demo Day feature per the addendum. Sequenced after T-11
    (auth) because user role + territory must be available to scope every chat prompt.
    Sequenced after T-12 (export) so all Phase 1+2 features are merged before this
    goes in.
  - **Needs from team:**
    - T-11 (auth) complete — user session needed for role/territory context
    - Michael: `ANTHROPIC_API_KEY` in the server environment (Railway / Vercel env)
  - **Estimate:** 6 h

---

## Week 3 — June 17–24 · Polish only

> Feature freeze June 17. No new components or routes — fix, tune, and rehearse.

---

- [ ] **T-14 · Loading states**
  - **Branch:** `feat/t-14-loading-states`
  - **What:** Add `loading.tsx` files alongside each async page (Next.js App Router
    convention). Show skeleton card placeholders that match the real layout during DB
    fetch. Prevents layout shift on slower connections at Blackstone.
  - **Estimate:** 1.5 h

---

- [ ] **T-15 · Empty states**
  - **Branch:** `feat/t-15-empty-states`
  - **What:** Audit every zero-data scenario: feed with no signals · hospital with
    no history · alerts page with no urgent signals · profile with no contacts.
    Replace any remaining generic copy with on-brand, helpful messages.
  - **Estimate:** 1 h

---

- [ ] **T-16 · Polish pass + wire real territory data**
  - **Branch:** `feat/t-16-polish-pass`
  - **What:** Two things in one PR:
    1. Final Tailwind pass — spacing consistency, readable at 13" laptop size,
       any rough edges from Danielle/AE feedback. Reed said "If it looks and works
       like that, you guys did a great job" — hold that bar.
    2. Swap placeholder territory assignments for real ones when Danielle delivers
       (~June 18). Update `user_hospitals` seed or coordinate with Michael to update
       the DB.
  - **Estimate:** 2 h

---

- [ ] **T-17 · Demo Day prep**
  - **Branch:** `feat/t-17-demo-prep`
  - **What:** Update root README with: live URL · login credentials for each of the
    4 users · how to reset demo state if a scrape run corrupts data the morning of
    June 24 · backup recording instructions in case of network issues at Blackstone.
  - **Estimate:** 30 min

---

## Blockers to surface to the team now

| What I need                                         | From                | Needed by | Blocks                    |
| --------------------------------------------------- | ------------------- | --------- | ------------------------- |
| SUPABASE_URL + SUPABASE_ANON_KEY                    | Michael             | ASAP      | T-03 and everything after |
| Schema + seed SQL deployed to Supabase              | Michael             | ASAP      | T-03                      |
| At least one scrape cycle with real signals         | Michael             | June 9    | T-04, T-06                |
| `users` + `user_hospitals` seeded (placeholders ok) | Michael             | June 10   | T-08, T-11                |
| Supabase Auth configured + 4 user accounts          | Michael             | June 10   | T-11                      |
| Contact ingestion running                           | Michael             | June 10   | T-09                      |
| `ANTHROPIC_API_KEY` in server environment           | Michael             | June 10   | T-13                      |
| Real territory assignments (Michael/Jeff/David)     | Danielle (via Joel) | June 18   | T-16                      |

---

## Reed demo — minimum viable set (June 10)

Reed is reviewing a working dashboard. These are the only tasks that **must** look real:

| Task                       | Why it's required                                      |
| -------------------------- | ------------------------------------------------------ |
| T-01 Nav active state      | Without it the sidebar looks broken                    |
| T-02 Signal card           | The visual centerpiece — everything else is decoration |
| T-03 Supabase client       | Prerequisite for all live data                         |
| T-04 Signal feed live      | First page Reed sees                                   |
| T-05 Hospitals list live   | He will click here                                     |
| T-06 Hospital profile live | He will drill into at least one hospital               |

Territory filter, auth, alerts, export, contacts polish, timeline — all can be shown
as "shipping this week" during the Reed demo. The signal feed and one hospital
drill-down are enough to prove the concept.

---

## Chat assistant — now T-13 in Week 2

The chat assistant was promoted from stretch to committed at the June 2 midpoint
(addendum §4). It is **T-13** in this plan, sequenced after T-12 in Week 2. See the
full task definition above. Name it "chat assistant" in all UI copy — Reed initially
heard "Copilot" as Microsoft Copilot (addendum §4 naming note).

---

_Updated June 2, 2026 · Juan Franco · incorporates PRD Addendum v1_
