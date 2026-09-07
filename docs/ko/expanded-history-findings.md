# 5개 자치단체 History 표본 확장 결과

확인일: **2026-09-07**

기존 `3000000` 한 곳의 bounded audit에 규모별 q10/q50/q90/max 대표 네 곳(`4420000`, `4530000`, `3830000`, `3220000`)을 추가했습니다. 비교 시점은 동일하게 `2026-01-01`과 `2026-09-06`, 카테고리는 일반음식점·휴게음식점·제과점영업 세 종류입니다.

이 표본은 통계적 확률표본이 아닙니다. 목적은 규모가 다른 자치단체에서도 identity/lifecycle 신호가 일관되는지 확인하는 것입니다.

## 핵심 결과

- 5개 자치단체 × 3카테고리 = **15 source×authority pair**
- 시작 133,832행, 종료 136,598행
- 공통 `MNG_NO` 133,832건
- 신규 `MNG_NO` 2,766건
- 시작 ID 소실 **0건**
- snapshot 내부 `MNG_NO` 중복 **0건**
- 공통 `MNG_NO`의 인허가일자 변경 **0건**
- 상태 변경 1,994건과 폐업일자 변경 1,994건이 동일 행에서 일치
- 상태 변경 없는 폐업일자 변경 **0건**

따라서 이번 표본의 15/15 pair에서 `MNG_NO_CONTINUITY=STRONG`이 유지됐습니다. 그러나 이것은 공식 PK 또는 establishment identity 선언이 아닙니다.

## 새로 발견된 lifecycle 신호

확장 표본에서 `03→01` 역전이가 **2건** 확인됐습니다.

| 자치단체코드 | 카테고리 | 전이 | 폐업일자 변화 |
|---|---|---|---|
| `3830000` | 휴게음식점 | `03→01` | 값 → 빈값 |
| `4530000` | 일반음식점 | `03→01` | 값 → 빈값 |

후속 3일 probe에서 두 사례 모두 실제로 `폐업(03) → 영업/정상(01)` 전환이 재현됐고, 폐업일자는 값에서 빈값으로 바뀌었습니다. permit date, 사업장명, 주소, 좌표는 그대로였습니다. 따라서 source-level 역전은 확인됐지만 **재개업**인지 **행정정정**인지는 여전히 구분하지 않습니다.

이 결과로 `03`을 영구적인 terminal closure로 간주하는 survival rule은 **채택하지 않습니다**.

## 상태 vocabulary drift

상태코드 `05`가 두 pair에서 새로 등장했습니다.

- `3000000` 휴게음식점
- `3220000` 제과점영업

공식 상태코드 reference에서 의미를 확인하기 전에는 canonical lifecycle state로 매핑하지 않습니다.

## Identity 관련 추가 신호

사업장명+주소+좌표가 모두 동시에 변경된 공통 `MNG_NO`는 전체 표본에서 42건, 9개 pair에 걸쳐 존재했습니다. 이는 자동으로 relocation 또는 identifier reuse로 분류하지 않습니다. 다음 단계에서 소수 사례를 비공개 bounded review로 구분해야 합니다.

## 현재 판정

```text
MNG_NO continuity: CONSISTENT_ACROSS_SAMPLE
lifecycle: SOURCE_STATE_REVERSAL_CONFIRMED
terminal closure irreversibility: REJECTED
source PK: NOT DECLARED
establishment identity: NOT DECLARED
```

다음 gate는 reversible 상태를 표현할 수 있는 분석 grain을 동결하고, 상태코드 `05`와 identity-attribute 동시변경 사례를 추가 검토하는 것입니다. 전국 daily-history 크롤링은 필요하지 않습니다.

기계 판독 결과는 `provenance/expanded_history_audit.json`에 있습니다. 원문 `MNG_NO`, 사업장명, 주소, 좌표 값은 public provenance에 포함하지 않습니다.
