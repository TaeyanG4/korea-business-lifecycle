# 03→01 Reverse-Transition Follow-up Probe

The expanded sample audit found two `03→01` reversals. In both cases the closure date changed from populated to blank while permit date, business name, address, and coordinates were unchanged at the two endpoints.

This follow-up is not a nationwide history harvest. It uses the end-row `LAST_MDFCN_PNT` date as a candidate and queries only the day before, the candidate day, and the day after.

- Rest cafes / `3830000`: `2026-08-31`, `2026-09-01`, `2026-09-02`
- General restaurants / `4530000`: `2026-03-16`, `2026-03-17`, `2026-03-18`

There are six snapshots total with a hard network-request cap of 411. No raw `MNG_NO`, business name, address, coordinate, or closure-date value is emitted to public output.

## Execution

Dry run:

```powershell
python scripts/acquire_reverse_transition_probes.py
```

Execute:

```powershell
python scripts/acquire_reverse_transition_probes.py --execute
```

Then run the aggregate-only audit:

```powershell
python scripts/audit_reverse_transition_probes.py
```

If the transition is not visible in the three-date window, the tool does not automatically broaden the crawl. A new bounded plan is required.

