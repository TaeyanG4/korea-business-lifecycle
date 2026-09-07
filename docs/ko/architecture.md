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
      ↳ PERMIT_STATUS_EPISODE: next gate
  → geospatial normalization
  → deterministic Parquet/ZSTD build
  → 별도 공개 검토
```

v1 grain은 canonical `PERMIT` parent + derived `PERMIT_STATUS_EPISODE`로 고정했고 `PERMIT` parent schema까지 동결했습니다. episode schema, full-history ingestion, production episode reconstruction, Kaggle publication은 아직 구현하지 않습니다.

## 데이터 저장 원칙

실행용 데이터는 기본적으로 Git에서 제외되는 `data/local/` 아래에 저장합니다. `KBL_DATA_ROOT`로 위치를 바꿀 수 있지만, 저장소 내부 경로를 쓸 경우 반드시 `data/local/` 하위여야 합니다.
