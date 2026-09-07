# Canonical PERMIT_STATUS_EPISODE Schema

확인일: **2026-09-07**

Phase 4의 두 번째 schema milestone으로 `PERMIT_STATUS_EPISODE` 계약을 동결합니다. 이 단계는 **episode를 생성하는 단계가 아닙니다.** 전국 history observation 전략이 승인되기 전까지 production reconstruction은 계속 비활성화합니다.

## 행의 의미

한 행은 한 permit 안에서 **source status 4튜플이 연속해서 동일하게 관찰되는 최대 구간**입니다.

상태 partition에 사용하는 값은 다음 네 source 필드뿐입니다.

- `source_status_code`
- `source_status_name`
- `source_detail_status_code`
- `source_detail_status_name`

사업장명·주소·좌표 변화로 episode를 나누지 않으며, `01`, `03`, `05`를 canonical active/closed/reopened 상태로 해석하지 않습니다.

## Parent 연결

episode는 `source_key + management_number`로 `PERMIT` parent와 연결합니다. 이 조합은 현재 관찰에서 강한 continuity를 보인 기술적 linkage candidate일 뿐 공식 PK 선언이 아닙니다.

`episode_number`는 한 permit과 한 observation window 안에서 1부터 증가합니다. 더 오래된 history가 나중에 추가되면 번호가 바뀔 수 있으므로 persistent identity가 아닙니다. 따라서 `episode_id`도 만들지 않습니다.

## 시작 경계

첫 episode의 실제 시작일은 알 수 없으므로 `LEFT_CENSORED`입니다.

```text
start_boundary_lower_date = null
start_boundary_upper_date = first_observed_date
```

`permit_date`를 episode 시작일이나 실제 개업일로 대신 사용하지 않습니다.

두 번째 이후 episode는 이전 상태의 마지막 관찰과 새 상태의 첫 관찰 사이에서 상태가 바뀐 것이므로 `INTERVAL_CENSORED`입니다.

```text
(start_boundary_lower_date, start_boundary_upper_date]
= (previous last_observed_date, current first_observed_date]
```

하루 연속 snapshot이라도 전환 시각을 정확한 날짜/시각으로 주장하지 않습니다.

## 종료 경계

다음 episode가 있으면 종료도 interval-censored입니다.

```text
(end_boundary_lower_date, end_boundary_upper_date]
= (current last_observed_date, next first_observed_date]
```

마지막 episode는 `RIGHT_CENSORED`입니다.

```text
end_boundary_lower_date = last_observed_date
end_boundary_upper_date = null
right_censored = true
```

이는 마지막 관찰일까지 해당 상태였다는 뜻일 뿐, 그 이후 영업 지속이나 terminal closure를 주장하지 않습니다.

## 폐업일자 처리

폐업일자는 episode 경계를 만드는 필드가 아닙니다. 각 episode의 첫/마지막 관찰에서 source closure date와 `VALID | MISSING | INVALID` quality를 보존하여 정정·역전 신호를 잃지 않게 합니다.

실제 두 사례에서 `03/폐업 + 폐업일자 값`이 다음 날 `01/영업/정상 + 폐업일자 공백`으로 되돌아갔으므로 `폐업일자`를 permanent terminal event로 승격하지 않습니다.

## 명시적으로 만들지 않는 필드

- `establishment_id`
- persistent `episode_id`
- canonical active/closed flag
- terminal event flag
- exact event/open/close date
- `reopened_flag`
- `duration_days`

특히 `reopened_flag`는 source-state reversal과 현실의 실제 재개업을 구분할 수 없으므로 만들지 않습니다.

## 다음 단계

두 canonical schema 계약이 모두 동결됐습니다. 다음 구현 단계에서는 먼저 current snapshot → `PERMIT` parent의 deterministic transformer를 구현하는 것이 안전합니다. 전국 episode reconstruction은 계속 비활성화합니다.

기계 판독 schema는 `schemas/permit_status_episode.v1.json`에 있습니다.
