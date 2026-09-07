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

## Jan–Sep date-effective history domain

The official 2026-07-01 change reference marks **32 new numeric codes** and **32 deleted numeric codes** at the same effective date. The deleted set is disjoint from current 244, and the new set is a subset of current 244.

History API queryability itself is not date-effective membership: deleted codes remain answerable after the reform, and new/current codes can answer pre-reform dates. Current-state enumeration therefore follows the official change effective date instead of API queryability.

Current gate state:

- exact current 244 numeric list: **complete**;
- exact new 32 numeric list: **complete**;
- exact deleted 32 numeric list: **complete**;
- current-reference numeric enumeration: **ready**;
- pre-reform numeric enumeration: **244 = current - new + deleted, ready**;
- post-reform numeric enumeration: **current 244, ready**; and
- future source snapshots require a reference refresh.

## Relationship to the cost model

Production planning now uses the date-effective **244-code domain**, not the 276 union. At current row scale the pre-reform range is **30,109–30,838 requests per as-of date**, and post-reform is **30,151–30,838**.

Those values are not historical row-count bounds. Deleted codes can be non-empty for earlier dates, so actual historical paging can differ.

## Next gate

The authority code-set gate is passed. The next action is the approved resumable nationwide acquisition under the monthly cadence and 400,000-request hard cap.
