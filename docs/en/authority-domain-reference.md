# Official Authority-Domain Reference Gate

Checked: **2026-09-07**

Nationwide history queries are partitioned by `OPN_ATMY_GRP_CD` (open authority code). This gate separates the **currently active domain**, **codes deleted by the 2026-07-01 administrative reform**, and the still-unverified **date-effective query domain for the Jan–Sep history window**.

## Official evidence in time order

The January 2026 LOCALDATA `Public Data Portal User Manual` says the `개방자치단체코드.xlsx` reference contains **245 provincial/city/county/district local-government codes**. The project preserves that documented count but does not promote it to the latest exact query domain.

A Ministry of the Interior and Safety notice published on 2026-07-03 documents authority-code deletion/new assignment for the `전남광주통합특별시` and Incheon administrative reform effective 2026-07-01 and provides `개방자치단체코드_영업상태코드_행정체제개편반영_20260702.xlsx`.

The exact official attachment is stored only under Git-ignored local runtime storage. Its SHA-256 is:

`d032ff4bd63148238a8066afb7b62f96770d8a063bd6c632d4f7617e9cc407f8`

## Latest official attachment parse

Strict parsing of `1. 개방자치단체코드` yields:

- **260** active rows;
- **244** active seven-digit numeric codes;
- **16** active `_ALL` aggregate tokens;
- **34** deleted rows = 32 numeric codes + 2 `_ALL` tokens;
- **33** new rows = 32 numeric codes + 1 `_ALL` token; and
- SHA-256 of the exact current 244 code/name list: `a666c5cb432c439f687064e3046ec2e9a84d2de708dfbe80817330e60b76ddad`.

The January manual's `245` therefore is not substituted for the latest exact list. The latest attachment's **current numeric domain is 244**, and `_ALL` aggregate tokens are excluded from row-level authority enumeration.

## Comparison with the current snapshots

All three v1 current snapshots contain the same **230** authority codes, and all 230 are a subset of the latest 244-code numeric domain.

- current official numeric: **244**;
- current observed non-empty: **230**;
- current official but unobserved: **14**; and
- deleted codes still present in the current snapshots: **0**.

The exact current 244 code/name list is now ingested, hashed, and validated in tracked provenance for the current reference date.

## Additional Jan–Sep history-window gate

The exact **32 deleted numeric codes** from the 2026-07-01 change are also ingested. They are disjoint from the current 244 codes, giving a conservative **276-code current-plus-deleted candidate union** for cost planning.

That 276-code union is not represented as a proven date-effective history query domain. Official documentation reviewed so far does not establish:

- whether deleted codes remain queryable for pre-reform `BASE_DATE` values;
- whether historical snapshots retain old codes or are remapped to new codes; or
- how the manual's 245 count reconciles to the exact date-effective domain.

Current gate state:

- exact current 244 numeric list: **complete**;
- exact deleted 32 numeric list: **complete**;
- current-reference numeric enumeration: **ready**;
- Jan–Sep date-effective history enumeration: **not ready**; and
- future source snapshots require a reference refresh.

## Relationship to the cost model

For planning, the project conservatively probes the full **276-code current-plus-deleted candidate union**. At current row scale, 230 partitions are currently non-empty and 46 additional candidates require one probe per source, producing **30,247–30,934 requests per as-of date**.

Those values are not historical row-count bounds. Deleted codes can be non-empty for earlier dates, so actual historical paging can differ.

## Next gate

Before production nationwide acquisition, verify date-effective history-filter semantics for the exact 32 deleted codes through official documentation or a bounded authenticated probe, then explicitly approve a cadence/request budget.
