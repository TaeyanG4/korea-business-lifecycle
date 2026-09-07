# Authenticated History Probe

The official v1 Swagger exposes `/history` for all three categories and requires:

- `serviceKey`
- `pageNo`
- `numOfRows` (maximum 100)
- `cond[BASE_DATE::EQ]` — from 2026-01-01 through the day before the query date
- `cond[OPN_ATMY_GRP_CD::EQ]`

Responses include `totalCount`, so pagination for one `(category, BASE_DATE, authority code)` query is finite. The official description is an **as-of-date state query**, however, and is not treated as a lossless event log.

The current snapshots contain the same 230 observed authority codes in all three categories, all seven-digit numeric strings. This is used for probe input validation, not as proof of an authoritative complete nationwide code domain.

`scripts/probe_history.py` makes exactly one page-1 request, stores no returned row values, and prints only aggregate metadata such as `totalCount`. The service key is supplied only through an environment variable.

```powershell
$env:KBL_DATA_GO_KR_SERVICE_KEY = "<data.go.kr Decoding key>"
python scripts/probe_history.py bakeries 20260101 3000000
```

Never commit or place the key in command-line arguments, logs, provenance, or a tracked `.env` file.
