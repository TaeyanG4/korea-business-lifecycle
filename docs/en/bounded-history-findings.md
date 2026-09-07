# Bounded History Audit Findings

> The follow-up sample expansion is complete. See [Five-Authority History Sample Findings](expanded-history-findings.md) for the current scoped conclusion.

Checked: **2026-09-07**

This is not a nationwide history harvest. It compares only two as-of snapshots, `2026-01-01` and `2026-09-06`, for one authority code (`3000000`) across general restaurants, rest cafes, and bakeries.

## Conclusion

All three categories are classified as `MNG_NO_CONTINUITY=STRONG` and `LIFECYCLE_SIGNAL=USABLE_FOR_FURTHER_AUDIT` for this bounded pair.

The classification uses exact contradiction/invariant checks only:

- zero duplicate `MNG_NO` values in either snapshot;
- zero starting `MNG_NO` values disappeared;
- zero permit-date changes among common `MNG_NO` values;
- every observed status change is row-aligned with a closure-date change;
- zero closure-date changes without a status change; and
- zero `03→01` transitions in this bounded pair.

This does **not** declare `MNG_NO` to be an official primary key or a persistent establishment identity.

## Results

| Category | Start | End | Common IDs | Added IDs | Disappeared IDs | Status changes | Permit-date changes |
|---|---:|---:|---:|---:|---:|---:|---:|
| Bakeries | 377 | 391 | 377 | 14 | 0 | 6 | 0 |
| Rest cafes | 5,428 | 5,542 | 5,428 | 114 | 0 | 94 | 0 |
| General restaurants | 20,314 | 20,571 | 20,314 | 257 | 0 | 199 | 0 |

Status changes and closure-date changes are aligned on the same rows: 6/6, 94/94, and 199/199 respectively.

## Additional cautions

- The end rest-cafe snapshot contains one status code `05` that was absent at the start. It must not be mapped to a canonical lifecycle state until its semantics are verified.
- Business name, address, and coordinates all changed together for 2 common rest-cafe `MNG_NO` values and 7 general-restaurant values. Follow-up sampling must distinguish relocation, correction, entity replacement, or identifier reuse without publishing raw values.
- Absence of a `03→01` transition in two snapshots does not prove reopening never occurs. Intermediate states are unobserved in this as-of comparison.

## Next gate

The project-wide grain is not frozen from this result alone. The next step is the same bounded audit over a small number of additional authorities with different characteristics to determine whether `MNG_NO` continuity remains stable across jurisdictions.

The machine-readable evidence is in `provenance/bounded_history_audit.json`. No raw `MNG_NO`, business-name, address, or coordinate values are included in public provenance.
