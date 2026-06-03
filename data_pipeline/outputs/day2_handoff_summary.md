# Adonis Data Handoff Summary

Generated: 2026-06-03T16:00:48.808294+00:00

## Scope
- Hospitals: NewYork-Presbyterian, UMass Memorial
- Recency window (days): 365
- Dedup window (days): 30

## Counts
- Stored candidates: 9
- Rules-engine hits (provisional): 6
- Tier distribution:
  - urgent: 5
  - worth_knowing: 4
- Skip reasons:
  - duplicate_source_url: 1
  - no_topic_match: 2
  - noise_not_hospital_specific: 2
  - outside_recency_window: 6

## Per Hospital
- NewYork-Presbyterian: 3
- UMass Memorial: 6

## Top Candidate Signals
- [UMass Memorial] Bill Gates meets Willy Wonka: How Epic's 82-year-old billionaire CEO, Judy Faulkner, built her software factory | source=CNBC | topics=leadership, epic, revenue_cycle | url=https://www.cnbc.com/2025/08/16/how-epics-82-year-old-ceo-judy-faulkner-built-her-software-factory.html
- [NewYork-Presbyterian] New York-Presbyterian CEO Steven Corwin to step down | source=Crain's New York | topics=leadership, revenue_cycle | url=https://www.crainsnewyork.com/health-pulse/new-york-presbyterian-ceo-steven-corwin-announces-resignation/
- [NewYork-Presbyterian] JLL advises Weill Cornell Medicine on acquisition of Manhattan’s 1334 York Avenue | source=JLL | topics=acquisition, revenue_cycle | url=https://www.jll.com/en-us/newsroom/jll-advises-weill-cornell-medicine-on-acquisition-of-manhattans-1334-york-avenue
- [NewYork-Presbyterian] New generation of health system CEOs take the helm amid federal regulatory shift | source=Crain's New York | topics=leadership, revenue_cycle | url=https://www.crainsnewyork.com/health-pulse/new-york-presbyterian-northwell-nyu-langone-get-new-ceos/
- [UMass Memorial] Healthcare Providers and Epic Act to Safeguard Patients’ Health Information | source=Epic Systems | topics=epic, revenue_cycle | url=https://www.epic.com/epic/post/what-you-put-up-with-is-what-you-stand-for/
- [UMass Memorial] UMass Memorial Health reaches new contract with Blue Cross Blue Shield of MA | source=Worcester Telegram | topics=leadership, revenue_cycle | url=https://www.telegram.com/story/business/2025/11/13/umass-memorial-health-blue-cross-new-contract/87248300007/
- [UMass Memorial] Epic, health care providers sue over alleged misuse of patient records | source=WPR | topics=epic, revenue_cycle | url=https://www.wpr.org/news/epic-health-care-providers-sue-over-alleged-misuse-patient-records
- [UMass Memorial] How five AI startups are strategizing around Epic’s big push | source=Modern Healthcare | topics=epic, revenue_cycle | url=http://www.modernhealthcare.com/health-tech/ai/mh-epic-ai-tools-abridge-innovaccer-ambience/
- [UMass Memorial] Can your health records be sold for profit? A lawsuit says it’s happening. | source=The Washington Post | topics=epic | url=https://www.washingtonpost.com/health/2026/01/22/electronic-health-record-fraud-lawsuit/

## Next Step
- Feed these candidates into rules-engine and classification in the next milestone.

## Lead QA Snapshot
- Lead count: 3
- Recommended for manual review: 1
- Rejected low-score matches: 2
- Match bucket counts: {'high': 1, 'medium': 0, 'low': 0, 'missing': 2}
- Review markdown: outputs/day2_contact_leads_review.md
- Review CSV: outputs/day2_contact_leads_review.csv

### Top Rejected Examples
- Steven Corwin | hospital=NewYork-Presbyterian | score=0.05 | reason=below_minimum_threshold=0.20
- Judy Faulkner | hospital=UMass Memorial | score=0.05 | reason=below_minimum_threshold=0.20
