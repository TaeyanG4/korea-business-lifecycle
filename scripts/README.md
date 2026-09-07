# Scripts

Current-snapshot acquisition is implemented for the three v1 official bulk URLs. Core v1 is complete around the verified current snapshot. History supports bounded single/sample acquisition plus one explicit **optional** nationwide reference plan: 10 monthly-anchor dates × three sources × 244 date-effective authority codes. The optional nationwide path remains bounded, DRY_RUN by default, resumable, rate-limited, and request-capped.

- `repo_check.py`: public-repository hygiene checks.
- `acquire_snapshot.py`: bounded acquisition of one current official v1 bulk snapshot into external `KBL_DATA_ROOT`.
- `profile_artifact.py`: offline profiling of an already-downloaded CSV under external `KBL_DATA_ROOT`.
- `compare_profiles.py`: exact column-set comparison; it never infers semantic equivalence from names.
- `audit_snapshot.py`: disk-backed current-snapshot identity/duplicate/date/status/privacy/geography audit. It does not create canonical lifecycle labels.
- `audit_cross_category.py`: compares current-snapshot identifier overlap across categories without merging entities or emitting names/addresses.
- `probe_history.py`: one authenticated page-1 history probe using `KBL_DATA_GO_KR_SERVICE_KEY`. It never enumerates pages or writes the key.
- `probe_deleted_authority_semantics.py`: DRY_RUN by default; the exact 384-request count-only probe across all 32 deleted authority codes, three sources and four dates. The completed run emits only authority/date/source `totalCount` values.
- `verify_deleted_authority_semantics.py`: offline verifier for a completed 384-request aggregate-only result; it checks exact task coverage and recomputes the count-freeze assessment without reading source rows.
- `history_authority_policy.py`: network-free builder for the approved pre/post-reform exact 244-code current-state enumeration policy.
- `history_nationwide_plan.py`: network-free builder for the optional 7,320-task monthly nationwide acquisition contract.
- `acquire_nationwide_history.py`: DRY_RUN by default; resumable optional monthly acquisition with date-effective authority codes, global request pacing, and a 400,000-request fail-closed cap per run. Complete existing snapshots are reused.
- `acquire_history_snapshot.py`: one bounded as-of-date history snapshot for one authority code, with an explicit maximum page cap.
- `compare_history_snapshots.py`: aggregate-only comparison of two bounded history snapshots without emitting identifiers, names or addresses.
- `acquire_reverse_transition_probes.py`: dry-run by default; optionally acquires only the six tracked snapshots around the two observed `03->01` cases.
- `audit_reverse_transition_probes.py`: follows the two reverse cases in local memory and emits only aggregate/boolean transition evidence.
- `select_history_sample.py`: deterministic q10/q50/q90/max authority selection from current-snapshot scale, excluding the completed baseline authority.
- `acquire_history_sample.py`: resumable bounded batch for the tracked four-authority expansion sample. It is dry-run by default and requires explicit `--execute`.
- `audit_history_sample.py`: aggregate-only audit across the completed expansion sample.
- `episode_materialization_plan.py`: network-free optional episode materialization contract; if used, it waits for all 7,320 approved history snapshots.
- `materialize_history_episodes.py`: local-only optional bucketed `PERMIT_STATUS_EPISODE` materializer; preflight is available with `--preflight`, raw page hashes are checked, and incomplete/duplicate snapshot tasks fail closed.
- `verify_history_episode_build.py`: independent local verifier for episode Parquet hashes, schemas, compression, and censoring invariants; it returns aggregate verification only.
- `prepare_kaggle_release.py`: verifies the approved aggregate Parquet hash, derives a deterministic UTF-8 CSV of the same 67,267 cells, and prepares the aggregate-only Kaggle package (`CSV + Parquet + source_summary.csv + schema.json + DATA_DICTIONARY.md + README/SOURCES + release-manifest`) under ignored `data/local/kaggle_release/`; `--owner` writes upload-ready `dataset-metadata.json`.
- `prepare_kaggle_row_release.py`: prepares the current 3,010,802-row canonical Kaggle dataset as CSV + Parquet plus provenance documentation. Its metadata contract includes title/subtitle, source provenance, update frequency, file descriptions, and all 26 column descriptions.
- `verify_kaggle_row_release.py`: independently reparses the prepared CSV and Parquet and verifies the exact 3,010,802-row × 26-column shape, order, hashes, and dataset id.
- `build_kaggle_quickstart_notebook.py`: builds the public Kaggle Quickstart/EDA notebook for the current-snapshot dataset. The notebook locates Kaggle inputs recursively, validates the 3M-row Parquet shape, summarizes categories/status/permit years, and demonstrates both Parquet and CSV access.
- `build_kaggle_regional_market_notebook.py`: builds the public regional market-atlas notebook. It derives a bounded first-level region display proxy from address text, compares current permit-record footprint/category mix/recent administrative permit-date composition/coordinate coverage, and keeps the result explicitly supply-side rather than presenting an investment score.
- `maintain_kaggle_dataset_metadata.py`: read-only by default; validates the live 3,010,802-row release and synchronizes the approved 8 file descriptions and all 56 Data Explorer column descriptions only with `--apply`. It preserves Kaggle's current column types and fails closed if the dataset id, file set, table shape, or column order changes.

The current downloader enforces HTTPS + the official `file.localdata.go.kr` host, bounded retries, free-space checks, atomic finalization, byte-count verification when `Content-Length` is available, SHA-256 provenance, and credential redaction in manifest URLs. Optional history has no unbounded mode: nationwide acquisition is an explicit fixed 7,320-task plan, DRY_RUN by default, globally rate-limited and request-capped, and it never writes the service key to manifests.
