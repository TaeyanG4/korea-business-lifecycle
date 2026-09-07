# 대한민국 지방행정 식품 인허가 데이터

[English](README.en.md)

행정안전부 지방행정 인허가정보를 재현 가능한 방식으로 정리하는 공개 프로젝트입니다. 저장소 이름은 `korea-business-lifecycle`을 유지하지만, **v1의 핵심 데이터 제품은 전국 current permit snapshot**입니다. 전국 history 수집과 `PERMIT_STATUS_EPISODE` 재구성은 분석 목적에 따라 선택하는 **optional advanced workflow**입니다.

## v1 상태

**LOCAL V1 CORE: COMPLETE**

- 대상: 일반음식점, 휴게음식점, 제과점영업
- Canonical `PERMIT`: **3,010,802행**, production materialization 및 독립 검증 완료
- WGS84 sidecar: **3,010,802행**, 2,811,767건 좌표 변환, 독립 검증 완료
- 공개 후보 aggregate: **67,267 cells**, k=10 suppression 적용, 독립 검증 완료
- 전국 history/episode: **v1 완료조건이 아님**. runner, schema, verifier는 optional 분석 도구로 유지

실데이터와 derived runtime artifact는 모두 Git-ignored `data/local/` 아래에만 저장합니다.

## 공개 범위

Kaggle/public v1은 **privacy-minimized aggregate만** 공개 대상으로 합니다.

공개하지 않는 항목:

- row-level `PERMIT`
- 사업장명, 정확한 주소, 관리번호, 전화번호 등 직접/연결 가능 필드
- 정밀 source 좌표 및 WGS84 좌표
- 일부만 수집된 history snapshot

공개 aggregate는 `source_key`, 자치단체 코드, 원천 상태코드/상세상태코드, 인허가연도, 폐업연도 단위로 집계하며 cell count가 10 미만인 셀을 제외합니다. **k=10은 기술적 최소화 기준일 뿐 법적 개인정보 안전을 보장하지 않습니다.**

## 소스와 이용조건

2026-09-08 재확인 기준 공공데이터포털의 세 공식 OpenAPI 상세페이지는 모두 `이용허락범위 제한 없음`을 표시합니다. v1은 이 공식 metadata를 공개 근거로 사용하고, 출처를 명시한 privacy-minimized aggregate만 Kaggle에 배포합니다. 별도 서면 문의는 추가 assurance를 위한 선택사항으로 남깁니다.

- 15154916 — 행정안전부_식품_일반음식점 조회서비스
- 15154921 — 행정안전부_식품_휴게음식점 조회서비스
- 15155252 — 행정안전부_식품_제과점영업 조회서비스

최종 기계 판독 release 결정은 `provenance/v1_release_scope.json`에 있습니다.

## Lifecycle 사용 시 주의사항

현재 snapshot만으로 실제 사업체 생애주기를 단정하지 않습니다.

- `MNG_NO`는 공식 PK/사업체 identity라고 선언하지 않습니다.
- `인허가일자`는 실제 물리적 개업일로 해석하지 않습니다.
- `폐업일자`는 영구 terminal event라고 가정하지 않습니다.
- 실제 `03→01` reversal 2건이 확인되어 `03`은 irreversible terminal이 아닙니다.
- 상태코드 `05` 의미는 unresolved입니다.
- history는 as-of snapshot 서비스이며 lossless event log가 아닙니다.
- optional episode를 만들 경우 sparse transition은 interval-censored, 마지막 episode는 right-censored로 유지합니다.

## Optional history workflow

전국 history가 필요한 분석가는 준비된 monthly reference cadence와 runner를 사용할 수 있습니다. 기준 cadence는 10개 날짜 × 3 sources × date-effective 244 authority codes = 7,320 snapshot tasks입니다. 이 수집은 **core v1 또는 Kaggle aggregate 공개에 필요하지 않습니다.**

관련 문서:

- [v1 Grain 결정](docs/ko/grain-decision.md)
- [History observation strategy](docs/ko/history-observation-strategy.md)
- [Authority domain reference](docs/ko/authority-domain-reference.md)
- [Architecture](docs/ko/architecture.md)
- [Public aggregate](docs/ko/public-permit-aggregate.md)
- [Redistribution clarification](docs/ko/redistribution-clarification.md)

## 개발 및 검증

```bash
python -m pip install -e ".[test]"
python -m compileall src scripts tests
pytest -v
python scripts/release_readiness.py
```

테스트는 기본적으로 네트워크 접근을 차단하고 synthetic fixture만 사용합니다. `tests/fixtures/`의 약 4KB fixture는 실제 공개 데이터가 아니라 canonical transformer와 verifier를 재현 가능하게 검증하기 위한 최소 테스트 자료입니다.

## 저장소 데이터 정책

- 실제 source rows, credentials, runtime logs, partial history, canonical Parquet, Kaggle staging은 `data/local/`에만 둡니다.
- `.env`와 Kaggle/API credentials는 Git에 포함하지 않습니다.
- `schemas/`와 aggregate-only provenance만 Git으로 관리합니다.
- 과거 보수적 gate/probe provenance는 감사 추적을 위해 유지하며, 최신 제품 범위는 `v1_release_scope.json`이 우선합니다.