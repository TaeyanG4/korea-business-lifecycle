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

Current-snapshot acquisition/profiling and bounded history audits are complete. Production `PERMIT` build `permit-v1-9908225df465e2ff` and separate WGS84 sidecar `permit-geo-v1-c4af8799de0283bb` are both materialized and independently verified across all **3,010,802 rows**. Lifecycle semantic hard rules remain unchanged: `03` is not irreversible terminal closure and `05` remains unmapped. The full **384-request** count-only probe across 32 deleted codes, three sources, and four dates is complete. Using the official 2026-07-01 change reference, the date-effective current-state authority domain is now fixed to **pre-reform 244 = current 244 - new 32 + deleted 32**, and **post-reform current 244 only**. API queryability itself does not define that membership. The production history cadence is approved as **MONTHLY_ANCHOR_PLUS_END** over 10 dates, maximum gap 31 days, current-scale planning **301,258–308,380 requests**, with a 400,000-request hard cap per run. Nationwide acquisition has not yet been executed; a resumable runner, complete-7,320-snapshot gate, bucketed episode materializer, and independent verifier are prepared. Written redistribution questions/contact routes are also prepared, but external publication remains unapproved.

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
- [Bounded PERMIT_STATUS_EPISODE reconstruction](docs/en/bounded-episode-reconstruction.md)
- [Nationwide history observation strategy cost gate](docs/en/history-observation-strategy.md)
- [History authority partition semantics](docs/en/history-authority-partition-semantics.md)
- [Official authority-domain reference gate](docs/en/authority-domain-reference.md)
- [Redistribution written-clarification gate](docs/en/redistribution-clarification.md)
- [Canonical PERMIT transformer](docs/en/canonical-permit-transformer.md)
- [Canonical PERMIT bounded real-data compatibility](docs/en/canonical-permit-compatibility.md)
- [Canonical PERMIT full-snapshot dry run](docs/en/canonical-permit-full-dry-run.md)
- [Canonical PERMIT production materialization](docs/en/canonical-permit-materialization.md)
- [Geospatial source X/Y axis QA](docs/en/geospatial-axis-qa.md)
- [Canonical PERMIT WGS84 enrichment](docs/en/canonical-permit-geospatial.md)
- [Privacy-minimized public aggregate candidate](docs/en/public-permit-aggregate.md)
- [History sample expansion plan](docs/en/history-sample-expansion.md)
- [Five-authority history sample findings](docs/en/expanded-history-findings.md)
- [First-milestone feasibility](docs/en/first-milestone.md)

Current product-track gates are available as aggregate-only JSON:

```bash
python scripts/release_readiness.py
```

## License

The project code license and dataset redistribution policy are not yet finalized. The 2026-09-07 refresh reconfirmed `no restriction on the permitted-use scope` on all three official MOIS v1 APIs, so the source-use metadata gate is recorded as PASS. Source-specific third-party-rights clarification is still outstanding under the portal policy, so raw mirroring and external/Kaggle redistribution of the privacy-minimized aggregate remain `UNRESOLVED`.
