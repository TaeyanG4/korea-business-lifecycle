# Official Authority-Domain Reference Gate

확인일: **2026-09-07**

전국 history API는 `OPN_ATMY_GRP_CD`(개방자치단체코드)별 조회가 필요합니다. 이 gate는 **현재 유효 코드**, **2026-07-01 개편으로 삭제된 코드**, 그리고 **Jan–Sep history window에서 실제로 어떤 코드를 query해야 하는지**를 분리합니다.

## 공식 근거의 시간 순서

2026년 1월 LOCALDATA `공공데이터포털 이용 매뉴얼`은 `개방자치단체코드.xlsx` 참고문서에서 **245개의 시도·시군구 지방자치단체 코드**를 확인한다고 설명합니다. 이 숫자는 문서상 근거로 보존하지만 최신 exact query domain으로 승격하지 않습니다.

공공데이터포털의 2026-07-03 행정안전부 공지는 `전남광주통합특별시 및 인천형 행정체제개편('26.7.1.)`에 따른 자치단체코드 삭제·신규 부여를 안내하고, `개방자치단체코드_영업상태코드_행정체제개편반영_20260702.xlsx`를 제공합니다.

로컬에 보관한 공식 첨부는 Git-ignored이며 SHA-256은 다음과 같습니다.

`d032ff4bd63148238a8066afb7b62f96770d8a063bd6c632d4f7617e9cc407f8`

## 최신 공식 첨부 파싱 결과

`1. 개방자치단체코드` 시트를 strict parser로 읽은 결과입니다.

- 현재 활성 행: **260**
- 현재 활성 7자리 숫자 코드: **244**
- 현재 활성 `_ALL` 집계 토큰: **16**
- 삭제 표시 행: **34** = 숫자 코드 32 + `_ALL` 2
- 신규 표시 행: **33** = 숫자 코드 32 + `_ALL` 1
- 현재 244개 숫자 code/name 목록 SHA-256: `a666c5cb432c439f687064e3046ec2e9a84d2de708dfbe80817330e60b76ddad`

따라서 1월 매뉴얼의 `245`를 최신 exact list로 사용할 수 없습니다. 최신 첨부의 **현재 숫자 domain은 244개**이며 `_ALL` 토큰은 row-level authority enumeration에 사용하지 않습니다.

## current snapshot과 비교

세 v1 current snapshot의 authority code set은 서로 동일한 **230개**이고 모두 최신 244개 숫자 domain의 subset입니다.

- current official numeric: **244**
- current observed non-empty: **230**
- current official but unobserved: **14**
- current snapshot에 남은 삭제 코드: **0**

현재 reference date에 대한 244개 exact code/name list는 tracked provenance에 ingestion·hash·validation 완료했습니다.

## Jan–Sep history window의 추가 gate

2026-07-01 개편에서 삭제된 **32개 숫자 코드**도 exact change reference로 ingestion했습니다. 현재 244개와 삭제 32개는 서로 겹치지 않으므로 보수적인 history-window candidate union은 **276개**입니다.

그러나 이 276개를 단순히 “정답 query domain”이라고 부르지는 않습니다. 공식 문서에서 다음이 확인되지 않았기 때문입니다.

- 삭제된 code가 개편 전 `BASE_DATE`에서 계속 query 가능한지
- source가 과거 snapshot을 old code로 유지하는지 또는 new code로 재매핑하는지
- 1월 매뉴얼의 245 count와 exact date-effective domain의 차이를 어떻게 해석해야 하는지

따라서 현재 상태는 다음과 같습니다.

- exact current 244 numeric list: **완료**
- exact deleted 32 numeric list: **완료**
- current-reference numeric enumeration: **ready**
- Jan–Sep date-effective history enumeration: **not ready**
- future source snapshot: reference 재검증 필요

## Cost model과의 관계

비용 계획에서는 보수적으로 current+deleted **276개 candidate union**을 모두 probe한다고 가정합니다. current snapshot에서 non-empty인 230개 외에 46개 candidate를 source별 1회씩 확인하는 current-scale planning range는 **30,247–30,934 requests/as-of-date**입니다.

이 숫자는 historical row-count upper/lower bound가 아닙니다. 삭제 code가 과거 날짜에 non-empty일 수 있으므로 실제 historical paging은 달라질 수 있습니다.

## 다음 gate

production nationwide history acquisition 전에는 삭제된 32개 코드의 date-effective history filter semantics를 공식 문서 또는 bounded authenticated probe로 확인하고, 그 다음 cadence/request budget을 명시적으로 승인해야 합니다.
