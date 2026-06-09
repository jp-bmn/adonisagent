

| INTERNAL Build Plan Not for client distribution | ADONIS ACCOUNT INTELLIGENCE TOOL Team Engineering PRD  ·  v2 Now includes Luminai platform enhancements · May 2026 |
| :---: | :---- |

| Field | Details |
| :---- | :---- |
| Project lead | Joel Philip — backend, architecture, agent orchestration, Slack delivery |
| Frontend | Juan Franco — dashboard UI, hospital profiles, territory views |
| Data | Michael Chabler — scrapers, signal extraction, LinkedIn discovery, PDF ingestion |
| Midpoint review | Tuesday, June 2, 2026 · 3:00 PM ET — live digest demo for Reed \+ Danielle |
| Demo Day | Wednesday, June 24, 2026 |
| Version | v2 — adds Luminai-sourced enhancements to signal review, rule engine, PDF ingestion, and digest tracking |

**1 · What Changed After Danielle’s Meeting**

Everything below supersedes the previous PRD drafts on the points where Danielle’s email conflicts or adds detail.

**Confirmed changes**

* Delivery: Slack DMs, not email. One combined message per AE, grouped by hospital account.

* Weekly cadence confirmed — digest sends Monday mornings.

* Hospital profiles: contact name, role, prior employer, hospital website link, LinkedIn profile URLs.

* HubSpot: Danielle manually updates when a new contact is identified. Tool never touches HubSpot.

* Fifth hospital confirmed: CommonSpirit — David’s territory.

* Co-pilot email drafting is off the table. On-demand chat (Phase 3\) is still valid.

**New signal types (added by Danielle)**

* Rev cycle hiring spikes, new hospital launches, post-go-live friction, restructuring language

* Vendor failure/disputes, AI adoption outside RCM, automation proof, named automation owners

* Public thought leadership by rev cycle leaders

**2 · Flags and Recommendations**

| FLAG | Weekly-only cadence creates a blind spot for urgent mid-week signals. Recommendation: scraper runs silently Mon / Wed / Fri. Digest delivers Monday only. Urgent-tier signals fire an immediate DM on detection. |
| :---: | :---- |

| FLAG | CommonSpirit covers 140+ hospitals in 28 states. Confirm with Danielle which specific division David is targeting before Michael builds that scraper. |
| :---: | :---- |

| FLAG | LinkedIn URLs cannot be scraped. Use serper.dev site:linkedin.com queries to surface candidate URLs. Store as unverified until Danielle confirms them. |
| :---: | :---- |

| FLAG | Jefferson Health is not formally confirmed. Do not build scrapers or territory logic for Jeff until Danielle confirms and provides his Slack user ID. |
| :---: | :---- |

| REC | Job posting monitoring is Phase 2\. Build the news signal pipeline first; add job board queries in week 3 after the digest is validated. |
| :---: | :---- |

| REC | Urgent signals should fire immediately, not wait for Monday. Worth Knowing signals aggregate weekly. This closes the cadence gap Danielle raised. |
| :---: | :---- |

**3 · Luminai-Inspired Enhancements**

A review of the Luminai healthcare automation platform surfaced four architectural patterns that improve our pipeline. Each maps directly to a weakness in the current build plan.

**3.1 · Signal review queue  —  Escalate low-confidence signals to Danielle**

Luminai routes ambiguous workflow exceptions to a human reviewer before they proceed. We apply the same pattern to low-confidence signals.

Currently, every classified signal goes straight into the digest regardless of how confident the Claude API classification was. When confidence is low, weak or irrelevant signals reach AEs and erode trust in the tool. Instead: any signal where Claude returns confidence below 0.70 is held in a Pending state. Danielle sees a small review queue in her admin dashboard each Monday before the digest fires. One click approves it into the digest or dismisses it permanently.

| What changes | Who | When |
| :---- | :---- | :---- |
| Add confidence\_score (float) and review\_status enum (pending / approved / dismissed) to signals table | Joel | Week 2 |
| Return confidence from Claude API classification call alongside tier and summary | Michael | Week 2 |
| Build ‘Pending review’ queue in Danielle’s admin view — approve / dismiss buttons | Juan | Week 3 |
| Digest send logic only includes signals where tier \!= filtered\_out AND (confidence \>= 0.70 OR review\_status \= approved) | Joel | Week 3 |

**3.2 · Deterministic rules layer  —  Enforce Danielle’s known priorities before the AI**

