# Privacy-Minimized Public Permit Aggregate

확인일: **2026-09-08**

row-level `PERMIT`/WGS84 산출물은 공개하지 않고, 개인정보·연결 가능성을 줄인 **aggregate만 공개**합니다. 이 artifact는 기술적 privacy-minimization 검증을 완료했고, `provenance/v1_release_scope.json`의 별도 release decision에서 Kaggle/public 배포가 승인되었습니다.

## 입력

- verified parent build: `permit-v1-9908225df465e2ff`
- parent rows: 3,010,802
- parent independent verifier: PASS
- network access: 없음
- row-level public projection: 승인하지 않음

## 7컬럼 aggregate schema

`schemas/public_permit_aggregate.v1.json`은 다음 컬럼만 허용합니다.

- `source_key`
- `authority_code`
- `source_status_code`
- `source_detail_status_code`
- `permit_year`
- `closure_year`
- `cell_count`

`permit_date`와 `closure_date`의 exact date는 출력하지 않고 연도만 파생합니다. `permit_year`는 실제 개업연도로 해석하지 않고, `closure_year`도 irreversible terminal event를 의미하지 않습니다. status `03`/`05`에 canonical 의미를 새로 부여하지 않습니다.

## 명시적 제외

다음 계열의 row-level 정보는 aggregate output에 들어가지 않습니다.

- `management_number`, `source_row_number`, artifact/retrieval lineage
- business name
- lot/road address 및 postal code
- source X/Y, WGS84 longitude/latitude
- raw update timestamps
- telephone/homepage

## 셀 suppression

grouping key는 `source + authority + source status codes + permit year + closure year`입니다. 같은 key의 `cell_count`가 **10 미만이면 해당 셀 전체를 output에서 제외**합니다.

`k=10`은 이 프로젝트의 기술적 suppression threshold일 뿐이며 **법적·통계적 개인정보 안전을 보장한다고 주장하지 않습니다**. 기술 검증과 최종 release-scope 승인은 서로 별도로 기록합니다.

## Local build

현재 deterministic build ID는 `permit-public-agg-v1-bedd874de6619bee`입니다.

기본 모드는 plan-only입니다.

```bash
python scripts/materialize_public_permit_aggregate.py
```

장시간 실제 실행:

```bash
python scripts/materialize_public_permit_aggregate.py --execute
```

materializer는 verified parent의 3,010,802행을 전부 읽되 필요한 6개 input field만 사용합니다. 최종 candidate는 `data/local/public_candidate/permit_aggregate/v1/...` 아래에만 저장합니다.

## 독립 검증

```bash
python scripts/verify_public_permit_aggregate.py
```

verifier는 parent build를 다시 검증하고 aggregate manifest/hash/schema/ZSTD, `cell_count >= 10`, released/suppressed row accounting을 확인합니다.

## 현재 release 상태

- implementation + synthetic suppression/tamper tests: PASS
- real parent plan-only validation: PASS
- production aggregate scan: **PASS (3,010,802 rows)**
- cells before suppression: 297,195
- released candidate cells (`cell_count >= 10`): 67,267
- suppressed cells: 229,928
- source rows represented by released cells: 2,383,689
- source rows represented by suppressed cells: 627,113
- output: 108,019 bytes, independent verifier PASS
- technical minimization: VERIFIED
- row-level public release: BLOCKED
- aggregate publication: **APPROVED**
- Kaggle redistribution: **APPROVED FOR THIS VERIFIED AGGREGATE**
- Kaggle publication: **PUBLISHED / READY** — `taeyangg4/korea-food-service-permit-aggregate`
- row-level/precise-coordinate publication: BLOCKED
- release decision: `provenance/v1_release_scope.json`
- publication result: `provenance/kaggle_release.json`

기존 build manifest/schema 안의 candidate-time publication flag는 immutable build 당시의 gate를 기록합니다. 2026-09-08 최종 release decision이 이 **동일 hash의 검증된 aggregate artifact** 공개를 별도로 승인하며, row-level 공개 승인을 의미하지 않습니다.
