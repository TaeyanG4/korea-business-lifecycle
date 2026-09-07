# 아키텍처

## 목적

원천 데이터와 의미 해석을 분리하고, 각 단계의 증거 gate를 통과한 정보만 다음 단계에서 사용합니다.

```text
공식 소스 증거
  → 외부 raw 저장소
  → staging/profile
  → grain/identity/lifecycle audit
  → canonical schema
  → geospatial normalization
  → deterministic Parquet/ZSTD build
  → 별도 공개 검토
```

현재 저장소는 첫 실행 마일스톤만 구현합니다. full-history ingestion, lifecycle reconstruction, Kaggle publication은 아직 구현하지 않습니다.

## 데이터 저장 원칙

`data/raw`, `data/staging`, `data/processed`, `data/logs`는 구조 표시용입니다. 실제 파일은 Git 바깥 `KBL_DATA_ROOT`에 저장해야 합니다.

