# Scripts

Current-snapshot acquisition is implemented for the three v1 official bulk URLs only. Historical acquisition remains intentionally unimplemented until the finite-history gate passes.

- `repo_check.py`: public-repository hygiene checks.
- `acquire_snapshot.py`: bounded acquisition of one current official v1 bulk snapshot into external `KBL_DATA_ROOT`.
- `profile_artifact.py`: offline profiling of an already-downloaded CSV under external `KBL_DATA_ROOT`.
- `compare_profiles.py`: exact column-set comparison; it never infers semantic equivalence from names.

The downloader enforces HTTPS + the official `file.localdata.go.kr` host, bounded retries, free-space checks, atomic finalization, byte-count verification when `Content-Length` is available, SHA-256 provenance, and credential redaction in manifest URLs.
