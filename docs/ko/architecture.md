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
      ↳ publication/redistribution: still blocked
  → bounded PERMIT_STATUS_EPISODE tooling
      ↳ sparse explicit observations only
      ↳ max 100,000 observations/call, in-memory
      ↳ LEFT / INTERVAL / RIGHT censoring preserved
      ↳ production nationwide reconstruction: acquisition 완료 전 disabled
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
      ↳ acquisition: 7,320 snapshot tasks, resumable, hard cap 400,000 requests/run, not executed
      ↳ episode materializer/verifier: prepared; all 7,320 snapshots complete/unique 전까지 blocked
  → redistribution clarification gate
      ↳ source-use metadata: PASS
      ↳ written source-specific questions/contact routes: prepared
      ↳ raw/aggregate external redistribution: unresolved
```

v1 parent와 WGS84 sidecar는 각각 3,010,802행 기준으로 production materialization과 독립 검증까지 완료했습니다. authority code-set은 공식 변경표를 기준으로 개편 전 `current-new+deleted` 244, 개편 후 current 244로 승인했습니다. 이는 API가 어느 code에 과거 `BASE_DATE` 응답을 반환하는지와 분리된 current-state membership 정책입니다. monthly 10-date cadence와 400,000-request fail-closed budget도 승인했지만 전국 acquisition 자체는 아직 실행하지 않았습니다. 수집 runner는 기존 complete snapshot을 재사용하며, 7,320 task가 모두 complete/unique일 때만 production episode materializer가 열립니다. redistribution은 source-use metadata PASS와 별개로 source-specific 서면 확인 전까지 외부 공개를 계속 차단합니다.

## 데이터 저장 원칙

실행용 데이터는 기본적으로 Git에서 제외되는 `data/local/` 아래에 저장합니다. `KBL_DATA_ROOT`로 위치를 바꿀 수 있지만, 저장소 내부 경로를 쓸 경우 반드시 `data/local/` 하위여야 합니다.
