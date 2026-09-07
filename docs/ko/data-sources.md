# v1 데이터 소스

확인일: **2026-09-07**

현재 행정안전부 공지 기준 지방행정 인허가 후보군은 **195종**입니다. 이는 구현 약속이 아니라 현재 inventory입니다.

- 195종 및 과거이력 서비스 공지: https://www.mois.go.kr/frt/bbs/type002/commonSelectBoardArticle.do?bbsId=BBSMSTR_000000000205&nttId=123477
- 195종 데이터 목록 공지: https://www.data.go.kr/bbs/ntc/selectNotice.do?originId=NOTICE_0000000004709
- 공공데이터 이용정책: https://www.data.go.kr/ugs/selectPortalPolicyView.do

## v1

| 카테고리 | API | 파일/표준 | 카탈로그 행 수 | 확인된 형식 | 공식 설명의 CRS |
|---|---|---|---:|---|---|
| 일반음식점 | `15154916` | 파일 `15045016`, 표준 `15096283` | 2,129,830 | CSV, REST JSON+XML | EPSG:5174 |
| 휴게음식점 | `15154921` | 파일 `15006730` | 561,397 | CSV, REST JSON+XML | EPSG:5174 |
| 제과점영업 | `15155252` | 표준 `15155672` + 공식 bulk URL | 60,302 | CSV, REST JSON+XML | EPSG:5174 |

제과점은 현재 표준 페이지 `15155672`가 bulk URL과 파일 메타데이터를 함께 제공하지만, 별도의 직접 파일 데이터 숫자 ID는 이번 reconnaissance에서 확정하지 않고 `UNKNOWN`으로 보존합니다.

세 소스의 공식 설명은 `인허가일자`, `영업상태`, `사업장명`, `소재지주소`를 명시합니다. 그러나 기본키, 폐업 의미, 이력 보존 하한, history의 완전성, X/Y 필드 의미는 아직 확정하지 않습니다.

상세한 기계 판독 레지스트리는 `provenance/source_registry.json`을 참조합니다.

