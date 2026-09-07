# Geospatial Source X/Y Axis QA

확인일: **2026-09-07**

공식 catalog는 세 v1 source 모두 source CRS를 `EPSG:5174`로 설명하지만, CSV의 `좌표정보(X)` / `좌표정보(Y)`가 EPSG formal axis label과 같은 방식으로 채워졌다고 자동으로 가정하지 않습니다. WGS84 latitude/longitude를 만들기 전에 실제 source field 배치를 별도로 검증합니다.

## CRS reference

`pyproj==3.7.2` / PROJ 9.5.1에서 `EPSG:5174`는 `Korean 1985 / Modified Central Belt`이며 formal axis는 다음과 같습니다.

- first axis: Northing, abbreviation `X`, north direction
- second axis: Easting, abbreviation `Y`, east direction

이 formal axis 정의와 upstream CSV field 이름 `좌표정보(X)` / `좌표정보(Y)`의 실제 값 배치는 **서로 다른 증거 문제**입니다.

## Bounded real-data probe

각 current snapshot에서 header 다음 첫 nonblank coordinate pair 5,000개를 검사했습니다. 총 15,000쌍입니다. row-level 좌표와 주소는 출력하거나 provenance에 저장하지 않았습니다.

두 candidate를 비교했습니다.

1. candidate A: source X를 easting, source Y를 northing으로 해석
2. candidate B: source X를 northing, source Y를 easting으로 해석

두 candidate 모두 15,000/15,000쌍이 매우 넓은 Korea WGS84 envelope 안에 들어왔기 때문에 단순 국가 범위 plausibility만으로는 축을 구분할 수 없었습니다.

다음으로 road/lot address의 시·도 prefix만 메모리에서 capital/gangwon/chungcheong/jeolla/gyeongsang/jeju 6개 거시권역으로 축약하고, 변환된 위치가 해당 거시권역의 넓은 envelope에 들어오는지만 aggregate로 비교했습니다.

| source | eligible pairs | X=easting/Y=northing match | swapped match |
| --- | ---: | ---: | ---: |
| general_restaurants | 5,000 | 5,000 | 0 |
| rest_cafes | 5,000 | 5,000 | 0 |
| bakeries | 5,000 | 5,000 | 0 |
| **total** | **15,000** | **15,000** | **0** |

따라서 bounded evidence는 세 source 모두 **`좌표정보(X)=easting`, `좌표정보(Y)=northing`을 강하게 선호**합니다.

## 아직 확정하지 않는 것

이번 sample은 각 source의 첫 5,000 nonblank pair이므로 전국 stratified evidence가 아닙니다. 거시권역 envelope도 authoritative geocoding이 아닌 QA heuristic입니다. 따라서 현재도 다음 값은 유지합니다.

- `coordinate_axis_order_verified_nationwide = false`
- `wgs84_generation_approved = false`
- frozen `PERMIT` parent의 source X/Y는 원 source float64 그대로 유지
- `wgs84_latitude` / `wgs84_longitude`는 생성하지 않음

## Full-snapshot validator

bounded result를 전국 전체에서 확인하기 위한 aggregate-only validator도 구현했습니다. 3,010,802행 전체를 읽고, prior profiling에서 관찰된 약 2,811,767 coordinate pair 전체에 같은 candidate comparison을 적용합니다. 시작 전에 approved raw artifact SHA-256을 실제 bytes에서 다시 계산합니다.

기본 모드는 plan-only입니다.

```bash
python scripts/validate_full_coordinate_axis.py
```

장시간 전체 실행은 다음 명령입니다.

```bash
mkdir -p data/local/logs
python scripts/validate_full_coordinate_axis.py --execute \
  | tee data/local/logs/geospatial-full-axis-20260907.json
```

진행률은 stderr, 최종 aggregate JSON은 stdout입니다. full scan이 통과해도 결과 검토 전에는 schema의 `coordinate_axis_order_validated`를 true로 바꾸거나 WGS84 row-level column을 만들지 않습니다.
