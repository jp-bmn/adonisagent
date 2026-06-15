# Sprint Log — Adonis Account Intelligence

Living record of what shipped, decisions made, and what's next.
Updated at the end of every session.

**Demo Day:** June 24, 2026 at Blackstone
**Build-complete deadline:** June 18, 2026
**Repo:** ~/projects/adonisagent
**Stack:** Next.js 15 · FastAPI · Supabase · Claude · Tailwind · Railway

---

## Backlog (prioritized — not yet built)

| Priority | Item | Owner | Notes |
|---|---|---|---|
| 🔴 High | Hide `filtered_out` signals from main feed | Juan | One-line filter in page.tsx |
| 🔴 High | Alerts page hospital filter | Juan | Dropdown same as territory filter |
| 🟡 Medium | Make signal cards tap-to-open article on mobile | Juan | Wrap card in `<a>` |
| 🟡 Medium | Jefferson Health visited-link style fix | Juan | CSS visited state leaking |
| 🟡 Medium | Page `<title>` tags per route | Juan | Browser tab polish |

---

## Future Enhancements (post-Demo Day)

### Hermes
- **Proactive signal nudge** — notify rep when new signal arrives since last session
- **Auto briefing on login** — Hermes opens with day's briefing automatically on first login
- **Conversation history panel** — tap history icon, see all past chats grouped by day/time, tap to reload, option to delete individual or all. Like ChatGPT sidebar.
- **Email send integration** — draft goes straight to Gmail/Outlook via OAuth instead of copy-paste

### Platform
- **AE default territory view** — feed auto-filters to logged-in AE's hospitals on load
- **Admin-only Review gate** — hide Review nav from AEs, only show to `isAdmin` users
- **Expand monitoring** — provider groups + customer success (Reed's request)
- **Job posting monitoring** — serper.dev for `rcm_hiring_spike` signals
- **Automate contacts pipeline** — Michael runs manually now
- **Deployment + operating runbook** — for Adonis handoff post-demo
- **End-to-end test** — all 4 real users (Danielle, David, Michael, Jeff)

---

## Sprint 13 — Jun 15, 2026

### Juan (Frontend)

**Shipped**
- PR #35 — Export page relabeled: "Signals CSV" → "Contacts CSV", filename fix, description updated
- PR #36 — Mobile top bar: logged-in user initials (DF avatar) in mobile header
- PR #37 — Mobile polish + bug sweep (merged multiple fixes):
  - Hospitals list: table → mobile card list (logo + name + chevron)
  - Hospital detail: section padding `p-4 md:p-6`, border fix for mobile stacking
  - Contacts layout: name above LinkedIn link, fallback "Unknown contact" for empty names
  - Hospital name in signal cards on profile page (was showing raw UUID)
  - Desktop nav: added Review, renamed "Export (CSV)" → "Export"
  - HTML tags stripped from signal titles (SignalCard + ReviewQueue)
  - Review queue: snake_case → readable signal type labels
  - Hospital profile header: stats move below name on mobile (no more crowding)
  - Skeleton loader for hospital profile page (`/hospitals/[id]/loading.tsx`)
  - Hermes signal context: add summary + source URL, exclude `filtered_out`, richer format
  - Hermes: renders markdown links `[text](url)` as clickable `<a>` tags
  - Hermes: passes contacts (name, title, LinkedIn, email) for all hospitals
  - Hermes: territory-aware — filters signals + contacts to logged-in user's hospitals
  - Hermes: starter prompts when chat is empty (Brief me, Who to call, Draft email, What's urgent)
  - Hermes: "⚡ Brief me on my territory" auto-send button
  - Hermes: email draft detection — styled box + "📋 Copy to clipboard" button
  - Hermes: `isAdmin` passed from UserProvider so Danielle sees all 6 hospitals
  - Hermes: system prompt updated with briefing/calling/email draft behaviors
  - Hermes: max_tokens bumped to 1024 for richer briefings

**Decisions Made**
- Starter prompts auto-send on tap (don't just fill the input) — faster for demo
- Email detection uses `Subject:` line presence — simple, reliable, no special API marker needed
- Territory context uses `isAdmin` from UserProvider rather than detecting from `ae_users` — Danielle isn't in `ae_users` as an AE so detection was failing
- `filtered_out` signals excluded from Hermes context — they're noise, not intel

**Open GitHub Issues (assigned)**
| # | Issue | Owner |
|---|---|---|
| #31 | KPI trend delta fields not returning from `/status` | Joel |
| #38 | Contact names empty across all hospital profiles | Michael |
| #39 | Test signal "Ignore Me 4" showing in prod | Joel |
| #40 | Signal titles falling back to signal type label | Joel |
| #41 | Signals attributed to wrong hospitals | Joel |
| #42 | Signal type miscategorization (Epic go-live on AI/lawsuit articles) | Joel |

### Joel (Backend)
- Working on issues #31, #39, #40, #41, #42

### Michael (Data Pipeline)
- Issue #38: contact names empty — pipeline not saving `name` field

---

## Sprint 12 — Jun 13, 2026

### Juan (Frontend)

**Shipped (PRs #23–#30)**
- F-01: Removed `@anthropic-ai/sdk` from lockfile
- F-03: Renamed CoPilot → Hermes throughout
- F-04: Category pills on signal cards
- F-05: Sort toggle (urgent / recent / hospital A–Z)
- F-06: Category filter chips with horizontal scroll
- F-07: Territory selector + SidebarUser component (GET /me live)
- F-08: Hermes live signal context (Joel fixed #18 + #19)
- F-09: Review queue approve/dismiss wired
- F-10: Hospital staff profiles contact table
- F-11: Export contacts CSV (`/export/csv` live)
- F-12: UTM tracking / Last viewed
- Empty states on signal feed (category + no signals)
- Skeleton loader (loading.tsx) matching real page layout
- Hermes markdown renderer (bullet lists, bold, numbered lists)
- Hermes bubble clamps to viewport on window resize
- KPI colored top stripes (3px per tile)
- KPI trend pills wired to Joel's delta fields
- Hospital logos via Logo.dev API

**Decisions Made**
- Raw fetch for Anthropic API — no SDK to keep bundle lean (per PRD)
- URL search params for all filter state — shareable links, no React state needed
- `loading.tsx` convention for skeleton loaders — Next.js handles it automatically

---

## Notes for Next Session

- Commit PR #37 branch (all Hermes work + mobile polish — not yet pushed to PR)
- Joel needs to merge PRs #35, #36, #37 before June 18
- Once Michael fixes #38 (contact names), Hermes contact lookups become fully functional
- Demo Day talking points: mention Review queue admin gate, AE territory default, proactive nudge as "what's next" answers
