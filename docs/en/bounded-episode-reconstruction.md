# Bounded PERMIT_STATUS_EPISODE Reconstruction

Checked: **2026-09-07**

Production `PERMIT_STATUS_EPISODE` reconstruction remains disabled. A separate **bounded in-memory reconstructor** is implemented for explicitly supplied sparse as-of observations only.

## Safety boundary

- maximum observations: 100,000 per call;
- no history-API acquisition;
- no interpolation of missing dates;
- exactly one observation required per `source_key + management_number + observed_date`;
- observations outside the declared window fail closed;
- `MNG_NO` is not declared an official primary key; and
- nationwide production reconstruction is not enabled.

The implementation is `reconstruct_bounded_status_episodes` in `src/korea_business_lifecycle/episode_reconstruction.py`.

## Episode partition

Episodes split only when the frozen four-field source status tuple changes:

- `source_status_code`
- `source_status_name`
- `source_detail_status_code`
- `source_detail_status_name`

A closure-date change alone does not split an episode. Business name, address, and coordinates are not part of the input contract.

## Censoring

The first episode is `LEFT_CENSORED`:

```text
start lower = null
start upper = first observed date
```

When source state changes, the transition is only bounded between the previous episode's last observation and the next episode's first observation:

```text
(previous last observed, next first observed]
```

Both sides therefore use `INTERVAL_CENSORED` boundaries. No exact event date is created.

The final episode is `RIGHT_CENSORED`; no state is inferred after the last observation.

## Status semantics

- `03` is not irreversible terminal;
- `05` is preserved as raw source state;
- no `reopened_flag`;
- no canonical active/closed flags;
- no terminal event; and
- permit date is not used as episode start.

A real `03→01`-like reversal is represented only as two source-state episodes with an interval-censored transition. The reconstructor does not decide whether that represents real reopening or administrative correction.

## Closure date

Closure date is retained only as first/last observed episode context. Inputs inconsistent with `VALID | MISSING | INVALID` quality fail closed.

## Current gate

- synthetic/fail-closed tests: 11 PASS on Python 3.11 and 3.12;
- bounded reconstructor: IMPLEMENTED / SYNTHETIC VALIDATED;
- nationwide production reconstruction: **DISABLED**;
- nationwide lossless event history: unavailable;
- status `05` semantics: unresolved; and
- reopening vs correction: unresolved.

The next step is not to scale this reconstructor to production. It is to define an explicit **nationwide history-observation strategy** first.
