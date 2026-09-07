# v1 Grain 결정

확인일: **2026-09-07**

## 결정

Food-Service v1은 하나의 grain으로 모든 데이터를 표현하지 않고 두 층으로 고정합니다.

1. **Canonical parent grain: `PERMIT`**
   - 한 행은 하나의 source permit record를 의미합니다.
   - 사업장명·주소·좌표가 비슷하다는 이유만으로 서로 다른 permit을 하나의 사업체로 합치지 않습니다.
2. **Lifecycle analysis grain: `PERMIT_STATUS_EPISODE`**
   - 한 행은 같은 permit 안에서 source status state가 연속해서 유지되는 하나의 관찰 구간을 의미합니다.
   - `03→01` 역전이 실제로 확인됐으므로 폐업 상태를 영구 terminal state로 가정하지 않습니다.

원천/history snapshot 자체의 관찰 grain은 `PERMIT_AS_OF_SNAPSHOT`입니다. 즉 특정 날짜에 관찰된 permit row 하나가 한 행입니다.

## 왜 `PERMIT`을 parent로 선택했는가

현재 전국 snapshot 3,010,802행에서 `MNG_NO` 중복이 관찰되지 않았고, 5개 자치단체 × 3카테고리의 15개 bounded history pair에서도 시작 ID 소실·snapshot 내부 중복·permit-date 변경이 모두 0건이었습니다. 따라서 permit-level continuity는 현재 증거에서 강합니다.

그러나 이것은 `MNG_NO`가 공식 PK라는 뜻이 아닙니다. 빌드 중 예상 uniqueness가 깨지면 즉시 실패해야 하며, `MNG_NO`를 establishment identity로 승격하지 않습니다.

## 왜 lifecycle은 episode인가

두 실제 사례에서 같은 `MNG_NO`가 다음과 같이 되돌아갔습니다.

```text
03 / 폐업 / 폐업일자 있음
→
01 / 영업/정상 / 폐업일자 빈값
```

두 사례 모두 permit date, 사업장명, 주소, 좌표가 유지됐습니다. 현실의 재개업인지 행정정정인지는 아직 구분하지 않지만, source-level state가 reversible하다는 사실은 확인됐습니다.

따라서 `폐업일자 하나 = 영구 종료 이벤트 하나`인 단일 survival row 모델은 v1에서 사용하지 않습니다.

## 채택하지 않는 grain

### `ESTABLISHMENT_CATEGORY_EPISODE`

v1에서는 채택하지 않습니다. 서로 다른 permit을 동일 사업체로 연결할 근거가 아직 부족하며, relocation·entity replacement·identifier reuse 가능성도 남아 있습니다.

### `SINGLE_TERMINAL_SURVIVAL_ROW`

명시적으로 거부합니다. `03→01` source-state reversal이 실제로 확인됐기 때문입니다.

## Episode 경계 규칙

- sparse snapshot 사이의 상태 변화 시점은 정확한 날짜라고 주장하지 않고 **interval-censored**로 보존합니다.
- active 상태로 관찰이 끝난 episode는 **right-censored**입니다.
- 상태코드 `05`는 의미가 확인될 때까지 canonical state로 매핑하지 않습니다.
- 전국 daily history를 확보하지 않은 현재는 production episode reconstruction을 활성화하지 않습니다.

## 다음 단계

Phase 4에서는 이 grain 결정을 바탕으로 다음 두 스키마의 컬럼을 정의합니다.

- permit parent schema
- permit status episode schema

사업체 단위 entity resolution이나 terminal survival label 생성은 Phase 4 범위에 포함하지 않습니다.

기계 판독 결정은 `provenance/grain_decision.json`에 있습니다.
