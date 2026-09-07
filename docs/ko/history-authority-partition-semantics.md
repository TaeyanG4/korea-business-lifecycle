# History Authority Partition Semantics

확인일: **2026-09-07**

2026-07-01 행정체제개편으로 공식 current reference에서 삭제된 `OPN_ATMY_GRP_CD`가 history API에서 어떻게 동작하는지 bounded probe와 전체 32-code count-only probe로 확인했습니다. count-level freeze는 전체 삭제-code domain에 대해 검증했지만 row-content freeze는 bounded full-row sample에만 적용합니다.

## 인증 상태

과거 `SERVICE_KEY_IS_NOT_REGISTERED_ERROR` 403 probe는 역사적 provenance로 유지합니다. 이후 동일 로컬 credential 경로를 사용하는 bounded authenticated probe가 정상 `resultCode=0`으로 성공했으므로 **현재 history 실행 자체는 가능**합니다. key 값은 어떤 provenance/log에도 기록하지 않습니다.

## Count-only bounded probe

삭제 코드 `3490000`(인천 계열), `3590000`(광주 계열), `4800000`(전남 계열)을 세 v1 source에서 네 날짜 `20260101`, `20260630`, `20260701`, `20260906`에 page-1 `numOfRows=1`로 조회했습니다.

9개 source/code pair 모두 다음 패턴을 보였습니다.

- 2026-01-01 → 2026-06-30: `totalCount` 증가
- 2026-06-30 = 2026-07-01 = 2026-09-06: 동일 `totalCount`
- 삭제 code는 개편 후에도 query 성공

따라서 `삭제 code → 개편 당일부터 0건`이라는 단순 모델은 기각합니다.

## Full-row local audit

row-level 값은 Git에 남기지 않고 Git-ignored local history snapshot에서 aggregate diff만 계산했습니다.

- `3490000 / bakeries`: 2026-06-30과 2026-09-06 모두 314행, 공통 MNG_NO 314, 추가/소실 0, status/detail/closure/permit/name/address/coordinates 변경 모두 0
- `4800000 / bakeries`: 양쪽 332행, 공통 MNG_NO 332, 추가/소실 0, 모든 비교 필드 변경 0
- current-code control `3491000 / bakeries`: 양쪽 217행이지만 status/detail/closure 1건과 coordinates 1건 변경

삭제 partition에는 9월 6일에도 source status `01` 행이 남아 있었습니다. 즉 frozen legacy partition이 단순 폐업 archive만으로 구성된다고 볼 수 없습니다.

## Old/new overlap bounded audit

2026-09-06 bakeries에서 삭제 `3490000` 314행과 current code `3491000`, `3501000`, `3561000`, `3565000`의 union 932행을 MNG_NO로 로컬 비교했습니다.

- overlap: 0
- deleted-only: 314
- current-union-only: 932
- current bulk snapshot의 네 current code 합계도 932이며 history 2026-09-06 count와 일치
- current bulk snapshot의 deleted `3490000`: 0행

이는 bounded sample에서 old/new partition이 단순 duplicate projection이 아님을 보여주지만, 전국 모든 old/new partition이 disjoint라는 증명은 아닙니다. MNG_NO를 source PK 또는 establishment identity로 승격하지 않습니다.

## 현재 해석

history authority filter는 단순한 **date-effective active-code domain**으로 모델링하면 안 됩니다. bounded evidence에서는 삭제 partition이 개편 전까지 진화하다가 이후 frozen legacy state로 계속 queryable하고, current partition은 이후에도 변화할 수 있습니다. 따라서 current 244 + deleted 32 = 276 후보 union은 비용 계획에는 사용할 수 있지만, 특정 날짜의 current-state snapshot과 의미적으로 동일하다고 주장하지 않습니다.

## Full 32-code count-only probe 완료

32개 삭제 코드 전체에 대해 3 source × 4 dates, 총 **384 requests**의 count-only probe를 완료했습니다.

- requests: 384/384
- unique task: 384
- complete four-date source/authority pair: 96/96
- `2026-06-30 = 2026-07-01 = 2026-09-06` count: 96/96 pair
- 2026-06-30 non-empty: 90 pair
- 2026-01-01 → 2026-06-30 count 증가: 81 pair
- 네 날짜 모두 0건: 6 pair, authority code `6290000`, `6460000`
- row-level 값 / service key: 기록하지 않음

로컬 결과 JSON SHA-256은 `3f8326fe2b82835ffda148b2bb1fda0049452e7719c67d58f439c9977e19ad7f`이며 Git에는 aggregate provenance만 추적합니다. 96/96 pair의 count 고정은 96개 pair의 row 내용까지 모두 동결됐다는 증명은 아닙니다.

offline 검증은 다음 명령으로 재현할 수 있습니다.

```bash
py -3.12 scripts/verify_deleted_authority_semantics.py \
  data/local/logs/deleted-authority-semantics-20260907.json
```

## Legacy partition inclusion policy

- **2026-07-01 이후:** current-state enumeration은 공식 current numeric **244개만 사용**하고 deleted 32는 제외합니다.
- **2026-07-01 이전:** current/new code도 이미 query 가능하므로 current 244와 deleted 32를 자동 union하지 않습니다.
- pre-reform old/new partition completeness/overlap가 해결되기 전에는 Jan–Sep 전국 enumeration domain을 승인하지 않습니다.
- 276-code union은 pre-reform 비용 계획용 candidate일 뿐 authoritative snapshot domain이 아닙니다.

## 다음 gate

다음 핵심 gate는 pre-reform old/new authority partition completeness/overlap semantics입니다. 이것이 해결된 뒤에만 observation cadence와 request budget을 최종 결정할 수 있습니다. 이미 완료한 full probe는 재실행할 필요가 없으며, 원 실행 명령은 재현성 목적으로만 아래에 보존합니다.

```bash
mkdir -p data/local/logs
py -3.12 scripts/probe_deleted_authority_semantics.py --execute --max-requests 384 --request-delay-seconds 0.2 \
  2> data/local/logs/deleted-authority-semantics-20260907.stderr.log \
  | tee data/local/logs/deleted-authority-semantics-20260907.json
```
