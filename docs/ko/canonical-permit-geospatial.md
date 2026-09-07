# Canonical PERMIT Geospatial Enrichment

확인일: **2026-09-07**

검증된 immutable `PERMIT` parent를 변경하지 않고 WGS84 좌표를 제공하기 위한 **별도 1:1 sidecar**를 구현했습니다. 이 산출물은 local private runtime data이며 public/Kaggle 배포 승인을 의미하지 않습니다.

## Parent gate

- parent build: `permit-v1-9908225df465e2ff`
- parent rows: 3,010,802
- parent independent verifier: PASS
- parent schema: frozen 26 columns, 변경하지 않음
- axis evidence: `provenance/geospatial_full_axis.json`
- source X: easting
- source Y: northing
- source CRS: `EPSG:5174`
- target CRS: `EPSG:4326`

full geospatial QA는 2,811,767 coordinate pair 전체를 검사했습니다. 주소 거시권역 평가 가능 2,631,605건 중 X=easting/Y=northing 후보가 2,630,497건(99.958%) 일치했고 반대 후보만 단독으로 맞은 사례는 0건이었습니다. 이 승인은 **현재 SHA-256으로 고정된 v1 artifact 집합에만** 적용하며 future snapshot은 재검증합니다.

## Sidecar grain/schema

`schemas/permit_geospatial.v1.json`은 `PERMIT_GEOSPATIAL_ENRICHMENT` grain의 7컬럼 schema입니다.

- `source_key`
- `source_row_number`
- `management_number`
- `parent_permit_build_id`
- `wgs84_longitude`
- `wgs84_latitude`
- `coordinate_quality`

`source_key + source_row_number + management_number`는 parent row와의 lineage linkage입니다. 이를 공식 PK라고 선언하지 않으며 `management_number`도 계속 bounded continuity/expected uniqueness candidate일 뿐입니다.

`coordinate_quality`는 `TRANSFORMED` 또는 `MISSING_SOURCE_COORDINATES`만 허용합니다. source X/Y가 모두 비어 있으면 longitude/latitude를 둘 다 null로 기록합니다.

## Fail-closed 규칙

materializer는 쓰기 전에 기존 `PERMIT` build를 독립 verifier로 다시 검증합니다. 이후 다음 조건을 강제합니다.

- parent `source_row_number`가 1부터 정확히 연속적이어야 함
- parent `management_number`가 null/blank이면 실패
- source X/Y 중 하나만 존재하면 실패
- EPSG:5174 → EPSG:4326 변환 오류/비유한 결과면 실패
- 결과가 broad Korea envelope(lon 124..132, lat 32..40)를 벗어나면 실패
- reviewed QA의 source별 transformed/missing count와 다르면 실패
- 기존 deterministic final directory가 있으면 overwrite하지 않고 실패
- handled failure에서는 staging directory 제거

## Production plan

deterministic build ID는 **`permit-geo-v1-c4af8799de0283bb`**입니다.

- 전체 sidecar rows: 3,010,802
- `TRANSFORMED`: 2,811,767
- `MISSING_SOURCE_COORDINATES`: 199,035
- output: `data/local/canonical/permit_geospatial/v1/permit-geo-v1-c4af8799de0283bb/`
- format: Parquet 2.6
- compression: ZSTD level 9
- batch/row group: 50,000 rows
- `pyarrow==21.0.0`
- `pyproj==3.7.2`, PROJ 9.5.1

`--execute`가 없으면 plan만 출력합니다.

```bash
python scripts/materialize_permit_geospatial.py
```

장시간 실제 실행:

```bash
python scripts/materialize_permit_geospatial.py --execute
```

## 독립 검증

materialization 후 반드시 별도 verifier를 실행합니다.

```bash
python scripts/verify_permit_geospatial_build.py
```

verifier는 parent build를 다시 검증하고, WGS84 sidecar의 manifest, file hash, Arrow schema, ZSTD, row count, linkage 순서, coordinate quality, null/finite/range invariant를 전체 row에 대해 다시 확인합니다.

## 공개 경계

WGS84는 precise coordinate이므로 `privacy_review.json`의 public allowlist가 승인되고 redistribution gate가 별도로 통과하기 전에는 공개하지 않습니다. 이 sidecar를 만드는 것은 public row-level release, status semantics, lifecycle episode reconstruction을 승인하지 않습니다.

실제 3,010,802행 sidecar materialization과 독립 검증까지 완료됐습니다. build ID는 `permit-geo-v1-c4af8799de0283bb`이고 총 Parquet 용량은 50,805,782 bytes입니다. 2,811,767행은 `TRANSFORMED`, 199,035행은 `MISSING_SOURCE_COORDINATES`이며 parent 재검증, manifest/hash/schema/ZSTD, 전체 coordinate invariant 검사가 모두 PASS했습니다. 이 완료 상태도 public row-level release 승인을 의미하지 않습니다.
