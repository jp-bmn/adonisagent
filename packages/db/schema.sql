-- ============================================================================
-- Adonis Account Intelligence — Database Schema
-- ============================================================================
-- Run this in your Supabase project SQL editor.
-- Designed for the final PRD: 5 seed hospitals, 4 users (Danielle admin + 3 AEs),
-- email digest as primary delivery, agents run Mon/Wed/Fri.
-- ============================================================================

-- Extensions
create extension if not exists "uuid-ossp";
create extension if not exists vector;  -- for future semantic search over signal history

-- ============================================================================
-- HOSPITALS — the prospect accounts we monitor
-- ============================================================================
create table if not exists hospitals (
  id              text primary key,           -- short stable slug, e.g. 'nyp', 'commonspirit'
  name            text not null,              -- legal name
  display_name    text not null,              -- short display label
  parent_system   text,                       -- nullable for standalone systems
  state           text not null,              -- 2-letter US state
  city            text,
  website         text,
  newsroom_url    text,                       -- direct newsroom URL when known
  notes           text,
  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now()
);

create index if not exists hospitals_state_idx on hospitals (state);

-- ============================================================================
-- CONTACTS — people at hospitals (revenue / finance leadership)
-- ============================================================================
create type revenue_role as enum (
  'CRO', 'CFO', 'VP_REV_CYCLE', 'COO', 'CIO', 'CEO', 'OTHER'
);

create table if not exists contacts (
  id                 uuid primary key default uuid_generate_v4(),
  hospital_id        text not null references hospitals(id) on delete cascade,
  full_name          text not null,
  role               revenue_role not null,
  role_title_raw     text not null,           -- exact title as scraped, pre-normalization
  prior_employer     text,
  start_date         date,
  source_url         text,
  is_recent_change   boolean not null default false,
  created_at         timestamptz not null default now(),
  updated_at         timestamptz not null default now()
);

create index if not exists contacts_hospital_idx on contacts (hospital_id);
create index if not exists contacts_recent_change_idx on contacts (is_recent_change) where is_recent_change;

-- ============================================================================
-- SIGNALS — individual pieces of intelligence about hospitals
-- ============================================================================
create type signal_category as enum (
  -- urgent
  'LEADERSHIP_HIRE',
  'LEADERSHIP_DEPARTURE',
  'MERGER_ACQUISITION',
  'VENDOR_CHANGE',
  'EPIC_EVENT',
  'REGULATORY',
  -- standard
  'STRATEGY_CHANGE',
  'AUTOMATION_INITIATIVE',
  'PARTNERSHIP',
  'FINANCIAL_PERFORMANCE',
  'LEADERSHIP_OTHER',
  'REFERENCE_MATERIAL'
);

create type signal_priority as enum ('urgent', 'standard', 'noise');

create table if not exists signals (
  id                    uuid primary key default uuid_generate_v4(),
  hospital_id           text not null references hospitals(id) on delete cascade,
  contact_id            uuid references contacts(id) on delete set null,
  category              signal_category not null,
  priority              signal_priority not null,
  headline              text not null,
  summary               text not null,        -- LLM-generated, ~2-3 sentences
  rationale             text not null,        -- "why this matters" for the rep
  source_url            text not null,        -- mandatory - every signal must be verifiable
  source_type           text not null,        -- 'beckers', 'newsapi', 'hospital_newsroom', etc.
  published_at          timestamptz,
  detected_at           timestamptz not null default now(),
  score                 integer not null check (score >= 0 and score <= 100),
  delivered_in_digest   boolean not null default false,
  alert_fired           boolean not null default false,
  -- dedup: same signal from multiple sources should not double-count
  content_hash          text,
  created_at            timestamptz not null default now(),
  updated_at            timestamptz not null default now()
);

create index if not exists signals_hospital_idx on signals (hospital_id);
create index if not exists signals_priority_idx on signals (priority);
create index if not exists signals_detected_at_idx on signals (detected_at desc);
create index if not exists signals_undelivered_idx on signals (delivered_in_digest) where not delivered_in_digest;
create unique index if not exists signals_content_hash_idx on signals (content_hash) where content_hash is not null;

-- ============================================================================
-- USERS — Danielle (admin) and the three AEs
-- ============================================================================
create type user_role as enum ('admin', 'ae');

create table if not exists users (
  id                     uuid primary key default uuid_generate_v4(),
  full_name              text not null,
  email                  text not null unique,
  role                   user_role not null,
  territory              text,                -- nullable for admin; required for AEs
  created_at             timestamptz not null default now(),
  updated_at             timestamptz not null default now()
);

-- ============================================================================
-- TERRITORIES — which hospitals each AE owns
-- ============================================================================
create table if not exists user_hospitals (
  user_id         uuid not null references users(id) on delete cascade,
  hospital_id     text not null references hospitals(id) on delete cascade,
  assigned_at     timestamptz not null default now(),
  primary key (user_id, hospital_id)
);

create index if not exists user_hospitals_user_idx on user_hospitals (user_id);
create index if not exists user_hospitals_hospital_idx on user_hospitals (hospital_id);

-- ============================================================================
-- DIGESTS — Monday email summaries built by the agents and reviewed by Danielle
-- ============================================================================
create table if not exists digests (
  id                  uuid primary key default uuid_generate_v4(),
  user_id             uuid not null references users(id) on delete cascade,
  week_of             date not null,           -- the Monday this digest is for
  signal_ids          uuid[] not null,
  rendered_html       text not null,
  rendered_text       text not null,
  email_message_id    text,                    -- provider message-id when sent
  status              text not null default 'draft' check (status in ('draft', 'sent', 'failed')),
  sent_at             timestamptz,
  created_at          timestamptz not null default now(),
  updated_at          timestamptz not null default now()
);

create unique index if not exists digests_user_week_idx on digests (user_id, week_of);

-- ============================================================================
-- AGENT_RUNS — observability for the Mon/Wed/Fri scrape jobs
-- ============================================================================
create table if not exists agent_runs (
  id              uuid primary key default uuid_generate_v4(),
  source_type     text not null,              -- which scraper ran
  started_at      timestamptz not null default now(),
  finished_at     timestamptz,
  status          text not null default 'running' check (status in ('running', 'success', 'failure')),
  items_found     integer default 0,
  signals_created integer default 0,
  error_message   text,
  metadata        jsonb
);

create index if not exists agent_runs_started_at_idx on agent_runs (started_at desc);
create index if not exists agent_runs_source_status_idx on agent_runs (source_type, status);

-- ============================================================================
-- updated_at triggers
-- ============================================================================
create or replace function set_updated_at() returns trigger as $$
begin
  new.updated_at = now();
  return new;
end;
$$ language plpgsql;

create trigger hospitals_updated_at before update on hospitals
  for each row execute function set_updated_at();
create trigger contacts_updated_at before update on contacts
  for each row execute function set_updated_at();
create trigger signals_updated_at before update on signals
  for each row execute function set_updated_at();
create trigger users_updated_at before update on users
  for each row execute function set_updated_at();
create trigger digests_updated_at before update on digests
  for each row execute function set_updated_at();
