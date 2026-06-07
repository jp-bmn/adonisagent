/**
 * Confirmed seed hospitals for Phase 1.
 *
 * All five confirmed in writing: NewYork-Presbyterian, UMass Memorial, Ascension,
 * and University of Arkansas from the kickoff (May 11), CommonSpirit Health
 * added by Danielle Ferdon on May 19 (email to Joel Philip).
 *
 * Reed deliberately picked varied sizes and signal profiles. From the kickoff:
 * "I picked different sizes... it'll probably be much harder to find news on
 * the University of Arkansas Health Center than New York Presbyterian. But the
 * news that comes out of Arkansas is definitely more relevant."
 */

import type { Hospital } from './types';

type SeedHospital = Omit<Hospital, 'created_at' | 'updated_at'>;

export const SEED_HOSPITALS: SeedHospital[] = [
  {
    id: 'nyp',
    name: 'NewYork-Presbyterian Hospital',
    display_name: 'NewYork-Presbyterian',
    parent_system: null,
    state: 'NY',
    city: 'New York',
    website: 'https://www.nyp.org',
    newsroom_url: 'https://www.nyp.org/news',
    notes:
      'Large academic system; high news volume — good stress test for clinical-news filtering.',
  },
  {
    id: 'umass-memorial',
    name: 'UMass Memorial Health',
    display_name: 'UMass Memorial',
    parent_system: null,
    state: 'MA',
    city: 'Worcester',
    website: 'https://www.ummhealth.org',
    newsroom_url: 'https://www.ummhealth.org/news',
    notes: 'Academic medical center; Northeast territory.',
  },
  {
    id: 'ascension',
    name: 'Ascension Health',
    display_name: 'Ascension',
    parent_system: null,
    state: 'MO',
    city: 'St. Louis',
    website: 'https://www.ascension.org',
    newsroom_url: 'https://about.ascension.org/news',
    notes: 'Large Catholic health system; multi-state; known for active vendor reviews.',
  },
  {
    id: 'uams',
    name: 'University of Arkansas for Medical Sciences',
    display_name: 'UAMS',
    parent_system: null,
    state: 'AR',
    city: 'Little Rock',
    website: 'https://uamshealth.com',
    newsroom_url: 'https://news.uams.edu',
    notes:
      'Smaller news volume but high signal-to-noise — Reed flagged as the key comparison case.',
  },
  {
    id: 'commonspirit',
    name: 'CommonSpirit Health',
    display_name: 'CommonSpirit',
    parent_system: null,
    state: 'IL',
    city: 'Chicago',
    website: 'https://www.commonspirit.org',
    newsroom_url: 'https://www.commonspirit.org/newsroom',
    notes:
      'Added by Danielle Ferdon on May 19. ~140 hospitals across 24 states; 2019 CHI + Dignity Health merger. High news volume — ongoing integration, vendor consolidation, RCM news. Excellent stress test for signal scoring.',
  },
];