Luminai’s Enforce step applies SOPs and decision logic consistently, independently of probabilistic AI judgment. We replicate this with a rules engine that runs before the Claude API call.

Danielle has told us exactly which signal combinations are always urgent. Those should never be left to the AI to decide. A rules layer encodes them as hard logic: if the rule matches, the tier and confidence are set to their maximum values and the Claude call is skipped entirely, saving tokens and latency.

| Rule condition | Forced tier | Forced confidence |
| :---- | :---- | :---- |
| signal\_type \= leadership\_change AND role contains CRO, CFO, CRCO, or VP Revenue Cycle | urgent | 1.0 |
| signal\_type \= vendor\_dispute | urgent | 1.0 |
| signal\_type \= ma\_acquisition | urgent | 1.0 |
| signal\_type \= epic\_go\_live OR post\_golive\_friction | urgent | 1.0 |
| signal\_type \= restructuring | urgent | 1.0 |
| signal\_type \= rcm\_hiring\_spike AND 3+ postings in 7 days | urgent | 0.95 |
| signal\_type \= ai\_adoption\_outside\_rcm | worth\_knowing | 0.90 |
| signal\_type \= thought\_leadership | worth\_knowing | 0.85 |

Joel builds this as a Python function rules\_engine(article\_text, extracted\_type) → { tier, confidence } | None that runs before the Claude API call. Michael calls it first in the classification pipeline. If it returns a result, skip Claude. If it returns None, call Claude as normal.

**3.3 · PDF document ingestion  —  Unlock SEC filings and IRS Form 990s**

Luminai’s core problem is that 80% of health system data lives in unstructured documents. We have the same problem: SEC 8-K filings and IRS Form 990s are our best financial signal sources, but serper.dev returns PDF URLs that the current scraper cannot read.

Michael adds a PDF extraction step using pdfplumber (free, pip-installable) after serper.dev finds a filing URL. Extract the first 3,000 words of text, then pass it to the classification pipeline as a normal article. This immediately activates financial\_event signals from real filings rather than just news coverage of them.

| What changes | Who | When |
| :---- | :---- | :---- |
| pip install pdfplumber. Add extract\_pdf\_text(url) function that fetches and parses PDF text. | Michael | Week 3 |
| In the scraper, detect if a serper.dev result URL ends in .pdf. Route to extract\_pdf\_text instead of the HTML parser. | Michael | Week 3 |
| Pass extracted PDF text to the same classification pipeline as article text. Source\_name \= ‘SEC Filing’ or ‘IRS Form 990’. | Michael | Week 3 |
| No DB schema change needed — signals table already holds source\_name as a text field. | Joel | N/A |

**3.4 · Closed-loop digest visibility  —  Danielle knows when AEs open their digest**

Luminai closes every automated workflow by confirming the outcome back to the initiating party. Right now, Danielle’s digest fires and disappears — she has no way to know if Michael opened it or clicked through to the dashboard.

Joel adds UTM parameters to the dashboard link in each Slack digest (utm\_source=slack\&utm\_medium=digest\&utm\_campaign=weekly\&utm\_content=ae\_michael). The Next.js frontend captures these on page load and posts a view event to the API. Juan surfaces a “Last viewed” timestamp next to each AE in Danielle’s admin view.

| What changes | Who | When |
| :---- | :---- | :---- |
| Append UTM parameters to every dashboard link in Slack digest messages | Joel | Week 4 |
| Add digest\_views table: id, digest\_id, ae\_id, viewed\_at, utm\_source | Joel | Week 4 |
| On dashboard page load, POST /digest-view if UTM params are present. Store the event. | Joel \+ Juan | Week 4 |
| Add ‘Last viewed’ column to AE roster in Danielle’s admin dashboard. Show timestamp or ‘Not yet opened’. | Juan | Week 4 |

**4 · Users and Territory Map**

| User | Role | Hospitals (confirmed) |
| :---- | :---- | :---- |
| Danielle Ferdon | Admin — all accounts | All hospitals — compiles and sends weekly digest to AEs |
| Michael (AE) | Account executive | NewYork-Presbyterian, UMass Memorial |
| David (AE) | Account executive | Ascension, University of Arkansas, CommonSpirit\* |
| Jeff (AE) | Account executive | Jefferson Health — pending formal confirmation |

\* CommonSpirit territory must be scoped to a specific division before the scraper is built. See Section 2\.

