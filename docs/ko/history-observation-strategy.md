# Nationwide History Observation Strategy Cost Gate

확인일: **2026-09-07**

production `PERMIT_STATUS_EPISODE`를 전국 범위로 확장하기 전에, as-of history API를 어떤 cadence로 관찰할지 결정해야 합니다. 이 문서는 **cadence를 승인하지 않고 비용과 완전성 한계만 계산**합니다.

## 계산 근거

- v1 source: 일반음식점 / 휴게음식점 / 제과점영업
- current rows: 3,010,802
- current snapshot에서 세 source 모두 동일하게 관찰된 authority code: 230개
- history API 최대 page size: 100
- observed authority domain의 authoritative completeness: 미확인
- 비용 기준: current row scale의 수학적 paging bounds
- 실제 history row count forecast가 아님
- network access: 없음

authority별 query가 필요하므로 current row scale에서 전국 as-of 날짜 **1개**의 요청 수는 다음 범위입니다.

| Source | Current rows | Lower bound/date | Upper bound/date |
|---|---:|---:|---:|
| 일반음식점 | 2,295,369 | 22,954 | 23,183 |
| 휴게음식점 | 645,952 | 6,460 | 6,689 |
| 제과점영업 | 69,481 | 695 | 924 |
| **합계** | **3,010,802** | **30,109** | **30,796** |

## 2026-01-01 ~ 2026-09-06 비용 시나리오

249 calendar-day window를 대상으로 cadence별 비용만 비교합니다.

| 시나리오 | Observation dates | 최대 observation gap | Request lower | Request upper | 승인 |
|---|---:|---:|---:|---:|---|
| endpoints only | 2 | 248일 | 60,218 | 61,592 | 아니오 |
| monthly anchor + end | 10 | 31일 | 301,090 | 307,960 | 아니오 |
| weekly 7-day + end | 37 | 7일 | 1,114,033 | 1,139,452 | 아니오 |
| daily | 249 | 1일 | 7,497,141 | 7,668,204 | 아니오 |

위 숫자는 실제 historical row volume의 보장이 아니라 **현재 row scale에서의 paging cost bound**입니다.

## 왜 daily도 lossless event log가 아닌가

history endpoint는 as-of snapshot입니다. daily 관찰을 하더라도 다음을 증명하지 못합니다.

- 하루 안에 여러 번 상태가 바뀌지 않았다는 것
- snapshot 사이의 exact transition timestamp
- source가 모든 intermediate change를 event log로 보존한다는 것
- `03→01`이 실제 재개업인지 행정 정정인지
- status `05`의 canonical 의미

daily cadence는 interval-censoring width를 줄일 뿐 event-log semantics를 만들지 않습니다.

## 현재 결정

`NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_COST_AND_COMPLETENESS_REVIEW_REQUIRED`

production reconstruction을 시작하기 전에 최소한 다음이 필요합니다.

1. authoritative nationwide `OPN_ATMY_GRP_CD` domain 검증
2. 허용 가능한 request budget 결정
3. 분석 목적에 필요한 최대 censoring gap 결정
4. snapshot retention/중간 변화 손실 한계 수용 여부 결정
5. status `05` 및 reopening-vs-correction unresolved 상태를 어떻게 보존할지 유지

비용 모델은 network-free 명령으로 재현할 수 있습니다.

```bash
python scripts/history_observation_strategy.py
```
