# Five-Authority History Sample Findings

Checked: **2026-09-07**

The completed baseline authority `3000000` was expanded with deterministic q10/q50/q90/max scale representatives (`4420000`, `4530000`, `3830000`, `3220000`). The comparison remains bounded to `2026-01-01` versus `2026-09-06` across general restaurants, rest cafes, and bakeries.

This is not a probability sample. Its purpose is to test whether identity and lifecycle signals remain consistent across authorities with very different current-data scales.

## Core results

- 5 authorities × 3 categories = **15 source×authority pairs**
- 133,832 start rows and 136,598 end rows
- 133,832 common `MNG_NO` values
- 2,766 added `MNG_NO` values
- **0** starting IDs disappeared
- **0** duplicate `MNG_NO` rows within bounded snapshots
- **0** permit-date changes among common `MNG_NO` values
- 1,994 status changes and 1,994 closure-date changes aligned on the same rows
- **0** closure-date changes without a status change

All 15/15 pairs therefore retain `MNG_NO_CONTINUITY=STRONG` in this bounded sample. This is still not a declaration of an official primary key or persistent establishment identity.

## Newly observed lifecycle signal

The expanded sample contains **two `03→01` reverse transitions**.

| Authority | Category | Transition | Closure-date change |
|---|---|---|---|
| `3830000` | Rest cafes | `03→01` | value → blank |
| `4530000` | General restaurants | `03→01` | value → blank |

The three-date follow-up reproduced both transitions as `closed (03) → operating/normal (01)` with the closure-date field changing from populated to blank. Permit date, business name, address and coordinates remain unchanged. The source-level reversal is therefore confirmed, while reopening versus administrative correction remains unresolved.

This rejects code `03` as an assumed irreversible terminal closure for survival analysis.

## Status-vocabulary drift

Status code `05` newly appears in two pairs:

- rest cafes for authority `3000000`;
- bakeries for authority `3220000`.

It remains unmapped until its semantics are confirmed from the official status-code reference.

## Additional identity signal

Business name, address and coordinates all changed together for 42 common `MNG_NO` values across 9 pairs. These are not automatically labeled as relocation or identifier reuse. A small private bounded review is required to separate relocation, correction, entity replacement and possible reuse.

## Current assessment

```text
MNG_NO continuity: CONSISTENT_ACROSS_SAMPLE
lifecycle: SOURCE_STATE_REVERSAL_CONFIRMED
terminal closure irreversibility: REJECTED
source PK: NOT DECLARED
establishment identity: NOT DECLARED
```

The next gate is to freeze an analysis grain that can represent reversible status episodes, then review status code `05` and selected simultaneous identity-attribute changes. A nationwide daily-history crawl is not required.

Machine-readable results are in `provenance/expanded_history_audit.json`. No raw `MNG_NO`, business-name, address or coordinate values are committed to public provenance.
