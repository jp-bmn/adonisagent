# Adonis Account Intelligence — Demo Day Presentation Script

Welcome to the demo for **Adonis Account Intelligence**, an AI-native sales intelligence agent designed to find, classify, and deliver revenue cycle management (RCM) opportunities for our Account Executives (AEs).

---

## 1. What Problem Does Adonis Solve?
- **RCM Opportunities are Time-Sensitive**: Significant hospital events—such as leadership changes (e.g., CRO/CFO departures), EHR system go-lives (Epic cutovers), mergers and acquisitions (M&A), and major restructuring—drastically affect hospital billing and vendor contracts.
- **Manual Prospecting is Hard**: Sales teams have to sift through dozens of medical publications daily, manually identifying and validating triggers.
- **The Solution**: Adonis autonomously scrapes hospital news, classifies key events using a hybrid rules-and-AI classification engine, gates low-confidence items for human review, alerts AEs immediately about urgent events, and dispatches a compiled weekly digest with closed-loop UTM view tracking.

---

## 2. Hybrid AI Architecture: Rules Engine + LLM
To control operational latency and API costs, Adonis uses a two-stage hybrid pipeline:
1. **Deterministic Rules Engine (Luminai Enforce)**:
   - Evaluates incoming articles against a compiled set of regexes covering 8 specific revenue-touching patterns (e.g., leadership updates, go-lives, RCM hiring spikes).
   - Fies instantly (sub-millisecond, zero token cost) with high precision.
2. **LLM Cognitive Stage (Claude API)**:
   - If the rules engine does not match (e.g., complex financial events, bond debt restructurings), the signal falls through to `claude-sonnet-4-20250514`.
   - Claude evaluates the context, outputs standard JSON schemas, assigns confidence scores, and determines the sales relevance.

---

## 3. Core design patterns (Luminai)
Adonis implements four key agentic patterns:
* **Enforce (Rules Engine)**: Pre-filters clear-cut signals Deterministically.
* **Escalate (Immediate Alerting)**: Urgent signals (e.g., CRO departures) skip the weekly digest queue and are immediately dispatched to AEs via Slack DMs.
* **Human-in-the-Loop (Review Queue)**: Signals with low confidence scores (below 0.70) are placed in a review queue. The weekly digest dispatch is blocked until Danielle (admin) reviews and approves or dismisses them.
* **Closed-Loop (Engagement Tracking)**: AE digests include dashboard URLs decorated with UTM variables. Clicking the link triggers a public `POST /api/v1/digest-view` tracking endpoint, updating roster metrics to confirm when AEs read their digests.

---

## 4. Live System Walkthrough & Talking Points

Let's walk through the end-to-end system sequence:

### A. The Signal Feed & Scraper
1. Show the **signals feed** filtered for Michael's territory.
2. Trigger a synchronous run of the scraper:
   - Call `POST /api/v1/admin/run-scraper-sync` (authenticated via `X-API-Key`).
   - Show the returned summary: checks 5 hospitals, imports news, and updates metrics.

### B. Classification & Review Queue
1. Post a low-confidence signal (e.g. confidence=0.60):
   - Confirm it gets written with `review_status = 'pending'`.
2. Inspect Danielle's **Review Queue** (`GET /api/v1/signals/pending-review`).
3. Danielle approves the signal live (`POST /api/v1/signals/{id}/review` with action=approved).
   - The status updates to `approved`, freeing the digest queue.

### C. Digest Dispatching & Engagement
1. Run the weekly digest job:
   - Call `POST /api/v1/digests/send`.
   - Returns details on digests generated for AEs.
2. Simulate Michael clicking his Slack weekly digest button:
   - Post to `POST /api/v1/digest-view` with `digest_id` and Michael's `ae_id`.
3. Load the AE roster stats (`GET /api/v1/ae-users`):
   - Show that Michael's `last_viewed_digest` timestamp has successfully updated!

---

## 5. Live Metrics
The backend dashboard supports public endpoints to monitor service health:
- `GET /api/v1/status`: Displays total hospitals monitored (5), total signals stored, pending reviews, and the last run's status.
- `GET /api/v1/runs/latest`: Returns the run details of the latest scraper session.

---

## 6. What's Next?
- **Michael's Real Scrapers**: Transitioning from stubbed scrapers to Michael's real batch scraper pipeline via `/api/v1/signals/batch`.
- **Advanced Personalization**: Extending territory matching with custom AE vertical assignments (e.g., pediatrics vs. trauma systems).
