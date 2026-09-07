# History sample expansion plan

After completing the bounded longitudinal audit for authority `3000000`, four additional authorities were selected deterministically from the combined current-row scale distribution across the three v1 categories.

| Stratum | Authority code | Combined current rows | Expected API requests for two dates |
|---|---:|---:|---:|
| q10 | `4420000` | 1,984 | 43 |
| q50 | `4530000` | 9,323 | 188 |
| q90 | `3830000` | 28,136 | 561 |
| max | `3220000` | 70,649 | 1,400 |

The expansion queries only `2026-01-01` and `2026-09-06` for the three v1 categories. Including the completed baseline gives five authorities in total. The four added authorities require an estimated **2,192 requests** from the authenticated probes.

This is not a statistically representative nationwide probability sample. Its purpose is to test whether `MNG_NO` continuity, status/closure behavior, and status-vocabulary drift remain consistent across very different authority sizes.

## Safe execution

Run the network-free dry-run first:

```powershell
python scripts/acquire_history_sample.py
```

Actual acquisition requires explicit `--execute`:

```powershell
python scripts/acquire_history_sample.py --execute
```

The runner cannot expand beyond the tracked authority/date/category plan, refuses a plan above 2,500 expected requests, and skips already completed snapshots so interrupted runs can be resumed. The real service key is loaded only from the local `.env` or environment and is never emitted or written to manifests.

After acquisition, generate the aggregate-only audit with:

```powershell
python scripts/audit_history_sample.py --authority 4420000 --authority 4530000 --authority 3830000 --authority 3220000
```
