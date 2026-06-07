-- ============================================================================
-- Seed data — run after schema.sql against a fresh Supabase project
-- ============================================================================

-- The 5 confirmed seed hospitals
insert into hospitals (id, name, display_name, parent_system, state, city, website, newsroom_url, notes) values
  ('nyp', 'NewYork-Presbyterian Hospital', 'NewYork-Presbyterian', null, 'NY', 'New York',
    'https://www.nyp.org', 'https://www.nyp.org/news',
    'Large academic system; high news volume.'),
  ('umass-memorial', 'UMass Memorial Health', 'UMass Memorial', null, 'MA', 'Worcester',
    'https://www.ummhealth.org', 'https://www.ummhealth.org/news',
    'Academic medical center; Northeast.'),
  ('ascension', 'Ascension Health', 'Ascension', null, 'MO', 'St. Louis',
    'https://www.ascension.org', 'https://about.ascension.org/news',
    'Large Catholic health system; multi-state; active vendor reviews.'),
  ('uams', 'University of Arkansas for Medical Sciences', 'UAMS', null, 'AR', 'Little Rock',
    'https://uamshealth.com', 'https://news.uams.edu',
    'Smaller news volume; high signal-to-noise.'),
  ('commonspirit', 'CommonSpirit Health', 'CommonSpirit', null, 'IL', 'Chicago',
    'https://www.commonspirit.org', 'https://www.commonspirit.org/newsroom',
    'Confirmed by Danielle Ferdon, May 19. ~140 hospitals across 24 states.')
on conflict (id) do nothing;

-- The 4 users: Danielle (admin) + Michael, Jeff, David (AEs)
-- Replace email addresses with the real ones once confirmed.
insert into users (full_name, email, role, territory) values
  ('Danielle Ferdon', 'danielle.ferdon@adonis.io', 'admin', null),
  ('Michael',         'michael@adonis.io',         'ae',    'TBD - Territory 1'),
  ('Jeff',            'jeff@adonis.io',            'ae',    'TBD - Territory 2'),
  ('David',           'david@adonis.io',           'ae',    'TBD - Territory 3')
on conflict (email) do nothing;

-- NOTE: AE territory assignments (which hospitals belong to which AE) are an
-- open item per the PRD - "From Danielle: Confirmation of AE territory assignments"
-- Once confirmed, populate user_hospitals here.
