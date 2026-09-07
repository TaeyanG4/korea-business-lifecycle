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
      ↳ production nationwide reconstruction: disabled
  → nationwide history observation cost gate
      ↳ current-scale 276-code candidate-union planning: 30,247..30,934 requests/as-of date
      ↳ daily 249-date scenario: 7,531,503..7,702,566 requests
      ↳ latest current numeric authority domain: exact 244 ingested/validated
      ↳ exact deleted numeric change-reference codes: 32; current+deleted candidate union: 276
      ↳ current observed authority count: 230; all are a subset of current 244
      ↳ deleted-code date-effective history filter semantics: unresolved
      ↳ approved cadence: none
  → redistribution clarification gate
      ↳ source-use metadata: PASS
      ↳ written source-specific questions/contact routes: prepared
      ↳ raw/aggregate external redistribution: unresolved
```

v1 parent와 WGS84 sidecar는 각각 3,010,802행 기준으로 production materialization과 독립 검증까지 완료했습니다. publication-safety 단계의 local aggregate 후보도 3,010,802행 전수 스캔과 독립 검증까지 완료됐습니다. 추가로 bounded sparse-observation episode reconstructor와 network-free nationwide history cost model을 구현했습니다. authority domain은 최신 7월 공식 첨부에서 현재 244개 숫자 코드와 삭제 32개 숫자 코드를 exact ingestion/hash/validation했습니다. 다만 Jan–Sep history에서 삭제 코드가 pre-change `BASE_DATE`에 어떤 filter 의미를 갖는지는 공식 문서/실행으로 아직 확인되지 않아 production enumeration은 계속 차단합니다. redistribution도 source-use metadata는 PASS이나 source-specific 서면 확인 전에는 외부 공개를 계속 차단합니다.

## 데이터 저장 원칙

실행용 데이터는 기본적으로 Git에서 제외되는 `data/local/` 아래에 저장합니다. `KBL_DATA_ROOT`로 위치를 바꿀 수 있지만, 저장소 내부 경로를 쓸 경우 반드시 `data/local/` 하위여야 합니다.
