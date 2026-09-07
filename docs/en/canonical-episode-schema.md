# Canonical PERMIT_STATUS_EPISODE Schema

Checked: **2026-09-07**

The second Phase 4 schema milestone freezes the `PERMIT_STATUS_EPISODE` contract. This is **not** an episode-generation milestone. Production reconstruction remains disabled until an explicit nationwide history-observation strategy is approved.

## Row meaning

One row represents one maximal observed interval within a permit during which the **four-field source status tuple remains unchanged**.

The partition state consists only of:

- `source_status_code`
- `source_status_name`
- `source_detail_status_code`
- `source_detail_status_name`

Business-name, address, or coordinate changes do not split an episode. Codes `01`, `03`, and `05` are not converted into canonical active/closed/reopened semantics.

## Parent linkage

Episodes link to the `PERMIT` parent through `source_key + management_number`. This remains an empirical technical linkage candidate with strong bounded continuity, not a declared source primary key.

`episode_number` starts at one within a permit and a specific observation window. It can change if older history is later added, so it is not persistent identity and no `episode_id` is created.

## Start boundary

The first episode's true start is unknown and therefore `LEFT_CENSORED`:

```text
start_boundary_lower_date = null
start_boundary_upper_date = first_observed_date
```

Permit date is not substituted for episode start or physical opening date.

Every later episode begins with an `INTERVAL_CENSORED` transition between the previous state observation and the first observation of the new state:

```text
(start_boundary_lower_date, start_boundary_upper_date]
= (previous last_observed_date, current first_observed_date]
```

Even consecutive daily snapshots do not justify claiming an exact transition timestamp.

## End boundary

If a following episode exists, the current episode also ends with an interval-censored transition:

```text
(end_boundary_lower_date, end_boundary_upper_date]
= (current last_observed_date, next first_observed_date]
```

The final episode is `RIGHT_CENSORED`:

```text
end_boundary_lower_date = last_observed_date
end_boundary_upper_date = null
right_censored = true
```

This means only that the state was observed through the final date. It does not assert continued operation or a terminal event afterward.

## Closure-date handling

Closure date does not partition episodes. The schema preserves its first and last observed values plus `VALID | MISSING | INVALID` quality so correction/reversal signals are not erased.

The two confirmed cases reverted from `03/closed + populated closure date` to `01/operating-normal + blank closure date`, so closure date cannot be promoted to a permanent terminal event.

## Explicitly absent fields

- `establishment_id`
- persistent `episode_id`
- canonical active/closed flags
- terminal-event flag
- exact event/open/close date
- `reopened_flag`
- `duration_days`

In particular, a `reopened_flag` is not created because a source-state reversal cannot yet be distinguished from real-world reopening versus administrative correction.

## Next step

Both canonical schema contracts remain frozen. The production `PERMIT` parent is now complete, and a bounded in-memory episode reconstructor for explicitly supplied sparse observations has been implemented and synthetic-tested. Nationwide production episode reconstruction remains disabled because no nationwide history-observation strategy has been approved.

The bounded implementation contract is documented in [Bounded PERMIT_STATUS_EPISODE Reconstruction](bounded-episode-reconstruction.md).

The machine-readable contract is `schemas/permit_status_episode.v1.json`.
