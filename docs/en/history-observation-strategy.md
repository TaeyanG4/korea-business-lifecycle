# Nationwide History Observation Strategy Cost Gate

Checked: **2026-09-07**

Before production `PERMIT_STATUS_EPISODE` reconstruction can expand nationwide, both authority-enumeration semantics and an observation cadence must be settled. This document **does not approve a cadence**; it only quantifies planning cost and completeness limits.

## Cost basis

- v1 sources: general restaurants, rest cafes, bakeries;
- current rows: 3,010,802;
- numeric authorities observed non-empty identically across all three current snapshots: 230;
- current numeric authorities in the latest 2026-07-02 official attachment: 244;
- current `_ALL` aggregate tokens: 16, excluded from row enumeration;
- exact numeric authorities marked deleted by the 2026-07-01 reform: 32;
- current-plus-deleted candidate union: 276;
- candidate-union codes not observed in the current snapshot: 46 per source;
- maximum history API page size: 100;
- exact current 244 and deleted 32 lists: ingested, hashed, and validated;
- pre-reform `BASE_DATE` query semantics for deleted codes: unverified; and
- network access: none.

For cost planning, the current mathematical paging range over the 230 non-empty partitions is augmented with one probe for each of the remaining 46 candidate-union codes per source.

| Source | Current rows | 230 non-empty paging | Candidate probes | Planning range/date |
|---|---:|---:|---:|---:|
| General restaurants | 2,295,369 | 22,954–23,183 | 46 | 23,000–23,229 |
| Rest cafes | 645,952 | 6,460–6,689 | 46 | 6,506–6,735 |
| Bakeries | 69,481 | 695–924 | 46 | 741–970 |
| **Total** | **3,010,802** | **30,109–30,796** | **138** | **30,247–30,934** |

This is not an upper/lower bound on historical row volume. Deleted codes can be non-empty on earlier dates.

## 2026-01-01 through 2026-09-06 planning scenarios

The 249-calendar-day window is compared using the same current-scale planning range.

| Scenario | Observation dates | Maximum observation gap | Request lower | Request upper | Approved |
|---|---:|---:|---:|---:|---|
| endpoints only | 2 | 248 days | 60,494 | 61,868 | no |
| monthly anchor + end | 10 | 31 days | 302,470 | 309,340 | no |
| weekly 7-day + end | 37 | 7 days | 1,119,139 | 1,144,558 | no |
| daily | 249 | 1 day | 7,531,503 | 7,702,566 | no |

## Why daily still is not a lossless event log

The history endpoint is an as-of snapshot service. Even daily observations do not prove:

- absence of multiple intraday state changes;
- an exact transition timestamp between snapshots;
- preservation of every intermediate change as an event log;
- whether a `03→01` reversal is real reopening or administrative correction; or
- canonical semantics for status `05`.

Daily cadence narrows interval-censoring width; it does not create event-log semantics.

## Current decision

`NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_DATE_EFFECTIVE_AUTHORITY_FILTER_SEMANTICS_AND_COST_REVIEW_REQUIRED`

Before production reconstruction, at least these decisions remain:

1. verify pre/post-reform `BASE_DATE` filter semantics for the exact 32 deleted authority codes;
2. choose an acceptable request budget;
3. choose the maximum censoring gap required by the analytical goal;
4. accept or reject snapshot-retention/intermediate-change loss; and
5. preserve unresolved status `05` and reopening-vs-correction semantics.

The cost model is reproducible without network access:

```bash
python scripts/history_observation_strategy.py
```
