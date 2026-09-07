# Bounded PERMIT_STATUS_EPISODE Reconstruction

확인일: **2026-09-07**

`PERMIT_STATUS_EPISODE` production reconstruction은 여전히 비활성화되어 있습니다. 대신 명시적으로 제공된 sparse as-of observation만 대상으로 하는 **bounded in-memory reconstructor**를 구현했습니다.

## 안전 경계

- 최대 observation 수: 100,000 / call
- history API 취득 기능 없음
- missing date를 자동 보간하지 않음
- 한 `source_key + management_number + observed_date`당 정확히 1개 observation 요구
- observation window 밖 row는 fail-closed
- `MNG_NO`를 공식 PK로 선언하지 않음
- nationwide production reconstruction을 활성화하지 않음

구현은 `src/korea_business_lifecycle/episode_reconstruction.py`의 `reconstruct_bounded_status_episodes`입니다.

## Episode partition

episode는 frozen schema와 동일하게 다음 source status 4튜플이 바뀔 때만 split합니다.

- `source_status_code`
- `source_status_name`
- `source_detail_status_code`
- `source_detail_status_name`

폐업일자 변화만으로 episode를 나누지 않습니다. 사업장명·주소·좌표는 입력 계약에도 없습니다.

## Censoring

첫 episode는 `LEFT_CENSORED`입니다.

```text
start lower = null
start upper = first observed date
```

상태가 바뀌면 transition은 이전 episode의 마지막 관찰일과 다음 episode의 첫 관찰일 사이로만 압축합니다.

```text
(previous last observed, next first observed]
```

따라서 양쪽 episode 경계가 `INTERVAL_CENSORED`이며 exact event date를 생성하지 않습니다.

마지막 episode는 `RIGHT_CENSORED`입니다. 마지막 관찰 이후 상태를 추론하지 않습니다.

## 상태 의미

- `03`은 irreversible terminal이 아님
- `05`는 raw source state로 그대로 보존
- `reopened_flag` 없음
- canonical active/closed flag 없음
- terminal event 없음
- permit date를 episode 시작일로 사용하지 않음

실제 `03→01` 같은 reversal도 두 source-state episode와 interval-censored transition으로만 표현합니다. 실제 재개업인지 행정 정정인지는 판정하지 않습니다.

## Closure date

closure date는 episode의 첫/마지막 관찰 context로만 보존합니다. `VALID | MISSING | INVALID` quality와 일관되지 않는 입력은 fail-closed합니다.

## 현재 gate

- synthetic/fail-closed tests: Python 3.11/3.12 각각 11 PASS
- bounded reconstructor: IMPLEMENTED / SYNTHETIC VALIDATED
- nationwide production reconstruction: **DISABLED**
- nationwide lossless event history: 확보되지 않음
- status `05` semantics: unresolved
- reopening vs correction: unresolved

다음 단계는 이 reconstructor를 production으로 확대하는 것이 아니라, 먼저 **전국 history observation 전략**을 명시적으로 결정하는 것입니다.
