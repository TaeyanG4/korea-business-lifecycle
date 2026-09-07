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
      ↳ builder: implemented/tested
      ↳ production execution: pending user run
  → geospatial source-field QA
      ↳ bounded axis probe: X=easting/Y=northing strongly preferred
      ↳ full-snapshot aggregate validator: implemented / user execution pending
      ↳ WGS84 generation: blocked
  → 별도 공개 검토
```

v1 grain과 두 canonical schema 계약은 동결됐고, current snapshot → `PERMIT` transformer는 synthetic, source별 256행 bounded compatibility, 전체 3,010,802행 full dry run을 모두 통과했습니다. 동일 SHA-256 input에만 허용되는 local-only production Parquet/ZSTD builder도 구현·테스트했습니다. geospatial bounded QA는 source X=easting/Y=northing을 강하게 지지하며 전수 validator도 구현됐지만 아직 미실행이므로 schema의 axis 검증 flag와 WGS84 generation은 계속 비활성화합니다. production materialization, full geospatial scan은 사용자 장시간 실행 대기 상태이며 public release, episode reconstruction, Kaggle publication은 차단 상태입니다.

## 데이터 저장 원칙

실행용 데이터는 기본적으로 Git에서 제외되는 `data/local/` 아래에 저장합니다. `KBL_DATA_ROOT`로 위치를 바꿀 수 있지만, 저장소 내부 경로를 쓸 경우 반드시 `data/local/` 하위여야 합니다.
