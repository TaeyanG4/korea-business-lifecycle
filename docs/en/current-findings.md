# v1 Current Snapshot Findings

On 2026-09-07 the three nationwide current snapshots were acquired outside Git, fixed by SHA-256, then fully profiled and audited.

- General restaurants: 2,295,369 rows / 696,584,488 bytes
- Rest cafes: 645,952 rows / 207,347,981 bytes
- Bakeries: 69,481 rows / 22,654,977 bytes
- Total: **3,010,802 rows / 926,587,446 bytes**
- All three are CP949 with 39 columns; exact column intersection and union are both 39.
- `관리번호` has no observed duplicates within each current snapshot or across the three categories. This is not a source-PK declaration and does not prove longitudinal stability.
- Ten rest-cafe rows and 561 general-restaurant rows have the source closed label while the closure-date field is blank, falsifying a closure-date-only rule.
- General restaurants contain four non-blank unparseable permit dates and three closure dates after the retrieval date.
- Telephone, business name, exact addresses, homepage and precise coordinates exist in the observed schema, so no public row-level allowlist is approved.

These findings are current-snapshot evidence only. Relocation, reopening, category transitions, history ordering and longitudinal identifier stability remain unresolved until authenticated history queries can be tested.