**5 · System Architecture**

Three independent layers communicating through the database. Each team member owns one layer end-to-end. The rules engine (Section 3.2) sits at the boundary of Michael’s data layer and Joel’s backend.

| Data layer  —  Michael | Backend layer  —  Joel | Frontend layer  —  Juan |
| ----- | ----- | ----- |
| Scrapers (serper.dev, NewsAPI, RSS) PDF ingestion (pdfplumber) — NEW Rules engine (pre-AI tier assignment) — NEW Claude API classification \+ confidence LinkedIn URL discovery Deduplication \+ quality checks | FastAPI server \+ REST endpoints Supabase / PostgreSQL schema Weekly scheduler (Trigger.dev) Slack bot (DMs \+ urgent alerts) Digest view tracking (UTM) — NEW CSV export \+ run logging | Next.js 14 \+ TypeScript \+ Tailwind Dashboard (signal feed) Signal review queue (Danielle) — NEW Hospital profiles \+ territory views ‘Last viewed’ indicator in admin — NEW CSV export trigger \+ mobile layout |

**Tech stack**

| Layer | Technology | Notes |
| :---- | :---- | :---- |
| Frontend | Next.js 14, TypeScript, Tailwind, shadcn/ui | Juan. Vercel deploy. |
| Backend API | Python FastAPI | Joel. Better async for scraping \+ Claude API. |
| Database | Supabase (PostgreSQL) | Joel. Free tier sufficient for MVP. |
| Search / scraping | serper.dev \+ NewsAPI \+ RSS feeds | Michael. \~$0.001/query. |
| PDF extraction | pdfplumber (pip) | Michael. Free. Unlocks SEC \+ IRS filings. |
| Signal AI | Claude API (claude-sonnet-4-6) | Michael. Classification \+ summary after rules engine. |
| Scheduler | Trigger.dev | Joel. Managed async jobs with retry. |
| Slack | Slack Bolt SDK (Python) | Joel. DMs, urgent alerts, UTM-tagged digest links. |
| Deployment | Vercel (frontend) \+ Railway (backend) | \~$5/month total. |

**6 · Database Schema**

Joel owns the schema setup and migrations in Supabase. Fields marked NEW are additions from the Luminai enhancements in Section 3\.

| Table | Key columns | Owner |
| :---- | :---- | :---- |
| hospitals | id, name, website\_url, division\_note, created\_at | Joel |
| ae\_users | id, name, slack\_user\_id, is\_admin, created\_at | Joel |
| hospital\_ae\_assignments | hospital\_id, ae\_id, assigned\_at | Joel |
| contacts | id, hospital\_id, full\_name, role, prior\_employer, linkedin\_url, linkedin\_verified (bool), is\_active, created\_at | Michael writes / Joel API |
| signals | id, hospital\_id, signal\_type, tier, confidence\_score (float) NEW, review\_status (pending/approved/dismissed) NEW, title, summary, source\_url, source\_name, published\_date, created\_at, included\_in\_digest, urgent\_sent (bool) | Michael writes / Joel API |
| digests | id, ae\_id, sent\_at, slack\_message\_ts, week\_start, week\_end | Joel |
| digest\_views | id, digest\_id, ae\_id, viewed\_at, utm\_source NEW | Joel |
| agent\_runs | id, run\_at, hospitals\_checked, signals\_found, signals\_new, rules\_engine\_hits NEW, errors (jsonb), duration\_ms | Joel |

signal\_type enum: leadership\_change | rcm\_hiring\_spike | epic\_go\_live | post\_golive\_friction | ma\_acquisition | vendor\_change | vendor\_dispute | restructuring | new\_hospital\_launch | financial\_event | ai\_adoption\_outside\_rcm | automation\_proof | named\_automation\_owner | thought\_leadership

tier enum: urgent | worth\_knowing | filtered\_out

review\_status enum: pending | approved | dismissed  (only set when confidence\_score \< 0.70)

**7 · Role Assignments**

Items marked with ◆ are new additions from the Luminai enhancements.

**Joel  —  Project lead, backend, infrastructure**

