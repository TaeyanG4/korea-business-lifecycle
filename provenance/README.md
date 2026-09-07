# Provenance

This directory stores small, reviewable evidence metadata only. It must not contain nationwide source files or unreviewed personal/contact data.

- `source_registry.json`: current authoritative source identifiers and explicitly unresolved claims.
- `license_review.json`: separate public-access and Kaggle-redistribution decision state.
- `privacy_review.json`: observed v1 field inventory plus the still-blocked public allowlist decision.
- `observed_snapshot_summary.json`: privacy-safe aggregate findings from the three acquired current snapshots; no row-level source values.
- `history_review.json`: official authenticated history-query contract and remaining execution/completeness blockers.
- `feasibility.json`: current project gate state.

Evidence was rechecked on 2026-09-07 against official `data.go.kr` and Ministry of the Interior and Safety pages. Current v1 snapshots are stored under the repository-local Git-ignored runtime tree; only hashes and aggregate audit results are tracked here, never the source rows themselves.
