# Provenance

This directory stores small, reviewable evidence metadata only. It must not contain nationwide source files or unreviewed personal/contact data.

- `source_registry.json`: current authoritative source identifiers and explicitly unresolved claims.
- `license_review.json`: separate public-access and Kaggle-redistribution decision state.
- `privacy_review.json`: observed v1 field inventory plus the still-blocked public allowlist decision.
- `observed_snapshot_summary.json`: privacy-safe aggregate findings from the three acquired current snapshots; no row-level source values.
- `history_review.json`: official authenticated history-query contract and remaining execution/completeness blockers.
- `reverse_transition_probe_plan.json`: the fixed six-snapshot follow-up plan for the two observed `03->01` cases.
- `reverse_transition_findings.json`: aggregate-only confirmation of the two source-state reversals and the rejection of irreversible terminal-closure semantics.
- `grain_decision.json`: frozen v1 parent/lifecycle row-grain decision, canonical-schema freeze state, bounded-real-validated PERMIT transformer gate, and explicitly rejected alternatives.
- `permit_parent_compatibility.json`: aggregate-only bounded validation of the frozen `PERMIT` transformer against 256 real current-snapshot rows per source; no row-level values or canonical output.
- `feasibility.json`: current project gate state.

Evidence was rechecked on 2026-09-07 against official `data.go.kr` and Ministry of the Interior and Safety pages. Current v1 snapshots are stored under the repository-local Git-ignored runtime tree; only hashes and aggregate audit results are tracked here, never the source rows themselves.
