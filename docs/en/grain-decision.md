# v1 Grain Decision

Checked: **2026-09-07**

## Decision

Food-Service v1 does not force every artifact into one row grain. It freezes two layers.

1. **Canonical parent grain: `PERMIT`**
   - One row represents one source permit record.
   - Different permits are never merged into one establishment merely because business name, address or coordinates look similar.
2. **Optional lifecycle analysis grain: `PERMIT_STATUS_EPISODE`**
   - One row represents one observed interval within a permit during which the source status state remains unchanged.
   - Confirmed `03→01` reversals mean closed status cannot be treated as an irreversible terminal state.

The raw/history observation grain remains `PERMIT_AS_OF_SNAPSHOT`: one permit row observed on one dated snapshot.

## Why `PERMIT` is the canonical parent

No duplicate `MNG_NO` was observed across the 3,010,802 current-snapshot rows, and the 15 bounded source×authority history pairs showed zero disappeared starting IDs, zero within-snapshot duplicates, and zero permit-date changes. Permit-level continuity is therefore strong in the current evidence.

This still does **not** declare `MNG_NO` to be an official primary key. A build must fail closed if the expected uniqueness invariant breaks, and `MNG_NO` is not promoted to establishment identity.

## Why lifecycle uses episodes

Two real cases changed as follows for the same `MNG_NO`:

```text
03 / closed / closure date populated
→
01 / active-normal / closure date blank
```

Permit date, business name, address and coordinates remained stable in both cases. Reopening versus administrative correction remains unresolved, but source-level reversibility is confirmed.

Therefore v1 rejects a one-row survival model in which one closure date is assumed to be a permanent terminal event.

## Rejected grains

### `ESTABLISHMENT_CATEGORY_EPISODE`

Not selected for v1. Evidence is insufficient to link different permits into a persistent establishment identity, and relocation, entity replacement, and identifier-reuse risks remain unresolved.

### `SINGLE_TERMINAL_SURVIVAL_ROW`

Explicitly rejected because source-state `03→01` reversals are confirmed.

## Episode-boundary rules

- A state transition observed only between sparse snapshots remains **interval-censored** rather than assigned an invented exact date.
- An episode that ends the observation window while still active remains **right-censored**.
- Status code `05` remains unmapped until its semantics are verified.
- Production episode reconstruction is not a required core-v1 artifact. It is generated only when an analyst elects the optional history workflow and satisfies the approved snapshot-completeness and censoring rules.

## v1 product scope

Under the final 2026-09-08 scope, the current `PERMIT` snapshot is core v1 while `PERMIT_STATUS_EPISODE` remains a frozen reference schema plus optional reconstruction tooling. The nationwide 7,320-task history acquisition therefore does not block core-v1 completion or publication of the Kaggle aggregate.

Establishment entity resolution and terminal-survival labels remain outside v1.

The machine-readable decision is `provenance/grain_decision.json`.
