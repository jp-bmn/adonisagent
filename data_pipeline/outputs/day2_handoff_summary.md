# Adonis Data Handoff Summary

Generated: 2026-06-06T16:58:43.111704+00:00

## Scope

- Hospitals: NewYork-Presbyterian, UMass Memorial, Ascension, University of Arkansas, CommonSpirit
- Recency window (days): 365
- Dedup window (days): 30

## Counts

- Stored candidates: 9
- Rules-engine hits (provisional): 3
- Tier distribution:
  - urgent: 3
  - worth_knowing: 6
- Skip reasons:
  - duplicate_source_url: 22
  - no_topic_match: 5
  - noise_not_hospital_specific: 4
  - outside_recency_window: 11

## Per Hospital

- NewYork-Presbyterian: 2
- UMass Memorial: 3
- Ascension: 1
- University of Arkansas: 3
- CommonSpirit: 0

## Top Candidate Signals

- [UMass Memorial] Bill Gates meets Willy Wonka: How Epic's 82-year-old billionaire CEO, Judy Faulkner, built her software factory | source=CNBC | topics=leadership, epic, revenue_cycle | url=https://www.cnbc.com/2025/08/16/how-epics-82-year-old-ceo-judy-faulkner-built-her-software-factory.html
- [NewYork-Presbyterian] New York-Presbyterian CEO Steven Corwin to step down | source=Crain's New York | topics=leadership, revenue_cycle | url=https://www.crainsnewyork.com/health-pulse/new-york-presbyterian-ceo-steven-corwin-announces-resignation/
- [NewYork-Presbyterian] JLL advises Weill Cornell Medicine on acquisition of Manhattan’s 1334 York Avenue | source=JLL | topics=acquisition, revenue_cycle | url=https://www.jll.com/en-us/newsroom/jll-advises-weill-cornell-medicine-on-acquisition-of-manhattans-1334-york-avenue
- [UMass Memorial] Epic et al. dismiss a defendant in patient-data lawsuit | source=Healthcare IT News | topics=epic, revenue_cycle | url=https://www.healthcareitnews.com/news/epic-et-al-dismiss-defendant-patient-data-lawsuit
- [University of Arkansas] Community Health Systems Completes $110M Sale of Four Arkansas Hospitals to Freeman Health System | source=Digital Health News | topics=acquisition, revenue_cycle | url=https://www.digitalhealthnews.com/community-health-systems-completes-110m-sale-of-four-arkansas-hospitals-to-freeman-health-system-
- [University of Arkansas] Arkansas Children’s Names Alison Ziari SVP of Practice Plan, President of PSO | source=Arkansas Money & Politics | topics=leadership, revenue_cycle | url=https://armoneyandpolitics.com/arkansas-childrens-alison-ziari/
- [UMass Memorial] Trump's 'big beautiful bill' creates potential dilemma for UMass Memorial Health leader | source=Worcester Telegram | topics=leadership | url=https://www.telegram.com/story/news/2025/07/03/trumps-big-beautiful-bill-creates-dilemma-for-umass-memorial-health/84447201007/
- [Ascension] Industry Voices—A healthcare experience that is as seamless as it is soulful | source=Fierce Healthcare | topics=revenue_cycle | url=https://www.fiercehealthcare.com/providers/industry-voices-healthcare-experience-seamless-it-soulful
- [University of Arkansas] 40% of Arkansas Hospitals Report Losses in 2024 as Costs Outpace Revenues | source=Arkansas Business | topics=revenue_cycle | url=https://www.arkansasbusiness.com/article/arkansas-hospitals-strained-obbba/

## Next Step

- Feed these candidates into rules-engine and classification in the next milestone.

## Lead QA Snapshot

- Lead count: 13
- Recommended for manual review: 7
- Rejected low-score matches: 4
- Match bucket counts: {'high': 7, 'medium': 2, 'low': 0, 'missing': 4}
- Review markdown: outputs/day2_contact_leads_review.md
- Review CSV: outputs/day2_contact_leads_review.csv

### Top Rejected Examples

- Earnings Send | hospital=CommonSpirit | score=0.05 | reason=below_minimum_threshold=0.20
- Clear Warning | hospital=CommonSpirit | score=0.05 | reason=below_minimum_threshold=0.20
- Steven Corwin | hospital=NewYork-Presbyterian | score=0.05 | reason=below_minimum_threshold=0.20
