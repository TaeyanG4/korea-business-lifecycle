# 아키텍처

## 목적

원천 데이터와 의미 해석을 분리하고, 각 단계의 증거 gate를 통과한 정보만 다음 단계에서 사용합니다.

```text
공식 소스 증거
  → Git-ignored 로컬 raw 저장소 (`data/local/`)
  → staging/profile
  → grain/identity/lifecycle audit
  → canonical schema freeze
      ↳ PERMIT parent: frozen
      ↳ PERMIT_STATUS_EPISODE: frozen
  → deterministic PERMIT parent transformation
      ↳ synthetic 39-column fixture: validated
      ↳ bounded real-snapshot compatibility: passed (256 rows/source)
      ↳ full-snapshot streaming dry run: passed (3,010,802 rows)
  → local PERMIT Parquet/ZSTD materialization
      ↳ production build: completed (3,010,802 rows)
      ↳ independent verifier: passed
  → geospatial source-field QA
      ↳ bounded axis probe: X=easting/Y=northing strongly preferred
      ↳ full-snapshot aggregate validator: passed/reviewed (2,811,767 coordinate pairs)
      ↳ local WGS84 derivation: approved for exact current-v1 artifacts
      ↳ frozen PERMIT parent mutation: prohibited; use separate enrichment
  → PERMIT_GEOSPATIAL_ENRICHMENT
      ↳ 7-column schema: frozen
      ↳ builder + independent verifier: implemented/tested
      ↳ production execution: pending user run
  → 별도 공개 검토
```

v1 parent/lifecycle 계약은 동결됐고, current snapshot → `PERMIT` transformer와 production Parquet/ZSTD build가 모두 3,010,802행 기준으로 완료·검증됐습니다. full geospatial QA도 2,811,767 coordinate pair 전체를 검사해 source X=easting/Y=northing 해석을 현재 승인된 v1 artifact 범위에서 채택했습니다. 기존 frozen `PERMIT` schema hash와 parent build는 변경하지 않고, 별도 7컬럼 `PERMIT_GEOSPATIAL_ENRICHMENT` schema와 deterministic builder/verifier를 구현했습니다. production WGS84 sidecar 실행만 사용자 장시간 작업으로 남아 있으며 public release, episode reconstruction, Kaggle publication은 계속 차단 상태입니다.

## 데이터 저장 원칙

실행용 데이터는 기본적으로 Git에서 제외되는 `data/local/` 아래에 저장합니다. `KBL_DATA_ROOT`로 위치를 바꿀 수 있지만, 저장소 내부 경로를 쓸 경우 반드시 `data/local/` 하위여야 합니다.
