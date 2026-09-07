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
- EPSG:5174 is documented for the three v1 sources, but source X/Y meanings and axis order remain to be verified.
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

Current-snapshot acquisition/profiling and the five-authority bounded history audit are complete. `MNG_NO` continuity remains strong across all 15 source×authority pairs, and a three-date follow-up confirmed both `03→01` cases as source-level `closed→operating/normal` reversals. The project therefore rejects code `03` as an assumed irreversible terminal closure. The v1 grain is frozen as a canonical `PERMIT` parent plus derived `PERMIT_STATUS_EPISODE`; both the 26-column `PERMIT` parent schema and the 23-column `PERMIT_STATUS_EPISODE` schema are frozen. The current-snapshot → `PERMIT` deterministic transformer has passed synthetic fixtures, bounded compatibility on 256 real rows per source, and the **complete 3,010,802-row full-snapshot dry run**. The full scan found zero duplicate linkage candidates; the four `INVALID` permit dates match the prior profiling anomaly and remain null plus quality flags. A local-only Parquet/ZSTD production materializer is now implemented and tested, pinned to the exact approved input hashes; only the long production build awaits user execution. Episode boundaries preserve left/interval/right censoring without inferring exact transition times, canonical active/closed states, or terminal events. Public row-level release, WGS84 generation, and episode reconstruction remain disabled. The real service key remains local-only via `.env` or `KBL_DATA_GO_KR_SERVICE_KEY` and is never committed.

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
- [History sample expansion plan](docs/en/history-sample-expansion.md)
- [Five-authority history sample findings](docs/en/expanded-history-findings.md)
- [First-milestone feasibility](docs/en/first-milestone.md)

## License

The project code license and any dataset redistribution license are not yet finalized. The upstream `no restriction on permitted use` label is evidence to review, not an automatic grant to mirror source records on Kaggle.
