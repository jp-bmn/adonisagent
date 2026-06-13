# Adonis Backend — Signal Batch Ingestion Contract

**For:** Michael (Scraper Pipeline)
**From:** Joel (Backend)
**Date:** June 2026

---

## Endpoint

```
POST /api/v1/signals/batch
```

---

## Auth

**Bearer token** in the `Authorization` header:

```
Authorization: Bearer <INTERNAL_API_KEY>
```

In your `.env`:

```
SIGNALS_ENDPOINT_TOKEN=adonis-internal-dev-key-2026
```

> **Note:** During local dev, the URL is a localhost tunnel (see section below).
> For Railway production, the same token applies — Joel will share the Railway URL when deployed.

---

## Request Body

```json
{
  "run_context": {
    "run_id": "day2-run-001",
    "run_date": "2026-06-03",
    "scraper_version": "day2",
    "hospitals_scraped": 5
  },
  "signals": [
    {
      "hospital_name": "NewYork-Presbyterian",
      "title": "CRO John Smith departs NYP",
      "source_name": "Modern Healthcare",
      "source_url": "https://modernhealthcare.com/article-slug",
      "published_at_raw": "2026-06-01",
      "excerpt": "John Smith, Chief Revenue Officer at NYP, has announced his departure...",
      "matched_topics": ["leadership", "cro"],
      "extraction_stage": "filtered",
      "dedup_applied": true,
      "recency_applied": true
    }
  ]
}
```

### Field Notes

| Field              | Required | Notes                                                           |
| ------------------ | -------- | --------------------------------------------------------------- |
| `hospital_name`    | ✅       | Must fuzzy-match one of the 5 hospitals. See valid names below. |
| `title`            | ✅       | Max 200 characters                                              |
| `source_name`      | No       | Slack digest shows this as the citation                         |
| `source_url`       | No       | Used for deduplication — same URL + hospital = duplicate        |
| `published_at_raw` | No       | Any format: `2026-06-01`, `June 1, 2026`, ISO 8601              |
| `excerpt`          | No       | Mapped to `summary`. Max 1000 characters                        |
| `matched_topics`   | No       | List of topic strings — mapped to `signal_type` (see below)     |
| `extraction_stage` | No       | Logged, not stored                                              |
| `dedup_applied`    | No       | Logged, not stored                                              |
| `recency_applied`  | No       | Logged, not stored                                              |

### Valid Hospital Names (fuzzy-matched)

| Send any of...                                         | Resolves to |
| ------------------------------------------------------ | ----------- |
| `NewYork-Presbyterian`, `NYP`, `New York Presbyterian` | ✅          |
| `UMass Memorial`, `UMass`                              | ✅          |
| `Ascension`                                            | ✅          |
| `University of Arkansas Medical Sciences`, `UAMS`      | ✅          |
| `CommonSpirit Health`, `CommonSpirit`                  | ✅          |

### matched_topics → signal_type Mapping

| `matched_topics` value                                | → `signal_type`           |
| ----------------------------------------------------- | ------------------------- |
| `leadership`, `cro`, `cfo`, `vp_revenue`, `executive` | `leadership_change`       |
| `rcm_hiring`, `hiring_spike`, `revenue_cycle_hiring`  | `rcm_hiring_spike`        |
| `epic`, `epic_go_live`, `ehr_go_live`                 | `epic_go_live`            |
| `post_go_live`, `post_golive_friction`                | `post_golive_friction`    |
| `acquisition`, `merger`, `ma_acquisition`             | `ma_acquisition`          |
| `vendor_change`, `vendor`                             | `vendor_change`           |
| `vendor_dispute`                                      | `vendor_dispute`          |
| `restructuring`, `layoffs`                            | `restructuring`           |
| `financial`, `financial_event`, `earnings`            | `financial_event`         |
| `ai_adoption`, `automation`                           | `ai_adoption_outside_rcm` |
| `thought_leadership`                                  | `thought_leadership`      |
| _(unrecognized)_                                      | `filtered_out`            |

---

## Response — Success (HTTP 200)

```json
{
  "run_id": "day2-run-001",
  "received": 3,
  "inserted": 2,
  "duplicates": 1,
  "rejected": 0,
  "details": [
    { "index": 0, "status": "inserted", "reason": null, "signal_id": "dcb00752-9e35-4b5a-..." },
    {
      "index": 1,
      "status": "duplicate",
      "reason": "Signal with same source_url + hospital_id already exists",
      "signal_id": "prev-uuid"
    },
    { "index": 2, "status": "inserted", "reason": null, "signal_id": "new-uuid" }
  ]
}
```

### `details[].status` values

| Value       | Meaning                                                  |
| ----------- | -------------------------------------------------------- |
| `inserted`  | ✅ New signal stored in Supabase                         |
| `duplicate` | ⚠️ Same `source_url` + hospital already exists — skipped |
| `rejected`  | ❌ Missing required field or unknown hospital            |

---

## Response — Auth Error (HTTP 401)

```json
{ "detail": "Invalid or missing Bearer token. Set Authorization: Bearer <INTERNAL_API_KEY>" }
```

---

## Response — Validation Error (HTTP 422)

```json
{ "detail": "`signals` must be a list" }
```

---

## How to Test Locally (Right Now)

Joel's server is running at `localhost:8000`. To expose it to Michael:

### Option A — ngrok (recommended for quick test)

```bash
# Install ngrok: https://ngrok.com/download
brew install ngrok

# In terminal 1: start the backend
cd /Users/joel-bmn/adonisagent/backend
source .venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In terminal 2: start the tunnel
ngrok http 8000
# ngrok will print: Forwarding https://abc123.ngrok.io → localhost:8000
```

Then give Michael:

```
SIGNALS_ENDPOINT_URL=https://abc123.ngrok.io/api/v1/signals/batch
SIGNALS_ENDPOINT_TOKEN=adonis-internal-dev-key-2026
```

### Option B — Railway (permanent URL)

Deploy to Railway and give Michael the Railway URL.
The `.env` on Railway needs the same `INTERNAL_API_KEY=adonis-internal-dev-key-2026`.

---

## Verified Test Result

The endpoint was smoke-tested with a real CRO departure signal for NewYork-Presbyterian.

```
POST /api/v1/signals/batch → 200 OK
{
  "run_id": "test-001",
  "received": 1,
  "inserted": 1,
  "duplicates": 0,
  "rejected": 0,
  "details": [{ "index": 0, "status": "inserted", "signal_id": "dcb00752-..." }]
}
```

Signal is live in Supabase signals table. ✅

---

## Notes for Michael

- **Duplicate detection** is on `source_url + hospital_id`. If you send the same article twice, the second send returns `status: "duplicate"` — not an error.
- **Confidence score** defaults to `0.75` for all pipeline signals (auto-approved, no review queue). This will be replaced by the Claude classifier in Task 7.
- **Signal type** is inferred from `matched_topics[0]`. If none match, it defaults to `filtered_out`.
- **Hospital fuzzy matching** uses substring search — `"NYP"` will resolve to `NewYork-Presbyterian`.
