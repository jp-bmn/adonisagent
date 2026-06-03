# PRD · Account Intelligence Tool

> **Status:** Final draft submitted for approval.
> **Source:** Reflects everything learned across two partner meetings and Danielle Ferdon's workflow walkthrough on May 19, 2026.
> **Date:** May 2026

| Field | Details |
|---|---|
| Prepared for | Reed Kalash, Director of Growth & Revenue Operations · Danielle Ferdon, Partnerships |
| Prepared by | Juan Franco, Joel Philip & Michael Chabler · Pursuit L3 |
| Midpoint review | Tuesday, June 2, 2026 · 3:00 PM ET |
| Demo Day | Wednesday, June 24, 2026 at Blackstone |

Our ask: confirm this is the right direction, or tell us what to change. A full technical specification follows the midpoint review.

---

## 1 · The Problem

Today, researching hospital prospects is reactive and manual. Danielle currently uses **Glean** — an internal AI tool — to query news and signals on individual accounts, but only when a call is already scheduled. By the time the intelligence reaches an account executive, it is sometimes three weeks old. Accounts that aren't already in an active conversation fall off the radar entirely.

Three things make this worth solving now:

- **Timing** — a new revenue or finance leader typically re-evaluates vendor relationships within 90 days. A signal caught late is an opportunity missed.
- **Scale** — Danielle supports three account executives across 30–50 hospital accounts. Manual research across that universe cannot keep pace.
- **Consistency** — research only happens before calls. Accounts without scheduled calls receive no monitoring.

She often has to dig through extraneous information before getting to the core information she needs.

---

## 2 · Who It's For

Four Adonis team members will use this tool directly.

| User | Role |
|---|---|
| **Danielle Ferdon** | Partnerships / senior BDR. Admin view across all accounts. Compiles the weekly digest and sends it to the relevant AE each Monday. SME on current research workflow. |
| **Michael** (AE) | Territory-filtered dashboard, his hospital accounts only. Receives Danielle's Monday digest. Can check the dashboard independently throughout the week. |
| **Jeff** (AE) | Same as above, separate territory. |
| **David** (AE) | Same as above, separate territory. |

**People first, organization second.** The most valuable intelligence is about people — who leads revenue and finance, who just arrived, who just left. Hospital profiles center on those decision-makers, with org-level events as context.

---

## 3 · What We're Building

One system, three delivery layers. Phases 1 and 2 are committed scope for Demo Day. Phase 3 is a stretch feature.

### Phase 1 · Dashboard + Monday email digest — ships first

The dashboard is the anchor. It displays every account, every signal, and the full news history — filtered by territory for each AE, with full visibility for Danielle. Signals are color-coded by urgency. Each signal shows a one-sentence summary and a hyperlinked source. Click through for more detail.

Every Monday morning, the agents run a full sweep of all accounts and compile a digest. Danielle receives it, reviews it, and forwards the relevant sections to each AE. The email hyperlinks back to the live dashboard.

**Profile format:** Account name + one or two bullet-point sentence summaries + hyperlinked source per signal. AEs know what to do with the signal — they do not need a deep dive.

### Phase 2 · Territory views + persistent profiles

Each AE's dashboard is personalized to their hospital list. Hospital profile pages accumulate a running signal history over time. Danielle retains an admin view across all accounts and all territories.

### Phase 3 · Co-pilot — stretch feature

A chat interface layered on top of the dashboard. Danielle or an AE can ask on-demand questions ("what happened with UMass Memorial this month?"), request historical backtracking by custom date range, and prompt the co-pilot to draft the weekly email digest. The co-pilot knows who each user is and personalizes its responses to their territory.

---

## 4 · What the Tool Monitors

| Tier | Coverage |
|---|---|
| **Urgent** (instant alert) | New revenue or finance leader hired or departed (CRO, CFO, VP Revenue Cycle, Director RCM) · Merger, acquisition, or system expansion · Revenue-cycle vendor or outsourcing change · Epic or EHR go-live, migration, or expansion · Financial-review or regulatory event · Significant hiring of billing or RCM operations staff |
| **Worth knowing** (weekly digest) | Revenue-cycle strategy or performance changes · RCM automation or AI initiatives · Partnerships and joint ventures · Financial performance and margin pressure · Leadership changes outside revenue · Meeting-prep reference items (interviews, podcasts, trade coverage) |
| **Filtered out** | Equipment and facility purchases · Clinical or research program news · Community events, philanthropy, and awards · General AI news not specific to revenue cycle |

