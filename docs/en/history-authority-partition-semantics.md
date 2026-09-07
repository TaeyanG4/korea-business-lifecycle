# History Authority Partition Semantics

Checked: **2026-09-07**

A bounded probe was used to test how `OPN_ATMY_GRP_CD` values deleted by the 2026-07-01 administrative reform behave in the history API. The findings are direct execution evidence, not a nationwide generalization across all 32 deleted codes.

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

The history authority filter must not be modeled as a simple **date-effective active-code domain**. In the bounded evidence, deleted partitions evolve until the reform boundary and then remain queryable as frozen legacy state, while current partitions can continue evolving. The 244-current + 32-deleted = 276-code candidate union is useful for cost planning, but it is not represented as semantically equivalent to a current-state snapshot for a given date.

## Next gate

The complete count-only probe covers all 32 deleted codes × 3 sources × 4 dates: **384 requests**. It is DRY_RUN by default.

```bash
py -3.12 scripts/probe_deleted_authority_semantics.py
```

Network execution requires an explicit `--execute`; this long-running action is not started automatically.

In Git Bash, preserve the aggregate result and progress streams separately under the Git-ignored local log tree:

```bash
mkdir -p data/local/logs
py -3.12 scripts/probe_deleted_authority_semantics.py --execute --max-requests 384 --request-delay-seconds 0.2 \
  2> data/local/logs/deleted-authority-semantics-20260907.stderr.log \
  | tee data/local/logs/deleted-authority-semantics-20260907.json
```
