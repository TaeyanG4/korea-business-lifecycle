# Nationwide History Observation Strategy Cost Gate

Checked: **2026-09-07**

The authority-enumeration semantics and observation cadence are settled for analysts who choose nationwide `PERMIT_STATUS_EPISODE` reconstruction. This document records the reference **MONTHLY_ANCHOR_PLUS_END** cadence and its cost/completeness limits. **As of 2026-09-08 this workflow is not a prerequisite for core v1 completion or the Kaggle aggregate release.**

## Cost basis

- v1 sources: general restaurants, rest cafes, bakeries;
- current rows: 3,010,802;
- numeric authorities observed non-empty identically across all three current snapshots: 230;
- current numeric authorities in the latest 2026-07-02 official attachment: 244;
- current `_ALL` aggregate tokens: 16, excluded from row enumeration;
- exact numeric authorities marked deleted by the 2026-07-01 reform: 32;
- exact numeric authorities marked new by the 2026-07-01 reform: 32;
- current-plus-deleted candidate union: 276;
- candidate-union codes not observed in the current snapshot: 46 per source;
- maximum history API page size: 100;
- exact current 244 and deleted 32 lists: ingested, hashed, and validated;
- authenticated bounded history execution: available;
- bounded semantics: sampled deleted partitions evolve before the reform and remain frozen afterward;
- a sampled current partition continues evolving after the reform; and
- the full 32-deleted-code count probe is **384/384 complete**, with post-reform count freeze in all 96 source/authority pairs;
- post-reform current-state enumeration uses current 244 only and excludes deleted 32; and
- pre-reform current-state enumeration uses current 244 minus new 32 plus deleted 32, yielding exact 244; and
- old and new codes are never unioned on the same date.

Cost planning is split at 2026-07-01 using date-effective 244-code domains. Before the reform, the current-row-scale paging bound is computed across exact `current-new+deleted` 244. After the reform, current 244 is used and the 14 current official codes not observed in current snapshots are included as one-request probes per source.

| Source | 230 current non-empty paging | Pre-reform exact-244 range | Post-reform probes/range |
|---|---:|---:|---:|
| General restaurants | 22,954–23,183 | 22,954–23,197 | 14 / 22,968–23,197 |
| Rest cafes | 6,460–6,689 | 6,460–6,703 | 14 / 6,474–6,703 |
| Bakeries | 695–924 | 695–938 | 14 / 709–938 |
| **Total** | **30,109–30,796** | **30,109–30,838** | **42 / 30,151–30,838** |

This is not an upper/lower bound on historical row volume. Bounded execution shows that deleted codes can remain non-empty after the reform as frozen legacy partitions, so the candidate union is not treated as semantically equivalent to a date-specific current-state snapshot.

## 2026-01-01 through 2026-09-06 planning scenarios

The 249-calendar-day window is compared using the reform-aware mixed planning range.

| Scenario | Dates (pre/post) | Maximum gap | Request lower | Request upper | Approved |
|---|---:|---:|---:|---:|---|
| endpoints only | 2 (1/1) | 248 days | 60,260 | 61,676 | no |
| **monthly anchor + end** | **10 (6/4)** | **31 days** | **301,258** | **308,380** | **yes** |
| weekly 7-day + end | 37 (26/11) | 7 days | 1,114,495 | 1,141,006 | no |
| daily | 249 (181/68) | 1 day | 7,499,997 | 7,678,662 | no |

## Why daily still is not a lossless event log

The history endpoint is an as-of snapshot service. Even daily observations do not prove:

- absence of multiple intraday state changes;
- an exact transition timestamp between snapshots;
- preservation of every intermediate change as an event log;
- whether a `03→01` reversal is real reopening or administrative correction; or
- canonical semantics for status `05`.

Daily cadence narrows interval-censoring width; it does not create event-log semantics.

## Current decision

`OPTIONAL_MONTHLY_REFERENCE_CADENCE_AVAILABLE`

Only if an analyst elects optional production reconstruction do these execution gates apply:

1. execute the resumable **7,320 snapshot tasks** covering 10 dates × three sources × 244 authorities;
2. retain the **400,000 actual network-attempt hard cap** per run and minimum 0.2-second request delay;
3. require all 7,320 tasks complete with exactly one snapshot per task;
4. materialize production episodes while verifying raw-history page SHA-256 values;
5. pass the independent episode-build verifier; and
6. preserve unresolved status `05`, reopening-vs-correction, and event-log limitations.

The bounded execution findings are documented in [History Authority Partition Semantics](history-authority-partition-semantics.md).

The cost model is reproducible without network access:

```bash
python scripts/history_observation_strategy.py
```

The nationwide acquisition is optional and intentionally not auto-started; `scripts/acquire_nationwide_history.py` remains DRY_RUN by default.

```bash
# network-free plan/current local completion state
py -3.12 scripts/acquire_nationwide_history.py

# long-running production acquisition; completed snapshots are skipped on rerun
py -3.12 scripts/acquire_nationwide_history.py --execute \
  --max-network-requests 400000 \
  --request-delay-seconds 0.2

# must report 7320 complete, 0 missing, 0 multiple before materialization
py -3.12 scripts/materialize_history_episodes.py --preflight

# local-only production episode build
py -3.12 scripts/materialize_history_episodes.py

# independent verifier; --build-id is optional when exactly one episode build exists
py -3.12 scripts/verify_history_episode_build.py
```
