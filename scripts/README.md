# Scripts

Current-snapshot acquisition is implemented for the three v1 official bulk URLs. History supports both bounded single/sample acquisition and one explicit approved nationwide plan: 10 monthly-anchor dates × three sources × 244 date-effective authority codes. The nationwide path is still bounded, DRY_RUN by default, resumable, rate-limited, and request-capped.

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
- `history_nationwide_plan.py`: network-free builder for the approved 7,320-task monthly nationwide acquisition contract.
- `acquire_nationwide_history.py`: DRY_RUN by default; resumable monthly production acquisition with date-effective authority codes, global request pacing, and a 400,000-request fail-closed cap per run. Complete existing snapshots are reused.
- `acquire_history_snapshot.py`: one bounded as-of-date history snapshot for one authority code, with an explicit maximum page cap.
- `compare_history_snapshots.py`: aggregate-only comparison of two bounded history snapshots without emitting identifiers, names or addresses.
- `acquire_reverse_transition_probes.py`: dry-run by default; optionally acquires only the six tracked snapshots around the two observed `03->01` cases.
- `audit_reverse_transition_probes.py`: follows the two reverse cases in local memory and emits only aggregate/boolean transition evidence.
- `select_history_sample.py`: deterministic q10/q50/q90/max authority selection from current-snapshot scale, excluding the completed baseline authority.
- `acquire_history_sample.py`: resumable bounded batch for the tracked four-authority expansion sample. It is dry-run by default and requires explicit `--execute`.
- `audit_history_sample.py`: aggregate-only audit across the completed expansion sample.
- `episode_materialization_plan.py`: network-free production episode materialization contract; waits for all 7,320 approved history snapshots.
- `materialize_history_episodes.py`: local-only bucketed `PERMIT_STATUS_EPISODE` materializer; preflight is available with `--preflight`, raw page hashes are checked, and incomplete/duplicate snapshot tasks fail closed.
- `verify_history_episode_build.py`: independent local verifier for episode Parquet hashes, schemas, compression, and censoring invariants; it returns aggregate verification only.

The current downloader enforces HTTPS + the official `file.localdata.go.kr` host, bounded retries, free-space checks, atomic finalization, byte-count verification when `Content-Length` is available, SHA-256 provenance, and credential redaction in manifest URLs. History has no unbounded mode: nationwide acquisition is an explicit fixed 7,320-task plan, DRY_RUN by default, globally rate-limited and request-capped, and it never writes the service key to manifests.
