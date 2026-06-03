# Adonis Data Handoff Summary

Generated: 2026-06-02T16:13:15.442368+00:00

## Scope
- Hospitals: NewYork-Presbyterian, UMass Memorial
- Recency window (days): 365
- Dedup window (days): 30

## Counts
- Stored candidates: 3
- Rules-engine hits (provisional): 2
- Tier distribution:
  - urgent: 2
  - worth_knowing: 1
- Skip reasons:
  - duplicate_source_url: 5
  - no_topic_match: 2
  - noise_not_hospital_specific: 4
  - outside_recency_window: 6

## Per Hospital
- NewYork-Presbyterian: 2
- UMass Memorial: 1

## Top Candidate Signals
- [UMass Memorial] Epic's lawsuit against Health Gorilla raises broader issues about the future of data sharing, industry executives say | source=Fierce Healthcare | topics=epic, revenue_cycle | url=https://www.fiercehealthcare.com/health-tech/epics-lawsuit-against-health-gorilla-raises-broader-issues-about-future-data-sharing
- [NewYork-Presbyterian] NewYork-Presbyterian CEO is retiring, successor named | source=Chief Healthcare Executive | topics=leadership | url=https://www.chiefhealthcareexecutive.com/view/newyork-presbyterian-ceo-is-retiring-successor-named
- [NewYork-Presbyterian] DOJ sues NewYork-Presbyterian Hospital over alleged anticompetitive contracts | source=Healthcare Finance News | topics=revenue_cycle | url=https://www.healthcarefinancenews.com/news/doj-sues-newyork-presbyterian-hospital-over-alleged-anticompetitive-contracts

## Next Step
- Feed these candidates into rules-engine and classification in the next milestone.
