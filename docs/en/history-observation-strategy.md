# Nationwide History Observation Strategy Cost Gate

Checked: **2026-09-07**

Before production `PERMIT_STATUS_EPISODE` reconstruction can be expanded nationwide, an as-of history observation cadence must be chosen. This document **does not approve a cadence**; it only quantifies cost and completeness limits.

## Cost basis

- v1 sources: general restaurants, rest cafes, bakeries;
- current rows: 3,010,802;
- authority codes observed identically across all three current snapshots: 230;
- maximum history API page size: 100;
- authoritative completeness of the observed authority domain: unverified;
- cost basis: mathematical paging bounds at current row scale;
- not a forecast of historical row counts; and
- no network access.

Because requests are partitioned by authority, one nationwide as-of date at current scale has these bounds:

| Source | Current rows | Lower bound/date | Upper bound/date |
|---|---:|---:|---:|
| General restaurants | 2,295,369 | 22,954 | 23,183 |
| Rest cafes | 645,952 | 6,460 | 6,689 |
| Bakeries | 69,481 | 695 | 924 |
| **Total** | **3,010,802** | **30,109** | **30,796** |

## 2026-01-01 through 2026-09-06 scenarios

The 249-calendar-day window is compared only for cost.

| Scenario | Observation dates | Maximum observation gap | Request lower | Request upper | Approved |
|---|---:|---:|---:|---:|---|
| endpoints only | 2 | 248 days | 60,218 | 61,592 | no |
| monthly anchor + end | 10 | 31 days | 301,090 | 307,960 | no |
| weekly 7-day + end | 37 | 7 days | 1,114,033 | 1,139,452 | no |
| daily | 249 | 1 day | 7,497,141 | 7,668,204 | no |

These values are **current-scale paging cost bounds**, not guarantees of historical row volume.

## Why daily still is not a lossless event log

The history endpoint is an as-of snapshot service. Even daily observations do not prove:

- that multiple state changes did not occur within one day;
- an exact transition timestamp between snapshots;
- that the source retains every intermediate change as an event log;
- whether a `03→01` reversal is real reopening or administrative correction; or
- canonical semantics for status `05`.

Daily cadence narrows interval-censoring width; it does not create event-log semantics.

## Current decision

`NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_COST_AND_COMPLETENESS_REVIEW_REQUIRED`

Before production reconstruction, at least these decisions remain:

1. verify an authoritative nationwide `OPN_ATMY_GRP_CD` domain;
2. choose an acceptable request budget;
3. choose the maximum censoring gap required by the analytical goal;
4. decide whether snapshot retention/intermediate-change loss is acceptable; and
5. preserve unresolved status `05` and reopening-vs-correction semantics.

The cost model is reproducible without network access:

```bash
python scripts/history_observation_strategy.py
```