| JOEL | Set up GitHub monorepo, environment variable structure, and deployment pipelines for Vercel (frontend) and Railway (backend). |
| :---: | :---- |
| **JOEL** | Design and migrate the Supabase database schema including the new confidence\_score, review\_status, digest\_views, and rules\_engine\_hits fields. |
| **JOEL** | Build the FastAPI server: GET /hospitals, GET /signals?ae\_id=, GET /contacts?hospital\_id=, GET /signals/pending-review, POST /signals/:id/review, POST /digest/send, GET /export/csv, POST /digest-view. |
| **JOEL** | Build the Python rules\_engine(article\_text, extracted\_type) function. Hardcode Danielle’s confirmed rules (see Section 3.2 table). Michael calls this before the Claude API. |
| **JOEL** | Build the Slack bot: weekly Monday digest DM per AE with UTM-tagged dashboard link, immediate urgent alert DM on detection, Danielle admin summary. |
| **JOEL** | ◆ Append UTM parameters (utm\_source, utm\_medium, utm\_campaign, utm\_content) to every dashboard link in Slack digest messages. Record view events in digest\_views table. |
| **JOEL** | Set up Trigger.dev for three weekly scraper runs: Mon 6 AM, Wed 6 AM, Fri 6 AM ET. Monday run also triggers digest send after confirming Danielle’s review queue is clear. |
| **JOEL** | Build digest send guard: Monday digest only fires after the review queue is empty (all pending signals are approved or dismissed). If queue is non-empty at 7:45 AM, Slack-DM Danielle a reminder to clear it. |
| **JOEL** | CSV export endpoint. Run logging including rules\_engine\_hits count per run. Code review of all Michael and Juan PRs. |

**Juan  —  Frontend, dashboard, UX**

| JUAN | Set up Next.js 14 with TypeScript, Tailwind, and shadcn/ui. Match Adonis brand: white background, dark teal headings, clean card components. |
| :---: | :---- |
| **JUAN** | Dashboard layout: left sidebar (hospital list, territory-filtered), main signal feed (urgency color-coded cards), hospital profile panel. |
| **JUAN** | Territory-filtered views: Danielle sees all hospitals across all AEs; each AE sees only their assigned accounts. |
| **JUAN** | Signal card component: urgency badge (Urgent red / Worth Knowing blue / Low gray), one-sentence summary, source link, hospital name, date. |
| **JUAN** | Hospital profile page: contact table (name, role, prior employer, website link, LinkedIn URL with verified badge), running signal history feed. |
| **JUAN** | ◆ Pending review queue in Danielle’s admin view: list of low-confidence signals awaiting approval. Each row shows the signal summary, source, confidence score, and Approve / Dismiss buttons. Calls POST /signals/:id/review. |
| **JUAN** | ◆ ‘Last viewed’ column in Danielle’s AE roster: shows timestamp of last dashboard visit from digest link, or ‘Not yet opened’. Reads from digest\_views table via API. |
| **JUAN** | ◆ On dashboard page load, check for UTM params. If present, POST /digest-view to record the event. No visible UI change needed for the AE. |
| **JUAN** | CSV export button. Mobile responsiveness (sidebar collapses on narrow screens). Co-pilot UI scaffold if Phase 1-2 are stable (stretch). |

**Michael  —  Data, scraping, signal extraction**

| MICHAEL | Set up serper.dev and NewsAPI accounts. Confirm API key limits before writing scraper logic. |
| :---: | :---- |
| **MICHAEL** | Build news scraper for all 5 confirmed hospitals using serper.dev. Query pattern: ‘\[Hospital\] revenue cycle OR leadership OR Epic OR acquisition’. Start with NYP and UMass. |
| **MICHAEL** | Set up RSS ingestion for Becker’s Hospital Review, Modern Healthcare, and Fierce Healthcare. Filter by hospital name before classification. |
| **MICHAEL** | Call Joel’s rules\_engine() function first in the classification pipeline. If it returns a tier result, store that and skip Claude. If it returns None, call Claude API. |
| **MICHAEL** | Claude API classification call: return signal\_type, tier, confidence\_score (0.0–1.0), one\_sentence\_summary, why\_relevant\_to\_adonis. Pass all fields to the signal storage API endpoint. |
| **MICHAEL** | ◆ PDF ingestion: after serper.dev returns a result URL ending in .pdf, call extract\_pdf\_text(url) using pdfplumber. Pass first 3,000 words to the classification pipeline. Set source\_name to ‘SEC Filing’ or ‘IRS Form 990’ accordingly. |
| **MICHAEL** | Deduplication: before storing a signal, check for matching source\_url or matching title \+ hospital within 30 days. Skip duplicates. |
| **MICHAEL** | LinkedIn URL discovery: serper.dev query ‘site:linkedin.com/in \[name\] \[hospital\]’ for each contact. Store top result as linkedin\_url with linkedin\_verified \= false. |
| **MICHAEL** | Hospital leadership scraping: scrape each hospital’s official website for CEO, CFO, CRO, VP Revenue Cycle. Store as contacts via API. |
| **MICHAEL** | Phase 2 — job posting monitoring: serper.dev queries for ‘site:linkedin.com/jobs \[hospital\] revenue cycle OR AR specialist OR denials’. Trigger rcm\_hiring\_spike if 3+ postings detected in 7 days. |
| **MICHAEL** | Signal quality log after each run: articles found, classified, rules-engine hits, stored, skipped with reasons. Joel surfaces in run log API. |

