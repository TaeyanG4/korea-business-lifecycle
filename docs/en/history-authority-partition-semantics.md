# History Authority Partition Semantics

Checked: **2026-09-07**

Bounded probes and the full 32-code count-only probe were used to test how `OPN_ATMY_GRP_CD` values deleted by the 2026-07-01 administrative reform behave in the history API. Count-level freeze is verified across the full deleted-code domain, while row-content freeze remains limited to the bounded full-row sample.

## Authentication state

The earlier `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` 403 probe remains preserved as historical provenance. A later bounded authenticated probe using the same local credential path succeeded with `resultCode=0`, so **authenticated history execution is currently available**. No service-key value is recorded in provenance or logs.

## Count-only bounded probe

Deleted codes `3490000` (Incheon group), `3590000` (Gwangju group), and `4800000` (Jeonnam group) were queried for all three v1 sources on `20260101`, `20260630`, `20260701`, and `20260906`, using page 1 and `numOfRows=1`.

All nine source/code pairs showed the same pattern:

- `totalCount` increased from 2026-01-01 to 2026-06-30;
- 2026-06-30 = 2026-07-01 = 2026-09-06; and
- deleted codes remained queryable after the reform.

The simple model “a deleted code becomes zero-result on the effective date” is therefore rejected.

## Full-row local audit

Row-level values remain local and Git-ignored; only aggregate diffs are tracked.

- `3490000 / bakeries`: 314 rows on both 2026-06-30 and 2026-09-06, 314 common MNG_NO values, zero added/disappeared, and zero changes in status/detail/closure/permit/name/address/coordinates.
- `4800000 / bakeries`: 332 rows on both dates, 332 common MNG_NO values, zero added/disappeared, and zero changes in every compared field.
- current-code control `3491000 / bakeries`: 217 rows on both dates, but one status/detail/closure change and one coordinate change.

Deleted partitions still contained source status `01` rows on 2026-09-06, so they cannot be assumed to contain only closed legacy records.

## Bounded old/new overlap audit

For bakeries on 2026-09-06, deleted partition `3490000` contained 314 MNG_NO values and the union of current codes `3491000`, `3501000`, `3561000`, and `3565000` contained 932.

- overlap: 0;
- deleted-only: 314;
- current-union-only: 932;
- the current bulk snapshot also contains exactly 932 rows across those four current codes; and
- the current bulk snapshot contains zero rows for deleted `3490000`.

This shows that the bounded old/new partitions are not a simple duplicate projection, but it does not prove that all nationwide old/new partitions are disjoint. MNG_NO is not promoted to a source primary key or establishment identity.

## Current interpretation

History API queryability must not be modeled as a simple **date-effective active-code domain**. Deleted partitions remain queryable as frozen legacy state after the reform, and new/current partitions can answer pre-reform `BASE_DATE` values. The project therefore separates “the API answers this code” from date-effective current-state authority membership.

## Completed full 32-code count-only probe

The exact 32 deleted codes were probed across three sources and four dates, for **384 requests** total.

- requests: 384/384;
- unique tasks: 384;
- complete four-date source/authority pairs: 96/96;
- equal counts on `2026-06-30`, `2026-07-01`, and `2026-09-06`: 96/96 pairs;
- non-empty on 2026-06-30: 90 pairs;
- count growth from 2026-01-01 to 2026-06-30: 81 pairs;
- zero on all four dates: six pairs, authority codes `6290000` and `6460000`;
- no row-level values or service key recorded.

The local result JSON SHA-256 is `3f8326fe2b82835ffda148b2bb1fda0049452e7719c67d58f439c9977e19ad7f`; only aggregate provenance is tracked in Git. Count freeze in 96/96 pairs does **not** prove row-content freeze in all 96 pairs.

Offline verification is reproducible with:

```bash
py -3.12 scripts/verify_deleted_authority_semantics.py \
  data/local/logs/deleted-authority-semantics-20260907.json
```

## Legacy partition inclusion policy

- **On/after 2026-07-01:** enumerate the official current **244 numeric codes only** and exclude the 32 deleted codes from current-state enumeration.
- **Before 2026-07-01:** use the official change reference to take current 244 minus the 32 numeric rows marked `new`, then add the 32 numeric rows marked `deleted`, yielding an exact **244-code** domain.
- The production policy never unions old and new codes on the same date, so same-date old/new deduplication is not required by the enumeration policy.
- A pre-reform response from a new code, or a post-reform response from a deleted code, does not by itself alter date-effective membership.
- MNG_NO remains only a cross-reform observation-linkage candidate, not a source primary key or establishment identity.
- The 276-code current-plus-deleted union is no longer used as the production cost domain.

## Next gate

The date-effective authority policy is approved in `provenance/history_authority_policy.json`. The next gate is the approved **MONTHLY_ANCHOR_PLUS_END** nationwide history acquisition. The completed deleted-code probe command is retained below only for reproducibility; it does not need to be rerun.

```bash
mkdir -p data/local/logs
py -3.12 scripts/probe_deleted_authority_semantics.py --execute --max-requests 384 --request-delay-seconds 0.2 \
  2> data/local/logs/deleted-authority-semantics-20260907.stderr.log \
  | tee data/local/logs/deleted-authority-semantics-20260907.json
```
