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
- 32개 전체 deleted-code count probe: **384/384 완료**, 96개 source/authority pair 모두 post-reform count freeze 확인
- post-reform current-state enumeration policy: current 244 only, deleted 32 제외
- pre-reform old/new partition domain: 미확정, current+deleted 자동 union 금지

비용 계획은 2026-07-01을 경계로 분리합니다. pre-reform은 보수적으로 276 candidate union의 나머지 46개를 source별 1-request probe로 더하고, post-reform은 current 244만 사용하므로 current 공식 domain에서 관찰되지 않은 14개만 source별 probe합니다.

| Source | 230 non-empty paging | Pre-reform probes/range | Post-reform probes/range |
|---|---:|---:|---:|
| 일반음식점 | 22,954–23,183 | 46 / 23,000–23,229 | 14 / 22,968–23,197 |
| 휴게음식점 | 6,460–6,689 | 46 / 6,506–6,735 | 14 / 6,474–6,703 |
| 제과점영업 | 695–924 | 46 / 741–970 | 14 / 709–938 |
| **합계** | **30,109–30,796** | **138 / 30,247–30,934** | **42 / 30,151–30,838** |

이 범위는 historical row volume의 upper/lower bound가 아닙니다. bounded 실행에서는 삭제 code가 개편 후에도 non-empty인 frozen legacy partition으로 계속 query됐으므로, candidate union을 특정 날짜의 current-state와 동일하게 해석하지 않습니다.

## 2026-01-01 ~ 2026-09-06 planning scenarios

249 calendar-day window를 reform boundary에 맞춰 mixed planning range로 비교합니다.

| Scenario | Dates (pre/post) | 최대 gap | Request lower | Request upper | 승인 |
|---|---:|---:|---:|---:|---|
| endpoints only | 2 (1/1) | 248일 | 60,398 | 61,772 | 아니오 |
| monthly anchor + end | 10 (6/4) | 31일 | 302,086 | 308,956 | 아니오 |
| weekly 7-day + end | 37 (26/11) | 7일 | 1,118,083 | 1,143,502 | 아니오 |
| daily | 249 (181/68) | 1일 | 7,524,975 | 7,696,038 | 아니오 |

## 왜 daily도 lossless event log가 아닌가

history endpoint는 as-of snapshot입니다. daily 관찰도 다음을 증명하지 못합니다.

- 하루 안의 multiple state changes 부재
- snapshot 사이 exact transition timestamp
- 모든 intermediate change가 event log로 보존된다는 것
- `03→01`이 실제 재개업인지 행정 정정인지
- status `05`의 canonical 의미

daily cadence는 interval-censoring width를 줄일 뿐 event-log semantics를 만들지 않습니다.

## 현재 결정

`NO_NATIONWIDE_OBSERVATION_CADENCE_APPROVED_PRE_REFORM_AUTHORITY_DOMAIN_AND_COST_REVIEW_REQUIRED`

production reconstruction 전에는 최소한 다음이 필요합니다.

1. pre-reform old/new authority partition completeness와 overlap semantics 확인
2. 허용 가능한 request budget 결정
3. 분석 목적에 필요한 최대 censoring gap 결정
4. snapshot retention/중간 변화 손실 한계 수용 여부 결정
5. status `05` 및 reopening-vs-correction unresolved 상태 유지

bounded 실행 결과는 [History Authority Partition Semantics](history-authority-partition-semantics.md)에 기록합니다.

비용 모델은 network-free로 재현할 수 있습니다.

```bash
python scripts/history_observation_strategy.py
```
