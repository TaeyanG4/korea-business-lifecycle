# Korea Local Food-Service Permit Data

[한국어](README.md)

A reproducible public-data project built from Korean Ministry of the Interior and Safety local-government permit data. The repository keeps the name `korea-business-lifecycle`, but the **core v1 data product is a nationwide current permit snapshot**. Nationwide history acquisition and `PERMIT_STATUS_EPISODE` reconstruction are retained as an **optional advanced workflow** for analysts who need longitudinal inference.

## v1 status

**LOCAL V1 CORE: COMPLETE**

- Scope: general restaurants, rest cafes, and bakeries
- Canonical `PERMIT`: **3,010,802 rows**, production materialized and independently verified
- WGS84 sidecar: **3,010,802 rows**, 2,811,767 coordinates transformed and independently verified
- Public aggregate: **67,267 cells**, k=10 suppression, independently verified
- Nationwide history/episodes: **not required for v1 completion**; runner, schema, and verifier remain available as optional tooling

All real and derived runtime data stays under Git-ignored `data/local/`.

## Public release scope

The Kaggle/public v1 release contains **only the privacy-minimized aggregate**.

The following remain private:

- row-level `PERMIT`
- business names, exact addresses, management numbers, phone numbers, and other direct/linkable fields
- precise source coordinates and WGS84 coordinates
- partial history snapshots

The aggregate groups by source, authority code, raw status/detail-status code, permit year, and closure year, and suppresses cells below 10. **k=10 is a technical minimization threshold, not a legal privacy guarantee.**

## Sources and permitted-use metadata

As rechecked on 2026-09-08, all three official Public Data Portal API pages display `이용허락범위 제한 없음` (no restriction on the permitted-use scope). v1 uses that official metadata as the release basis and publishes only the attributed privacy-minimized aggregate. Separate written clarification remains optional additional assurance rather than a release prerequisite.

- 15154916 — MOIS food/general restaurants API
- 15154921 — MOIS food/rest cafes API
- 15155252 — MOIS food/bakeries API

The machine-readable final release decision is `provenance/v1_release_scope.json`.

## Lifecycle caveats

The current snapshot is not promoted into invented lifecycle events.

- `MNG_NO` is not declared an official primary key or establishment identity.
- Permit date is not treated as the physical opening date.
- Closure date is not assumed to be a permanent terminal event.
- Two observed `03→01` reversals prove that `03` is not irreversible terminal closure.
- Status code `05` remains unresolved.
- History is an as-of snapshot service, not a lossless event log.
- Optional sparse episodes preserve interval censoring and right censoring.

## Optional history workflow

Analysts who require longitudinal reconstruction can use the prepared monthly reference cadence and acquisition tooling. The reference plan is 10 dates × 3 sources × 244 date-effective authority codes = 7,320 snapshot tasks. This acquisition is **not required for core v1 or the Kaggle aggregate release**.

Key docs:

- [v1 Grain Decision](docs/en/grain-decision.md)
- [History Observation Strategy](docs/en/history-observation-strategy.md)
- [Authority Domain Reference](docs/en/authority-domain-reference.md)
- [Architecture](docs/en/architecture.md)
- [Public Aggregate](docs/en/public-permit-aggregate.md)
- [Redistribution Clarification](docs/en/redistribution-clarification.md)

## Development and verification

```bash
python -m pip install -e ".[test]"
python -m compileall src scripts tests
pytest -v
python scripts/release_readiness.py
```

Tests block network access by default and use synthetic fixtures only. The roughly 4 KB under `tests/fixtures/` is minimal test data required to reproducibly validate transformers and verifiers; it is not source data for publication.

## Repository data policy

- Real source rows, credentials, runtime logs, partial history, canonical Parquet, and Kaggle staging stay under `data/local/`.
- `.env` and Kaggle/API credentials are never tracked.
- Schemas and aggregate-only provenance are tracked.
- Older conservative gates/probes remain for audit history; `v1_release_scope.json` is the current product-scope authority.