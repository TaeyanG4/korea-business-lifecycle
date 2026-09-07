# Canonical PERMIT Production Materialization

확인일: **2026-09-07**

3,010,802행 full-snapshot dry run이 통과한 뒤, 동일한 immutable source artifact만 입력으로 허용하는 **로컬 전용 production `PERMIT` Parquet/ZSTD materializer**를 구현했습니다. 이 단계는 canonical parent를 실제 파일로 만들기 위한 production build이지만, 공개 배포 승인을 의미하지 않습니다.

## 입력 gate

materializer는 `provenance/permit_parent_full_dry_run.json`에서 `PASS`가 확인된 다음 세 artifact만 허용합니다.

- `general_restaurants`: 2,295,369행
- `rest_cafes`: 645,952행
- `bakeries`: 69,481행
- 합계: 3,010,802행

build 시작 전에 retrieval manifest의 hash/bytes/retrieval id가 full-dry-run evidence와 일치하는지 확인하고, raw 파일의 SHA-256도 실제 bytes에서 다시 계산합니다. 하나라도 다르면 output을 쓰지 않고 fail-closed합니다.

full dry run에서 `source_key + management_number` 중복이 정확히 0건으로 검증됐으므로, production build은 **동일 SHA-256 artifact에 한해서만** 그 exact uniqueness proof를 재사용합니다. 이는 `MNG_NO`가 공식 PK라는 선언이 아닙니다.

## Writer contract

- `pyarrow==21.0.0`
- Parquet format version `2.6`
- ZSTD compression level `9`
- data page version `2.0`
- 50,000 rows per Arrow batch
- 50,000 rows per Parquet row group
- source별 Parquet 1개 + local `manifest.json` 1개

Arrow schema는 frozen 26컬럼 `PERMIT` schema와 이름/순서/nullability/type을 정확히 맞춥니다. `source_retrieved_at_utc`는 `timestamp[us, UTC]`, 날짜는 `date32`, source X/Y는 `float64`입니다.

## 출력 위치와 원자성

최종 출력은 Git-ignored 경로만 사용합니다.

```text
data/local/canonical/permit/v1/<build_id>/
  general_restaurants.parquet
  rest_cafes.parquet
  bakeries.parquet
  manifest.json
```

현재 입력과 writer contract에서 계산된 build ID는 `permit-v1-9908225df465e2ff`입니다.

build는 먼저 `data/local/.tmp/permit-materialization/<build_id>-<pid>/`에 쓰고 모든 source의 row count, Arrow schema, Parquet metadata, output SHA-256 검증이 끝난 뒤 final directory로 rename합니다. 처리된 실패에서는 staging directory를 삭제합니다. 동일 build ID의 final directory가 이미 존재하면 덮어쓰지 않습니다.

## 의미 보존

- permit-date parse 불가 4건은 null + `INVALID` quality로 유지합니다.
- status `03`을 terminal closure로 변환하지 않습니다.
- status `05` 의미를 매핑하지 않습니다.
- WGS84를 만들지 않습니다.
- episode reconstruction을 수행하지 않습니다.
- telephone/homepage 등 deferred source field는 canonical output에 포함하지 않습니다.

## 실행

기본 모드는 plan-only입니다.

```bash
python scripts/materialize_permit_parent.py
```

실제 production materialization은 장시간 로컬 작업이므로 사용자가 명시적으로 실행합니다.

```bash
mkdir -p data/local/logs
python scripts/materialize_permit_parent.py --execute \
  | tee data/local/logs/permit-materialization-20260907.json
```

hashing/write 진행률은 stderr에 표시되고, 최종 local manifest summary JSON만 stdout으로 출력됩니다.

## 공개 경계

생성되는 Parquet에는 사업장명, 주소, source 좌표 등 row-level 정보가 있으므로 **local private runtime artifact**입니다. public/Kaggle row-level allowlist와 redistribution gate가 통과하기 전에는 배포하지 않습니다.

## 현재 상태

코드, synthetic Parquet round-trip, schema/압축 검증, immutable-output 보호, hash mismatch 실패 원자성 테스트, 실제 artifact plan 검증까지 완료했습니다. 실제 3,010,802행 production materialization은 아직 실행하지 않았습니다.
