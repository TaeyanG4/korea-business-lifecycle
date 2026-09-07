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

The current downloader enforces HTTPS + the official `file.localdata.go.kr` host, bounded retries, free-space checks, atomic finalization, byte-count verification when `Content-Length` is available, SHA-256 provenance, and credential redaction in manifest URLs. History acquisition has no nationwide/unbounded mode and never writes the service key to manifests.
