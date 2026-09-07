# Nationwide History Observation Strategy Cost Gate

확인일: **2026-09-07**

Optional `PERMIT_STATUS_EPISODE` 분석을 전국 범위로 확장할 때 사용할 authority enumeration과 observation cadence를 확정했습니다. 이 문서는 reference **MONTHLY_ANCHOR_PLUS_END** cadence와 그 비용/불완전성 한계를 기록합니다. **2026-09-08부터 이 workflow는 core v1 완료나 Kaggle aggregate 공개의 prerequisite가 아닙니다.**

## 계산 근거

- v1 source: 일반음식점 / 휴게음식점 / 제과점영업
- current rows: 3,010,802
- current snapshot에서 세 source 모두 동일하게 non-empty로 관찰된 numeric authority: 230개
- 2026-07-02 최신 공식 첨부의 current numeric authority: 244개
- current `_ALL` aggregate token: 16개 — row enumeration에서 제외
- 2026-07-01 개편으로 삭제 표시된 exact numeric authority: 32개
- 2026-07-01 개편으로 신규 표시된 exact numeric authority: 32개
- current + deleted candidate union: 276개
- current snapshot에서 candidate union 중 관찰되지 않은 code: source당 46개
- history API 최대 page size: 100
- exact current 244와 deleted 32 list ingestion/hash/validation: 완료
- authenticated bounded history execution: 가능
- bounded semantics: sampled deleted partition은 개편 전까지 변화한 뒤 post-reform frozen legacy state로 유지
- sampled current partition은 post-reform에도 변화 가능
- 32개 전체 deleted-code count probe: **384/384 완료**, 96개 source/authority pair 모두 post-reform count freeze 확인
- post-reform current-state enumeration policy: current 244 only, deleted 32 제외
- pre-reform current-state enumeration policy: current 244 - new 32 + deleted 32 = exact 244
- same-date old/new union: 사용하지 않음

비용 계획은 2026-07-01을 경계로 date-effective 244-code domain을 사용합니다. pre-reform은 `current-new+deleted` 244 전체의 current-row-scale paging bound를 계산하고, post-reform은 current 244 중 현재 snapshot에서 관찰되지 않은 14개를 source별 1회 probe하는 current-scale bound를 사용합니다.

| Source | 230 current non-empty paging | Pre-reform exact-244 range | Post-reform probes/range |
|---|---:|---:|---:|
| 일반음식점 | 22,954–23,183 | 22,954–23,197 | 14 / 22,968–23,197 |
| 휴게음식점 | 6,460–6,689 | 6,460–6,703 | 14 / 6,474–6,703 |
| 제과점영업 | 695–924 | 695–938 | 14 / 709–938 |
| **합계** | **30,109–30,796** | **30,109–30,838** | **42 / 30,151–30,838** |

이 범위는 historical row volume의 upper/lower bound가 아닙니다. bounded 실행에서는 삭제 code가 개편 후에도 non-empty인 frozen legacy partition으로 계속 query됐으므로, candidate union을 특정 날짜의 current-state와 동일하게 해석하지 않습니다.

## 2026-01-01 ~ 2026-09-06 planning scenarios

249 calendar-day window를 reform boundary에 맞춰 mixed planning range로 비교합니다.

| Scenario | Dates (pre/post) | 최대 gap | Request lower | Request upper | 승인 |
|---|---:|---:|---:|---:|---|
| endpoints only | 2 (1/1) | 248일 | 60,260 | 61,676 | 아니오 |
| **monthly anchor + end** | **10 (6/4)** | **31일** | **301,258** | **308,380** | **예** |
| weekly 7-day + end | 37 (26/11) | 7일 | 1,114,495 | 1,141,006 | 아니오 |
| daily | 249 (181/68) | 1일 | 7,499,997 | 7,678,662 | 아니오 |

## 왜 daily도 lossless event log가 아닌가

history endpoint는 as-of snapshot입니다. daily 관찰도 다음을 증명하지 못합니다.

- 하루 안의 multiple state changes 부재
- snapshot 사이 exact transition timestamp
- 모든 intermediate change가 event log로 보존된다는 것
- `03→01`이 실제 재개업인지 행정 정정인지
- status `05`의 canonical 의미

daily cadence는 interval-censoring width를 줄일 뿐 event-log semantics를 만들지 않습니다.

## 현재 결정

`OPTIONAL_MONTHLY_REFERENCE_CADENCE_AVAILABLE`

분석가가 optional production reconstruction을 선택한 경우에만 다음 gate를 적용합니다.

1. 10개 observation date × 3 source × 244 authority = **7,320 snapshot task**의 resumable nationwide acquisition 실행
2. 실행당 actual network attempt **400,000 hard cap**, 최소 request delay 0.2초 유지
3. 7,320 task가 모두 complete이고 task당 snapshot이 정확히 1개인지 preflight 확인
4. raw history page SHA-256을 검증하면서 production episode materialization
5. independent episode verifier PASS 확인
6. status `05`, reopening-vs-correction, event-log 한계는 그대로 유지

bounded 실행 결과는 [History Authority Partition Semantics](history-authority-partition-semantics.md)에 기록합니다.

비용 모델은 network-free로 재현할 수 있습니다.

```bash
python scripts/history_observation_strategy.py
```

실제 전국 수집은 장시간 실행이므로 optional이며 자동 시작하지 않습니다. `scripts/acquire_nationwide_history.py`는 기본 DRY_RUN입니다.

```bash
# network-free plan/current local completion state
py -3.12 scripts/acquire_nationwide_history.py

# long-running production acquisition; completed snapshots are skipped on rerun
py -3.12 scripts/acquire_nationwide_history.py --execute \
  --max-network-requests 400000 \
  --request-delay-seconds 0.2

# must report 7320 complete, 0 missing, 0 multiple before materialization
py -3.12 scripts/materialize_history_episodes.py --preflight

# local-only production episode build
py -3.12 scripts/materialize_history_episodes.py

# independent verifier; --build-id is optional when exactly one episode build exists
py -3.12 scripts/verify_history_episode_build.py
```
