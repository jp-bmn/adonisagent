-- =============================================================================
-- Adonis Account Intelligence Tool — Full Database Schema
-- Run this in Supabase SQL Editor: Dashboard → SQL Editor → New Query → Run
-- =============================================================================

-- Enable UUID extension (already enabled on Supabase, but safe to re-run)
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- =============================================================================
-- DROP existing tables (for clean re-runs in development)
-- Comment these out in production!
-- =============================================================================
DROP TABLE IF EXISTS digest_views CASCADE;
DROP TABLE IF EXISTS digests CASCADE;
DROP TABLE IF EXISTS signals CASCADE;
DROP TABLE IF EXISTS contacts CASCADE;
DROP TABLE IF EXISTS hospital_ae_assignments CASCADE;
DROP TABLE IF EXISTS ae_users CASCADE;
DROP TABLE IF EXISTS hospitals CASCADE;
DROP TABLE IF EXISTS agent_runs CASCADE;

-- =============================================================================
-- HOSPITALS
-- =============================================================================
CREATE TABLE hospitals (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name        text NOT NULL,
    website_url text,
    division_note text,
    account_type text NOT NULL DEFAULT 'hospital',
    created_at  timestamptz NOT NULL DEFAULT now()
);


-- =============================================================================
-- AE USERS
-- =============================================================================
CREATE TABLE ae_users (
    id             uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name           text NOT NULL,
    slack_user_id  text,
    is_admin       boolean NOT NULL DEFAULT false,
    created_at     timestamptz NOT NULL DEFAULT now()
);

-- =============================================================================
-- HOSPITAL <-> AE ASSIGNMENTS
-- =============================================================================
CREATE TABLE hospital_ae_assignments (
    hospital_id  uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    ae_id        uuid NOT NULL REFERENCES ae_users(id) ON DELETE CASCADE,
    assigned_at  timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (hospital_id, ae_id)
);

-- =============================================================================
-- CONTACTS
-- =============================================================================
CREATE TABLE contacts (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id       uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    full_name         text NOT NULL,
    role              text,
    prior_employer    text,
    linkedin_url      text,
    linkedin_verified boolean NOT NULL DEFAULT false,
    is_active         boolean NOT NULL DEFAULT true,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now()
);

-- Auto-update updated_at on PATCH
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = now();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER contacts_updated_at
    BEFORE UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- SIGNALS
-- =============================================================================
CREATE TABLE signals (
    id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    hospital_id          uuid NOT NULL REFERENCES hospitals(id) ON DELETE CASCADE,
    signal_type          text NOT NULL,
    tier                 text NOT NULL CHECK (tier IN ('urgent', 'worth_knowing', 'filtered_out')),
    confidence_score     float NOT NULL DEFAULT 0.0,
    review_status        text CHECK (review_status IN ('pending', 'approved', 'dismissed')),
    title                text,
    summary              text,
    why_it_matters       text,
    source_url           text,
    source_name          text,
    published_date       date,
    created_at           timestamptz NOT NULL DEFAULT now(),
    included_in_digest   boolean NOT NULL DEFAULT false,
    urgent_sent          boolean NOT NULL DEFAULT false
);

-- Index for common query patterns
CREATE INDEX idx_signals_hospital_id     ON signals(hospital_id);
CREATE INDEX idx_signals_tier            ON signals(tier);
CREATE INDEX idx_signals_review_status   ON signals(review_status);
CREATE INDEX idx_signals_created_at      ON signals(created_at DESC);

-- =============================================================================
-- DIGESTS
-- =============================================================================
CREATE TABLE digests (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    ae_id             uuid REFERENCES ae_users(id) ON DELETE SET NULL,
    sent_at           timestamptz,
    slack_message_ts  text,
    week_start        date,
    week_end          date
);

CREATE INDEX idx_digests_ae_id ON digests(ae_id);

-- =============================================================================
-- DIGEST VIEWS (UTM closed-loop tracking)
-- =============================================================================
CREATE TABLE digest_views (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    digest_id   uuid REFERENCES digests(id) ON DELETE CASCADE,
    ae_id       uuid REFERENCES ae_users(id) ON DELETE CASCADE,
    viewed_at   timestamptz NOT NULL DEFAULT now(),
    utm_source  text
);

CREATE INDEX idx_digest_views_ae_id     ON digest_views(ae_id);
CREATE INDEX idx_digest_views_digest_id ON digest_views(digest_id);

-- =============================================================================
-- AGENT RUNS
-- =============================================================================
CREATE TABLE agent_runs (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    run_at            timestamptz NOT NULL DEFAULT now(),
    hospitals_checked int NOT NULL DEFAULT 0,
    signals_found     int NOT NULL DEFAULT 0,
    signals_new       int NOT NULL DEFAULT 0,
    rules_engine_hits int NOT NULL DEFAULT 0,
    errors            jsonb,
    duration_ms       int
);

-- =============================================================================
-- SEED DATA
-- =============================================================================

-- Hospitals
INSERT INTO hospitals (name, website_url, division_note) VALUES
    ('NewYork-Presbyterian',                    'https://nyp.org',               NULL),
    ('UMass Memorial',                          'https://umassmemorial.org',      NULL),
    ('Ascension',                               'https://ascension.org',          NULL),
    ('University of Arkansas Medical Sciences', 'https://uams.edu',               NULL),
    ('CommonSpirit Health',                     'https://commonspirit.org',       'Specific division TBD — confirm with Danielle before expanding scraper scope');

-- AE Users (slack_user_id values filled in via .env — stored here as references)
INSERT INTO ae_users (name, slack_user_id, is_admin) VALUES
    ('Danielle Ferdon', 'PLACEHOLDER_DANIELLE', true),
    ('Michael',         'PLACEHOLDER_MICHAEL',  false),
    ('David',           'PLACEHOLDER_DAVID',    false),
    ('Jeff',            'PLACEHOLDER_JEFF',      false);

-- Hospital <-> AE assignments
-- NewYork-Presbyterian → Michael
-- UMass Memorial       → Michael
-- Ascension            → David
-- University of AR     → David
-- CommonSpirit         → David
INSERT INTO hospital_ae_assignments (hospital_id, ae_id)
SELECT h.id, u.id
FROM (VALUES
    ('NewYork-Presbyterian',                    'Michael'),
    ('UMass Memorial',                          'Michael'),
    ('Ascension',                               'David'),
    ('University of Arkansas Medical Sciences', 'David'),
    ('CommonSpirit Health',                     'David')
) AS mapping(hospital_name, user_name)
JOIN hospitals h ON h.name = mapping.hospital_name
JOIN ae_users  u ON u.name = mapping.user_name;

-- =============================================================================
-- VERIFICATION QUERY — run after migration to confirm counts
-- =============================================================================
SELECT
    (SELECT count(*) FROM hospitals)                AS hospitals,
    (SELECT count(*) FROM ae_users)                 AS ae_users,
    (SELECT count(*) FROM hospital_ae_assignments)  AS assignments,
    (SELECT count(*) FROM contacts)                 AS contacts,
    (SELECT count(*) FROM signals)                  AS signals,
    (SELECT count(*) FROM digests)                  AS digests,
    (SELECT count(*) FROM digest_views)             AS digest_views,
    (SELECT count(*) FROM agent_runs)               AS agent_runs;
-- Expected: 5, 4, 5, 0, 0, 0, 0, 0