**8 · 6-Week Sprint Plan**

Items marked ◆ are Luminai enhancements. The June 2 midpoint is a hard deadline — live digest demo, no exceptions.

| Week | Joel — Backend | Juan — Frontend | Michael — Data |
| ----- | :---- | :---- | :---- |
| **Wk 1May 19–23** | GitHub repo \+ monorepoSupabase schema (incl. new fields)FastAPI skeleton \+ env varsSlack bot credentials \+ test DM◆ rules\_engine() function skeleton | Next.js project initTailwind \+ shadcn setupLayout shell \+ routingHospital list sidebar | serper.dev \+ NewsAPI setupTest queries for NYP \+ UMassRSS feed for Becker’sFirst raw signal extraction test |
| **Wk 2May 26–30** | Weekly scheduler (Trigger.dev)Slack DM digest formatterSignal storage API endpoints◆ Claude API call with confidence return◆ rules\_engine() rules hardcoded | Signal card componentsUrgency color-codingHospital profile page shellTabs: All / Urgent / Worth Knowing | Full scraper for all 5 hospitals◆ rules\_engine() integrated into pipelineClassification pipeline end-to-endDeduplication logic |
| **JUNE 2Midpoint** | Live digest demoAPI stable for frontendFirst real signals in DB | Dashboard demo-readyTerritory filter workingSignal cards on live data | Signal quality reportAll 5 hospitals scraped onceClassification accuracy review |
| **Wk 3June 2–6** | Territory-filtered API endpointsAdmin vs AE auth logicContact storage endpointsRun logging \+ rules\_engine\_hits◆ Digest send guard (review queue check) | ◆ Pending review queue UI for DanielleDanielle admin view (all accounts)Per-AE territory viewContact profile display | ◆ PDF ingestion (pdfplumber)LinkedIn URL discoveryHospital leadership page scrapingJob posting queries (basic) |
| **Wk 4June 9–13** | CSV export endpointUrgent alert DM (immediate send)Error handling \+ retry logic◆ UTM parameters on digest links◆ POST /digest-view endpoint \+ digest\_views table | Signal history viewCSV export buttonDashboard polishMobile responsive layout◆ UTM capture on page load → POST /digest-view◆ ‘Last viewed’ column in admin AE roster | Vendor dispute \+ AI adoption signalsThought leadership signal typeSignal confidence tuningNoise reduction |
| **Wk 5June 16–20** | Performance optimizationProduction deployment (Railway)Monitoring \+ alertingFinal index tuning | Final UX polishLoad time optimizationBug fixesCo-pilot scaffold (stretch) | Final taxonomy refinementFalse positive analysisFull run validation with DaniellePDF ingestion quality check |
| **JUNE 24Demo Day** | Production stableAll integrations liveDemo script ready | Dashboard at full fidelityAll views workingDemo walkthrough rehearsed | Data current as of June 23All 5 hospitals in systemQuality report ready |

**9 · Full Signal Taxonomy**

All 14 signal types. Michael’s classifier returns one of these strings. The rules engine (Section 3.2) forces tier and confidence for the top 8 before Claude is called.

