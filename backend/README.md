# Adonis Intelligence Backend

Internal sales intelligence API for Adonis. Monitors hospital news, classifies triggers using a hybrid rules-and-AI pipeline, manages AE territories, and delivers weekly digests via Slack.

---

## Tech Stack

- **Framework**: FastAPI (Python 3.9+)
- **Database**: Supabase (PostgreSQL client)
- **AI Classification**: Anthropic SDK (Claude 3.5 Sonnet)
- **Messaging**: Slack Bolt SDK
- **Task Runner**: APScheduler (in-process)
- **Testing**: Pytest & Pytest-Asyncio

---

## Project Structure

```text
backend/
├── app/
│   ├── api/            # API endpoints (V1)
│   ├── core/           # Config, database connections, auth, and cache utilities
│   ├── jobs/           # APScheduler and background scraping jobs
│   ├── models/         # Pydantic schemas
│   └── services/       # Core services (rules engine, Slack messaging, classifier)
├── migrations/         # SQL DDL schemas for Supabase
├── scripts/            # Seed and validation scripts
└── tests/              # Pytest test suite (187 unit/E2E integration tests)
```

---

## Local Setup

### 1. Create and Activate Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Setup Environment Variables

Copy `.env.example` to `.env` and fill in your API credentials:

```bash
cp .env.example .env
```

Required fields in `.env`:

- `SUPABASE_URL` & `SUPABASE_KEY`: Supabase project database connection.
- `SLACK_BOT_TOKEN` & `SLACK_SIGNING_SECRET`: Slack Application credentials.
- `SLACK_USER_ID_DANIELLE`: User ID of the primary administrator for review alerts.
- `ANTHROPIC_API_KEY`: Anthropic Claude API key.
- `INTERNAL_API_KEY`: Key protecting admin endpoints (e.g. `POST /api/v1/admin/run-scraper-sync`).

---

## Database Schema & Seeding

### 1. Initialize Tables

Run the SQL DDL commands in `migrations/001_initial_schema.sql` inside your Supabase Project **SQL Editor** to create the initial tables, indexes, and triggers.

### 2. Seed Database

Run the seed script to populate hospitals, account executives, and territory assignments:

```bash
python scripts/seed_db.py
```

### 3. Verify Database State

Run the verification script to confirm tables are correctly populated:

```bash
python scripts/verify_seed.py
```

---

## Running the Application

Start the FastAPI development server:

```bash
uvicorn app.main:app --reload
```

The server will run locally at `http://127.0.0.1:8000`. Documentation will be accessible at `/docs`.

---

## Running the Test Suite

The repository includes a comprehensive unit and integration test suite containing **187 passing tests**.

### Run All Tests

```bash
pytest
```

### Run Integration Tests Only (requires real credentials in `.env`)

```bash
pytest -v tests/test_e2e.py
```

_Note: If no real credentials are set in the environment, the integration pipeline tests will be skipped automatically._
