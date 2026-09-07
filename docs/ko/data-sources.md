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
| 제과점영업 | `15155252` | 파일 `15006688`, 표준 `15155672` | 60,302 | CSV, REST JSON+XML | EPSG:5174 |

제과점 전국 파일 데이터는 현재 공공데이터포털에서 `15006688`로 확인됩니다. 표준 데이터 식별자는 별도로 `15155672`입니다.

세 소스의 공식 설명은 `인허가일자`, `영업상태`, `사업장명`, `소재지주소`를 명시합니다. 그러나 기본키, 폐업 의미, 이력 보존 하한, history의 완전성, X/Y 필드 의미는 아직 확정하지 않습니다.

상세한 기계 판독 레지스트리는 `provenance/source_registry.json`을 참조합니다.

## 라이선스 판정 상태

세 API 페이지는 `이용허락범위 제한 없음`을 표시합니다. 그러나 공공데이터포털 정책은 제3자 권리가 포함된 공공데이터의 경우 권리자의 정당한 이용허락 확보가 필요하다고 명시합니다. 따라서 이 프로젝트는 공개 접근과 Kaggle 원자료 재배포를 분리하며, `provenance/license_review.json`에서 재배포 상태를 계속 `UNRESOLVED`로 유지합니다.
