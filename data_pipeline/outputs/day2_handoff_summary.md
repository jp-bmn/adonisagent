# Adonis Data Handoff Summary

Generated: 2026-06-04T15:56:51.100412+00:00

## Scope
- Hospitals: NewYork-Presbyterian, UMass Memorial
- Recency window (days): 365
- Dedup window (days): 30

## Counts
- Stored candidates: 6
- Rules-engine hits (provisional): 3
- Tier distribution:
  - urgent: 2
  - worth_knowing: 4
- Skip reasons:
  - duplicate_source_url: 1
  - no_topic_match: 2
  - noise_not_hospital_specific: 3
  - outside_recency_window: 8

## Per Hospital
- NewYork-Presbyterian: 3
- UMass Memorial: 3

## Top Candidate Signals
- [UMass Memorial] Bill Gates meets Willy Wonka: How Epic's 82-year-old billionaire CEO, Judy Faulkner, built her software factory | source=CNBC | topics=leadership, epic, revenue_cycle | url=https://www.cnbc.com/2025/08/16/how-epics-82-year-old-ceo-judy-faulkner-built-her-software-factory.html
- [NewYork-Presbyterian] New York-Presbyterian CEO Steven Corwin to step down | source=Crain's New York | topics=leadership, revenue_cycle | url=https://www.crainsnewyork.com/health-pulse/new-york-presbyterian-ceo-steven-corwin-announces-resignation/
- [NewYork-Presbyterian] JLL advises Weill Cornell Medicine on acquisition of Manhattan’s 1334 York Avenue | source=JLL | topics=acquisition, revenue_cycle | url=https://www.jll.com/en-us/newsroom/jll-advises-weill-cornell-medicine-on-acquisition-of-manhattans-1334-york-avenue
- [NewYork-Presbyterian] New generation of health system CEOs take the helm amid federal regulatory shift | source=Crain's New York | topics=leadership, revenue_cycle | url=https://www.crainsnewyork.com/health-pulse/new-york-presbyterian-northwell-nyu-langone-get-new-ceos/
- [UMass Memorial] Where is the OCR? | source=MedLearn Publishing | topics=revenue_cycle | url=https://icd10monitor.medlearn.com/where-is-the-ocr/
- [UMass Memorial] Get Well and RhythmX AI merge patient engagement and precision medicine | source=Healthcare IT News | topics=revenue_cycle | url=https://www.healthcareitnews.com/news/get-well-and-rhythmx-ai-merge-patient-engagement-and-precision-medicine

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
