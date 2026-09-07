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
- authenticated bounded history execution: available;
- bounded semantics: sampled deleted partitions evolve before the reform and remain frozen afterward;
- a sampled current partition continues evolving after the reform; and
- the full 32-deleted-code count probe is **384/384 complete**, with post-reform count freeze in all 96 source/authority pairs;
- post-reform current-state enumeration uses current 244 only and excludes deleted 32; and
- the pre-reform old/new partition domain remains unresolved, so current and deleted partitions are not auto-unioned.

Cost planning is split at 2026-07-01. Before the reform, the conservative 276-code candidate union adds 46 one-request probes per source. After the reform, current-state enumeration uses only current 244, so only the 14 current official codes not observed in the current snapshots are probed per source.

| Source | 230 non-empty paging | Pre-reform probes/range | Post-reform probes/range |
|---|---:|---:|---:|
| General restaurants | 22,954–23,183 | 46 / 23,000–23,229 | 14 / 22,968–23,197 |
| Rest cafes | 6,460–6,689 | 46 / 6,506–6,735 | 14 / 6,474–6,703 |
| Bakeries | 695–924 | 46 / 741–970 | 14 / 709–938 |
| **Total** | **30,109–30,796** | **138 / 30,247–30,934** | **42 / 30,151–30,838** |

This is not an upper/lower bound on historical row volume. Bounded execution shows that deleted codes can remain non-empty after the reform as frozen legacy partitions, so the candidate union is not treated as semantically equivalent to a date-specific current-state snapshot.

## 2026-01-01 through 2026-09-06 planning scenarios

The 249-calendar-day window is compared using the reform-aware mixed planning range.

| Scenario | Dates (pre/post) | Maximum gap | Request lower | Request upper | Approved |
|---|---:|---:|---:|---:|---|
| endpoints only | 2 (1/1) | 248 days | 60,398 | 61,772 | no |
| monthly anchor + end | 10 (6/4) | 31 days | 302,086 | 308,956 | no |
| weekly 7-day + end | 37 (26/11) | 7 days | 1,118,083 | 1,143,502 | no |
| daily | 249 (181/68) | 1 day | 7,524,975 | 7,696,038 | no |

## Why daily still is not a lossless event log

The history endpoint is an as-of snapshot service. Even daily observations do not prove:

- absence of multiple intraday state changes;
- an exact transition timestamp between snapshots;
- preservation of every intermediate change as an event log;
- whether a `03→01` reversal is real reopening or administrative correction; or
- canonical semantics for status `05`.

Daily cadence narrows interval-censoring width; it does not create event-log semantics.

## Current decision

`NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_PRE_REFORM_AUTHORITY_DOMAIN_AND_COST_REVIEW_REQUIRED`

Before production reconstruction, at least these decisions remain:

1. resolve pre-reform old/new authority-partition completeness and overlap semantics;
2. choose an acceptable request budget;
3. choose the maximum censoring gap required by the analytical goal;
4. accept or reject snapshot-retention/intermediate-change loss; and
5. preserve unresolved status `05` and reopening-vs-correction semantics.

The bounded execution findings are documented in [History Authority Partition Semantics](history-authority-partition-semantics.md).

The cost model is reproducible without network access:

```bash
python scripts/history_observation_strategy.py
```
