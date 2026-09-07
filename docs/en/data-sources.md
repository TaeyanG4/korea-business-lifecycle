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
| Bakeries | `15155252` | standard `15155672` + official bulk URL | 60,302 | CSV, REST JSON+XML | EPSG:5174 |

For bakeries, standard page `15155672` currently exposes the bulk URL and file metadata. A separate direct numeric file-dataset ID was not established in this reconnaissance and remains `UNKNOWN` rather than inferred.

The official descriptions identify permit date, operating status, business name, and address concepts. Primary key, closure semantics, history retention lower bound/completeness, and X/Y field meanings remain unresolved.

See `provenance/source_registry.json` for the machine-readable registry.

