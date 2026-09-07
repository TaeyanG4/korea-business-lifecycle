# Bounded Source Profiling

Phase 2 separates current-snapshot acquisition from profiling. `acquire_snapshot.py` fetches only the three v1 official `file.localdata.go.kr` bulk URLs with finite retries/timeouts and never calls a history endpoint. The profiler reproducibly inspects an **already external CSV artifact stored outside Git**.

## Safety rules

- The default real-data location is the project-scoped sibling directory `../korea-business-lifecycle-data`.
- `KBL_DATA_ROOT` may explicitly override that default.
- The resolved real-data root must always remain outside the Git repository.
- The input artifact must live under `KBL_DATA_ROOT`.
- Raw bytes are never modified.
- SHA-256 is recorded.
- UTF-8 / CP949 / EUC-KR candidates are tested with strict decoding; replacement decoding is prohibited.
- CSV rows with a field count different from the header fail profiling.
- Cardinality memory is capped per column. Once capped, the profiler reports a lower bound rather than pretending the count is exact.
- Raw `top_values` are emitted only for status-like columns, not for address, business-name, or identifier-like fields.
- Date-like and coordinate-like columns receive full date/numeric parseability checks. Other columns use a bounded default probe of 10,000 non-null values and explicitly record whether the result is exact.
- Name-based column hints are profiling candidates, not semantic conclusions.

## Example

```bash
python scripts/acquire_snapshot.py general_restaurants \
  --data-root "$KBL_DATA_ROOT"

python scripts/profile_artifact.py general_restaurants \
  "$KBL_DATA_ROOT/raw/general_restaurants/source.csv"
```

If neither `KBL_DATA_ROOT` nor `--data-root` is supplied, the sibling directory
`../korea-business-lifecycle-data` is used.

Outputs are written outside Git:

```text
$KBL_DATA_ROOT/staging/profiles/<source_key>/<sha256>/
  manifest.json
  profile.json
```

The profile contains schema, row counts, null/blank counts, bounded cardinality, date parseability, numeric ranges, and name-based status/address/identifier/coordinate hints. It does not declare a primary key or lifecycle semantics.
