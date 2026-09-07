# Privacy-Minimized Public Permit Aggregate Candidate

Checked: **2026-09-07**

The project does not publish row-level `PERMIT` or WGS84 artifacts. This contract defines a separate local **privacy-minimized aggregate candidate**. It is a technical minimization step only and does not grant permission for Kaggle/public redistribution.

## Input

- verified parent build: `permit-v1-9908225df465e2ff`
- parent rows: 3,010,802
- parent independent verifier: PASS
- network access: none
- row-level public projection: not approved

## Seven-column aggregate schema

`schemas/public_permit_aggregate.v1.json` allows only:

- `source_key`
- `authority_code`
- `source_status_code`
- `source_detail_status_code`
- `permit_year`
- `closure_year`
- `cell_count`

Exact `permit_date` and `closure_date` values are not emitted; only years are derived. `permit_year` is not represented as a physical opening year, `closure_year` is not an irreversible terminal event, and no canonical meaning is added to source status codes `03` or `05`.

## Explicit exclusions

The aggregate output excludes row-level fields including:

- `management_number`, `source_row_number`, and artifact/retrieval lineage;
- business name;
- lot/road addresses and postal codes;
- source X/Y and WGS84 longitude/latitude;
- raw update timestamps; and
- telephone/homepage.

## Cell suppression

The grouping key is `source + authority + source status codes + permit year + closure year`. A cell with **fewer than 10 rows is suppressed entirely** from the candidate output.

`k=10` is only a technical suppression threshold for this project. It is **not claimed as a legal or statistical guarantee of privacy**. Redistribution/license review and final release policy remain separate required gates.

## Local build

The deterministic build ID is `permit-public-agg-v1-bedd874de6619bee`.

Default mode is plan-only:

```bash
python scripts/materialize_public_permit_aggregate.py
```

Long local execution:

```bash
python scripts/materialize_public_permit_aggregate.py --execute
```

The materializer scans all 3,010,802 verified parent rows but reads only the six input fields required for aggregation. The candidate remains under `data/local/public_candidate/permit_aggregate/v1/...`.

## Independent verification

```bash
python scripts/verify_public_permit_aggregate.py
```

The verifier re-verifies the parent build and checks the aggregate manifest/hash/schema/ZSTD, `cell_count >= 10`, and released/suppressed row accounting.

## Current gate

- implementation + synthetic suppression/tamper tests: PASS
- real parent plan-only validation: PASS
- production aggregate scan: **PASS (3,010,802 rows)**
- cells before suppression: 297,195
- released candidate cells (`cell_count >= 10`): 67,267
- suppressed cells: 229,928
- source rows represented by released cells: 2,383,689
- source rows represented by suppressed cells: 627,113
- output: 108,019 bytes, independent verifier PASS
- technical minimization: VERIFIED
- row-level public release: BLOCKED
- aggregate publication: BLOCKED
- Kaggle redistribution: UNRESOLVED

`Released candidate` does not mean approved for publication. It only means an aggregate cell passed the local suppression rule and is present in the local candidate artifact.