| Signal type | Description | Default tier |
| :---- | :---- | :---- |
| leadership\_change | New hire or departure: CRO, CFO, CEO, CRCO, VP Revenue Cycle, Director RCM | Urgent (rules engine) |
| rcm\_hiring\_spike | 3+ job postings in 7 days: AR, denials, billing, patient registration, claims app roles | Urgent (rules engine) |
| ma\_acquisition | Merger, acquisition, system expansion, or divestiture | Urgent (rules engine) |
| vendor\_change | RCM outsourcing, new vendor contract, or vendor termination | Urgent (rules engine) |
| epic\_go\_live | Epic EHR go-live, major expansion, or migration | Urgent (rules engine) |
| post\_golive\_friction | Gaps between Epic and tools like Experian, RevSpring, or 3M | Urgent (rules engine) |
| restructuring | Leadership saying current RCM approach is not working; staff redeployment | Urgent (rules engine) |
| vendor\_dispute | Lawsuits, public vendor failures, claims missed due to billing/coding breakdowns | Urgent (rules engine) |
| new\_hospital\_launch | New hospital, major campus, or new service-line build | Worth knowing (Claude) |
| financial\_event | Earnings, margin pressure, credit rating change, bond disclosures — including from PDF filings | Worth knowing (Claude) |
| ai\_adoption\_outside\_rcm | AI in clinical or compliance but not yet in revenue cycle | Worth knowing (Claude) |
| automation\_proof | Coding automation or prior auth automation wins | Worth knowing (Claude) |
| named\_automation\_owner | Leader in RCM reporting, automation, performance excellence, or Epic-tied apps | Worth knowing (Claude) |
| thought\_leadership | Rev cycle leader speaks at Becker’s / HFMA, advisory boards, public AI in RCM posts | Worth knowing (Claude) |

**10 · Slack Digest Specification**

One combined Slack DM per AE, grouped by hospital, sent Monday 8:00 AM ET. Digest only fires after Danielle’s review queue is empty. Urgent alerts send immediately on detection, separate from the digest.

| Hi Michael 👋 Here is your weekly territory update for the week of May 19\. ──────────────────── \*NewYork–Presbyterian\* • \[URGENT\] New CRO appointed — Jessica Huang joins from Atlantic Health System. \[Becker’s Hospital Review\] • \[WATCH\] VP Revenue Cycle has transitioned out. Role currently open. \[NYP Newsroom\] \*UMass Memorial\* • \[WATCH\] Revenue cycle outsourcing partnership announced for two satellite campuses. \[Modern Healthcare\] ──────────────────── → View full dashboard: \[link?utm\_source=slack\&utm\_medium=digest\&utm\_campaign=weekly\&utm\_content=ae\_michael\] |
| :---- |

**Slack delivery rules**

* Digest fires Monday 8:00 AM ET. Guard: if review queue is non-empty at 7:45 AM, Slack-DM Danielle to clear it before send.

* Urgent alerts send immediately on detection — max one per hospital per day.

* Omit hospitals with no new signals from the digest. No placeholder text.

* All source links must be real URLs. Omit signal if source\_url is null.

* UTM parameters appended to every dashboard link. Format: utm\_source=slack, utm\_medium=digest, utm\_campaign=weekly, utm\_content=ae\_\[name\].

**11 · API and Tooling Reference**

| Tool / API | Purpose | Owner | Cost |
| :---- | :---- | :---- | :---- |
| serper.dev | News queries \+ LinkedIn URL discovery \+ PDF URL detection. \~100 free then $0.001/query. | Michael | \< $0.10/wk |
| NewsAPI | Aggregated news. Free tier: 100 req/day. | Michael | Free (MVP) |
| Becker’s RSS | Healthcare trade press. Most reliable for leadership news. | Michael | Free |
| pdfplumber (pip) | PDF text extraction for SEC 8-K \+ IRS Form 990 filings. NEW. | Michael | Free |
| Claude API (sonnet-4-6) | Signal classification \+ confidence scoring (after rules engine). | Joel prompt / Michael calls | \~$0.15/wk |
| Supabase | PostgreSQL DB \+ dashboard. Free tier: 500 MB. | Joel | Free (MVP) |
| Trigger.dev | Weekly scraper scheduler. Free tier. | Joel | Free (MVP) |
| Slack Bolt (Python) | DMs, urgent alerts, UTM-tagged digest links. | Joel | Free |
| Railway | Backend \+ worker deployment. Always-on. | Joel | \~$5/mo |
| Vercel | Frontend deployment. Free tier for Next.js. | Juan | Free (MVP) |
| GitHub | Version control. Feature branches; Joel reviews PRs. | All | Free |

**INTERNAL DOCUMENT — NOT FOR CLIENT DISTRIBUTION**

Joel Philip (lead) · Juan Franco · Michael Chabler  ·  Pursuit L3 AI Native Demo Day  ·  May 2026