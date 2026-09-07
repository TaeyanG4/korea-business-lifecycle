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
      ↳ production build: completed/verified (3,010,802 rows)
  → privacy-minimized aggregate candidate
      ↳ direct/linkable row-level fields: excluded
      ↳ exact dates: year-only derivation
      ↳ minimum cell count: 10; smaller cells suppressed
      ↳ production scan: completed (3,010,802 rows)
      ↳ independent verifier: passed
      ↳ candidate cells: 67,267 released / 229,928 suppressed
      ↳ Kaggle aggregate publication: approved by final v1 release scope
      ↳ public serialization: same 67,267 cells as UTF-8 CSV + verified Parquet
      ↳ package metadata: source summary + release schema + data dictionary + manifest
  → approved canonical row-level Kaggle release
      ↳ PERMIT parent rows preserved: 3,010,802
      ↳ canonical columns preserved: 26
      ↳ public serialization: CSV + Parquet
      ↳ source EPSG:5174 coordinates included
      ↳ separately derived WGS84 sidecar excluded
  → bounded PERMIT_STATUS_EPISODE tooling
      ↳ sparse explicit observations only
      ↳ max 100,000 observations/call, in-memory
      ↳ LEFT / INTERVAL / RIGHT censoring preserved
      ↳ production nationwide reconstruction: optional advanced workflow
  → nationwide history observation cost gate
      ↳ pre-reform exact-244 current-scale planning: 30,109..30,838 requests/as-of date
      ↳ post-reform current-244-only planning: 30,151..30,838 requests/as-of date
      ↳ approved monthly 10-date scenario: 301,258..308,380 requests
      ↳ daily comparison scenario: 7,499,997..7,678,662 requests
      ↳ latest current numeric authority domain: exact 244 ingested/validated
      ↳ exact deleted numeric change-reference codes: 32; current+deleted candidate union: 276
      ↳ current observed authority count: 230; all are a subset of current 244
      ↳ bounded semantics: deleted partition freezes after reform; current partition can keep evolving
      ↳ full 32-code count-only probe: completed, 384/384 requests; post-reform count freeze 96/96 pairs
      ↳ post-reform policy: current 244 only, exclude deleted 32
      ↳ pre-reform policy: current 244 - new 32 + deleted 32 = exact 244
      ↳ same-date old/new union: 사용하지 않음
      ↳ approved cadence: MONTHLY_ANCHOR_PLUS_END, 10 dates, max gap 31 days
      ↳ optional acquisition reference: 7,320 snapshot tasks, resumable, hard cap 400,000 requests/run
      ↳ episode materializer/verifier: optional; 실행 시 all 7,320 snapshots complete/unique gate 유지
  → v1 release scope
      ↳ core v1: current PERMIT + local WGS84 sidecar, COMPLETE
      ↳ Kaggle/public: verified privacy-minimized aggregate + approved canonical row-level PERMIT
      ↳ source EPSG:5174 coordinates: canonical row release에 포함
      ↳ derived WGS84 sidecar: private
      ↳ written source-specific clarification: optional additional assurance
```

v1 parent와 WGS84 sidecar는 각각 3,010,802행 기준으로 production materialization과 독립 검증까지 완료했습니다. **2026-09-08부터 core v1은 이 current snapshot 제품으로 완료**하며, nationwide history/episode는 optional advanced workflow로 둡니다. Kaggle에는 기존 k=10 aggregate와 별도로 canonical `PERMIT` 3,010,802행 × 26컬럼을 CSV/Parquet으로 공개했습니다. Canonical source EPSG:5174 좌표는 row-level 공개본에 포함되지만 별도 파생 WGS84 sidecar는 공개하지 않습니다. 최종 범위는 `provenance/v1_release_scope.json`이 규정합니다.

## 데이터 저장 원칙

실행용 데이터는 기본적으로 Git에서 제외되는 `data/local/` 아래에 저장합니다. `KBL_DATA_ROOT`로 위치를 바꿀 수 있지만, 저장소 내부 경로를 쓸 경우 반드시 `data/local/` 하위여야 합니다.
