# Nationwide History Observation Strategy Cost Gate

확인일: **2026-09-07**

production `PERMIT_STATUS_EPISODE`를 전국 범위로 확장하기 전에 as-of history API의 authority enumeration 의미와 observation cadence를 모두 확정해야 합니다. 이 문서는 **cadence를 승인하지 않고 비용과 불완전성만 계산**합니다.

## 계산 근거

- v1 source: 일반음식점 / 휴게음식점 / 제과점영업
- current rows: 3,010,802
- current snapshot에서 세 source 모두 동일하게 non-empty로 관찰된 numeric authority: 230개
- 2026-07-02 최신 공식 첨부의 current numeric authority: 244개
- current `_ALL` aggregate token: 16개 — row enumeration에서 제외
- 2026-07-01 개편으로 삭제 표시된 exact numeric authority: 32개
- current + deleted candidate union: 276개
- current snapshot에서 candidate union 중 관찰되지 않은 code: source당 46개
- history API 최대 page size: 100
- exact current 244와 deleted 32 list ingestion/hash/validation: 완료
- authenticated bounded history execution: 가능
- bounded semantics: sampled deleted partition은 개편 전까지 변화한 뒤 post-reform frozen legacy state로 유지
- sampled current partition은 post-reform에도 변화 가능
- 32개 전체 deleted-code count probe: 준비 완료, 미실행

비용 계획은 current snapshot의 230개 non-empty partition에 대한 paging 수학적 범위에 candidate union의 나머지 46개를 source별 1-request probe로 더합니다.

| Source | Current rows | 230 non-empty paging | Candidate probes | Planning range/date |
|---|---:|---:|---:|---:|
| 일반음식점 | 2,295,369 | 22,954–23,183 | 46 | 23,000–23,229 |
| 휴게음식점 | 645,952 | 6,460–6,689 | 46 | 6,506–6,735 |
| 제과점영업 | 69,481 | 695–924 | 46 | 741–970 |
| **합계** | **3,010,802** | **30,109–30,796** | **138** | **30,247–30,934** |

이 범위는 historical row volume의 upper/lower bound가 아닙니다. bounded 실행에서는 삭제 code가 개편 후에도 non-empty인 frozen legacy partition으로 계속 query됐으므로, candidate union을 특정 날짜의 current-state와 동일하게 해석하지 않습니다.

## 2026-01-01 ~ 2026-09-06 planning scenarios

249 calendar-day window를 동일한 current-scale planning range로 비교합니다.

| Scenario | Observation dates | 최대 observation gap | Request lower | Request upper | 승인 |
|---|---:|---:|---:|---:|---|
| endpoints only | 2 | 248일 | 60,494 | 61,868 | 아니오 |
| monthly anchor + end | 10 | 31일 | 302,470 | 309,340 | 아니오 |
| weekly 7-day + end | 37 | 7일 | 1,119,139 | 1,144,558 | 아니오 |
| daily | 249 | 1일 | 7,531,503 | 7,702,566 | 아니오 |

## 왜 daily도 lossless event log가 아닌가

history endpoint는 as-of snapshot입니다. daily 관찰도 다음을 증명하지 못합니다.

- 하루 안의 multiple state changes 부재
- snapshot 사이 exact transition timestamp
- 모든 intermediate change가 event log로 보존된다는 것
- `03→01`이 실제 재개업인지 행정 정정인지
- status `05`의 canonical 의미

daily cadence는 interval-censoring width를 줄일 뿐 event-log semantics를 만들지 않습니다.

## 현재 결정

`NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_LEGACY_AUTHORITY_PARTITION_POLICY_AND_COST_REVIEW_REQUIRED`

production reconstruction 전에는 최소한 다음이 필요합니다.

1. 준비된 384-request count-only probe로 삭제 32개 전체의 freeze/queryability 패턴 확인
2. frozen legacy partition을 날짜별 분석에 포함/제외하는 명시적 정책 결정
3. 허용 가능한 request budget 결정
4. 분석 목적에 필요한 최대 censoring gap 결정
5. snapshot retention/중간 변화 손실 한계 수용 여부 결정
6. status `05` 및 reopening-vs-correction unresolved 상태 유지

bounded 실행 결과는 [History Authority Partition Semantics](history-authority-partition-semantics.md)에 기록합니다.

비용 모델은 network-free로 재현할 수 있습니다.

```bash
python scripts/history_observation_strategy.py
```
