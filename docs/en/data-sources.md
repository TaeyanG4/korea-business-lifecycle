# v1 data sources

Checked: **2026-09-07**

The current Ministry of the Interior and Safety inventory contains **195** local-government permit datasets. This is a versioned candidate inventory, not an implementation commitment.

- 195 datasets and history-service announcement: https://www.mois.go.kr/frt/bbs/type002/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000205&nttId=123477
- 195-dataset catalog notice: https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004709
- Public Data Portal use policy: https://www.data.go.kr/ugs/selectPortalPolicyView.do

## v1

| Category | API | File / standard | Catalog rows | Verified formats | CRS in official description |
|---|---|---|---:|---|---|
| General restaurants | `15154916` | file `15045016`, standard `15096283` | 2,129,830 | CSV, REST JSON+XML | EPSG:5174 |
| Rest cafes | `15154921` | file `15006730` | 561,397 | CSV, REST JSON+XML | EPSG:5174 |
| Bakeries | `15155252` | file `15006688`, standard `15155672` | 60,302 | CSV, REST JSON+XML | EPSG:5174 |

The current nationwide bakery file dataset is identified by the Public Data Portal as `15006688`. The separate standard-dataset identifier is `15155672`.

The official descriptions identify permit date, operating status, business name, and address concepts. Primary key, closure semantics, history retention lower bound/completeness, and X/Y field meanings remain unresolved.

See `provenance/source_registry.json` for the machine-readable registry.

Direct probes on 2026-09-07 established that the catalog `/file/<category>/info` URL is a download UI and the actual nationwide CSV action is `/file/download/<category>/info`. Current byte sizes observed through a Range probe were 696,584,488 bytes for general restaurants, 207,347,981 for rest cafes, and 22,654,977 for bakeries. These are point-in-time observations, not fixed source specifications.

## License-decision state

All three API pages display `이용허락범위 제한 없음` (no restriction on the displayed permitted-use scope). The Public Data Portal policy separately states that legitimate permission is required when third-party rights are included. The project therefore keeps public accessibility and Kaggle raw redistribution as separate gates; `provenance/license_review.json` remains `UNRESOLVED` for Kaggle redistribution.
