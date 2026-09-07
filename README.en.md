# Korea Business Lifecycle

[한국어](README.md)

An open project for reproducible research on the lifecycle of Korean businesses or permit units using local-government licensing data.

## Current execution scope

The first execution milestone is intentionally bounded to:

1. bootstrap a public GitHub repository and Python 3.11/3.12 project;
2. archive reproducible provenance for the current licensing-data sources; and
3. assess technical, legal, privacy, and history feasibility for **general restaurants, rest cafes, and bakeries** only.

No nationwide raw data, full-history harvesting, lifecycle reconstruction, or Kaggle publication is performed in this milestone.

## Important constraints

- The current official candidate inventory is recorded as **195 permit datasets**, not 196.
- No source primary key is assumed.
- Permit date is not automatically treated as physical opening date.
- Closure dates and status values are not converted into closure labels before semantic verification.
- EPSG:5174 is documented for the three v1 sources, and full current-v1 QA supports `좌표정보(X)=easting` and `좌표정보(Y)=northing`. This interpretation is scoped to the currently approved artifacts and future snapshots require revalidation.
- Public accessibility and permission to redistribute on Kaggle are separate gates.
- Real source data lives in the repository-local but Git-ignored `data/local/` runtime directory. Raw/history/staging/processed/log artifacts under it are never tracked.

## Development

```bash
python -m pip install -e ".[test]"
python -m compileall src scripts tests
pytest -v
```

Tests are offline and use synthetic fixtures only.

## Current history status

Current-snapshot acquisition/profiling and the five-authority bounded history audit are complete. `MNG_NO` continuity remains strong across all 15 source×authority pairs, and two `03→01` source-state reversals are confirmed, so code `03` is not treated as irreversible terminal closure. The v1 `PERMIT` and `PERMIT_STATUS_EPISODE` schemas remain frozen. The current-snapshot → `PERMIT` transformer passed the complete **3,010,802-row full dry run** with zero duplicate linkage candidates. Local production build `permit-v1-9908225df465e2ff` was then materialized as Parquet/ZSTD for all 3,010,802 rows, and an independent verifier rechecked hashes, schemas, ZSTD compression, and quality aggregates. Full geospatial QA inspected all 2,811,767 coordinate pairs; among 2,631,605 pairs eligible for coarse address-region comparison, `X=easting/Y=northing` matched 99.958% and there were zero candidate-B-only matches. Local WGS84 derivation is therefore approved for exactly these current-v1 artifacts, but it will be implemented as a separate enrichment rather than changing the frozen 26-column parent. Public row-level release and episode reconstruction remain blocked.

## Documentation

- [Architecture](docs/en/architecture.md)
- [v1 data sources](docs/en/data-sources.md)
- [Data/privacy policy](docs/en/data-policy.md)
- [Reproducibility](docs/en/reproducibility.md)
- [Bounded source profiling](docs/en/profiling.md)
- [Bounded history audit findings](docs/en/bounded-history-findings.md)
- [03→01 reverse-transition follow-up probe](docs/en/reverse-transition-probe.md)
- [v1 grain decision](docs/en/grain-decision.md)
- [Canonical PERMIT parent schema](docs/en/canonical-permit-schema.md)
- [Canonical PERMIT_STATUS_EPISODE schema](docs/en/canonical-episode-schema.md)
- [Canonical PERMIT transformer](docs/en/canonical-permit-transformer.md)
- [Canonical PERMIT bounded real-data compatibility](docs/en/canonical-permit-compatibility.md)
- [Canonical PERMIT full-snapshot dry run](docs/en/canonical-permit-full-dry-run.md)
- [Canonical PERMIT production materialization](docs/en/canonical-permit-materialization.md)
- [Geospatial source X/Y axis QA](docs/en/geospatial-axis-qa.md)
- [History sample expansion plan](docs/en/history-sample-expansion.md)
- [Five-authority history sample findings](docs/en/expanded-history-findings.md)
- [First-milestone feasibility](docs/en/first-milestone.md)

Current product-track gates are available as aggregate-only JSON:

```bash
python scripts/release_readiness.py
```

## License

The project code license and any dataset redistribution license are not yet finalized. The upstream `no restriction on permitted use` label is evidence to review, not an automatic grant to mirror source records on Kaggle.
