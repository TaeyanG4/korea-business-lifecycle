# Scripts

Current-snapshot acquisition is implemented for the three v1 official bulk URLs. Bounded history acquisition is now implemented only for explicitly selected source/date/authority combinations after the authentication and finite-query gates were verified.

- `repo_check.py`: public-repository hygiene checks.
- `acquire_snapshot.py`: bounded acquisition of one current official v1 bulk snapshot into external `KBL_DATA_ROOT`.
- `profile_artifact.py`: offline profiling of an already-downloaded CSV under external `KBL_DATA_ROOT`.
- `compare_profiles.py`: exact column-set comparison; it never infers semantic equivalence from names.
- `audit_snapshot.py`: disk-backed current-snapshot identity/duplicate/date/status/privacy/geography audit. It does not create canonical lifecycle labels.
- `audit_cross_category.py`: compares current-snapshot identifier overlap across categories without merging entities or emitting names/addresses.
- `probe_history.py`: one authenticated page-1 history probe using `KBL_DATA_GO_KR_SERVICE_KEY`. It never enumerates pages or writes the key.
- `acquire_history_snapshot.py`: one bounded as-of-date history snapshot for one authority code, with an explicit maximum page cap.
- `compare_history_snapshots.py`: aggregate-only comparison of two bounded history snapshots without emitting identifiers, names or addresses.
- `acquire_reverse_transition_probes.py`: dry-run by default; optionally acquires only the six tracked snapshots around the two observed `03->01` cases.
- `audit_reverse_transition_probes.py`: follows the two reverse cases in local memory and emits only aggregate/boolean transition evidence.
- `select_history_sample.py`: deterministic q10/q50/q90/max authority selection from current-snapshot scale, excluding the completed baseline authority.
- `acquire_history_sample.py`: resumable bounded batch for the tracked four-authority expansion sample. It is dry-run by default and requires explicit `--execute`.
- `audit_history_sample.py`: aggregate-only audit across the completed expansion sample.

The current downloader enforces HTTPS + the official `file.localdata.go.kr` host, bounded retries, free-space checks, atomic finalization, byte-count verification when `Content-Length` is available, SHA-256 provenance, and credential redaction in manifest URLs. History acquisition has no nationwide/unbounded mode and never writes the service key to manifests.