---

## 5 · Sources

Public sources only — no private records, PHI, or HIPAA-protected data. Every signal links to its original source so AEs can verify before acting.

| Source | Examples |
|---|---|
| Health system official | Hospital newsrooms, press releases, leadership and about pages — highest reliability for verified personnel changes |
| Healthcare trade press | Becker's Hospital Review / Health IT · Modern Healthcare · Fierce Healthcare · Healthcare Dive · RevCycleIntelligence · Health Affairs |
| Financial & regulatory | SEC filings, bond disclosures, IRS Form 990, official financial statements |
| News aggregation APIs | **serper.dev** (pennies per search) · NewsAPI · GDELT · RSS feeds from all sources above |
| Major business press | Bloomberg Health, Reuters Health, WSJ Health — subject to paywall access |

---

## 6 · Scope

| The tool will | The tool will not |
|---|---|
| Monitor the agreed hospital list — agents run 2–3x weekly | Connect to or write to HubSpot (list is provided; output is CSV for manual upload) |
| Send a Monday morning email digest to Danielle for distribution | Access any private, patient, or PHI / HIPAA-protected data |
| Provide a web dashboard with territory-filtered views | Scrape LinkedIn or replicate Sales Navigator |
| Build hospital profiles: account name, signal bullets, source links | Send outreach emails on behalf of reps |
| Export a HubSpot-ready CSV on demand | Monitor hospitals outside the agreed list |

**Stretch — Phase 3:** Co-pilot chat for on-demand queries, email drafting, historical signal search. Discussed positively with Danielle on May 19; delivery contingent on Phase 1 and 2 being stable.

---

## 7 · Build Plan

| Phase | Milestone | Delivered |
|---|---|---|
| Wk 1–2 | Digest + dashboard live | Working Monday email digest and dashboard for 5 seed hospitals. Color-coded urgency. Territory views. Signal quality validated with Danielle. |
| **June 2** | Midpoint review | Live demo to Reed and Danielle. Align on Phase 2 scope, full hospital list, co-pilot feasibility. |
| Wk 3–4 | Full dashboard | All confirmed accounts loaded. Persistent profiles. Per-AE territory views for Michael, Jeff, David. |
| Wk 5 | Refinement + co-pilot start | Dashboard polish. Co-pilot prototype if Phase 1–2 are stable. |
| **June 24** | Demo Day | Full product on live data. Monday digest running. Dashboard live for all four users. |

### Performance targets

- Digest cadence: Monday at 8:00 AM ET, weekly, zero manual input
- Dashboard refresh: agents run Mon, Wed, Fri — data never more than 48 hours old
- Signal latency: urgent signals appear in dashboard within 24 hours of public reporting
- Profile accuracy: each signal verified against at least one named source before display
- Signal precision: high enough that Danielle trusts the digest and does not re-query Glean to verify
- Export speed: HubSpot-ready CSV generated in under 5 minutes

---

## 8 · Open Items

- **From Danielle** — confirmation of AE territory assignments so the dashboard filters correctly from day one
- **Source access** — Bloomberg and WSJ are paywalled. We assume RSS-level access for now and will confirm at the midpoint
- **Co-pilot scope** — discussed positively May 19 but not formally committed. Prototype decision at the midpoint

---

## 9 · What Success Looks Like

Danielle opens her inbox on Monday morning and has a pre-organized digest ready to forward to each AE — without touching Glean, without searching a single website. The AEs check the dashboard when they need more detail. No account goes unwatched because a call hasn't been scheduled yet.

- Danielle no longer re-queries Glean before calls — the digest has already done the work
- AEs enter every call aware of the most recent signal for that account
- Urgent signals (new CRO, acquisition, Epic go-live) surface within 24 hours of public reporting
- The Monday digest posts every week with zero manual research required
- Any account can be fully briefed in under 60 seconds from the dashboard
- Signal precision is high enough that reps trust the output and do not revert to manual lookup
