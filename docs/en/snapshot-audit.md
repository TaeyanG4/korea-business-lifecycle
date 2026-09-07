# Current Snapshot Grain / Lifecycle Audit

`audit_snapshot.py` measures only falsifiable current-snapshot evidence before any Phase 3 longitudinal conclusion.

- It exactly measures nulls/uniqueness/duplicates for `관리번호` and `(개방자치단체코드, 관리번호)` using disk-backed SQLite.
- It counts duplicate parsed rows using SHA-256 of length-prefixed parsed fields, explicitly distinct from a raw-byte identity claim.
- It cross-checks the source `영업상태명=폐업` label against presence of `폐업일자`.
- It counts closure-before-permit, dates after retrieval, and non-blank unparseable dates.
- It reports only non-blank counts for business name, phone, road address, and lot address; those source values are never emitted to the audit JSON.
- It checks X/Y pair completeness, numeric parse failures, zeros, and negative values without performing a CRS transform.

This audit cannot establish relocation, category changes, reopening, history ordering, or longitudinal identifier stability. Those require history access.
