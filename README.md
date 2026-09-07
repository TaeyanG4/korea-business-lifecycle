# 대한민국 사업체 영업 생애주기 데이터

[English](README.en.md)

대한민국 지방행정 인허가 데이터를 근거로 사업체/인허가 단위의 영업 생애주기를 재현 가능한 방식으로 연구하기 위한 공개 프로젝트입니다.

## 현재 실행 범위

첫 실행 마일스톤은 다음 세 항목으로 제한합니다.

1. 공개 GitHub 저장소와 Python 3.11/3.12 개발 기반 구축
2. 현재 지방행정 인허가 데이터 소스에 대한 재현 가능한 출처 조사
3. v1 대상인 **일반음식점, 휴게음식점, 제과점영업**의 기술·법적·개인정보·이력 수집 가능성 판정

아직 전국 원천데이터를 저장소에 포함하지 않으며, 전체 이력 수집·생애주기 재구성·Kaggle 공개를 수행하지 않습니다.

## 중요한 제약

- 현재 공식 인허가 데이터 후보군은 196이 아니라 **195종**으로 기록합니다.
- 소스의 기본키(PK)를 추정하지 않습니다.
- `인허가일자`를 실제 개업일로 자동 해석하지 않습니다.
- 폐업일자나 상태값의 의미를 검증 전에는 폐업 라벨로 사용하지 않습니다.
- EPSG:5174는 v1 공식 설명에서 확인됐고, 현재 v1 전체 snapshot QA는 `좌표정보(X)=easting`, `좌표정보(Y)=northing`을 지지합니다. 이 해석은 현재 승인된 artifact에 한정하며 미래 snapshot은 재검증합니다.
- 공공데이터의 공개 접근 가능성과 Kaggle 재배포 허가는 별개로 판정합니다.
- 실데이터는 저장소 내부의 Git-ignored 전용 경로 `data/local/`에서 다룹니다. 이 경로 아래의 raw/history/staging/processed/log 산출물은 Git에 포함되지 않습니다.

## 개발

```bash
python -m pip install -e ".[test]"
python -m compileall src scripts tests
pytest -v
```

테스트는 네트워크 접근을 차단하며 합성 fixture만 사용합니다.

## 현재 history 상태

current snapshot 취득/프로파일링과 5개 자치단체 bounded history audit이 완료되었습니다. `PERMIT` parent build `permit-v1-9908225df465e2ff`와 별도 WGS84 sidecar `permit-geo-v1-c4af8799de0283bb`는 모두 **3,010,802행** 기준 production materialization·독립 검증까지 완료했습니다. lifecycle semantic hard rules도 유지합니다: `03`은 irreversible terminal이 아니고 `05`는 unmapped입니다. publication-safety의 local aggregate 후보도 3,010,802행 전수 스캔·독립 검증을 완료했고, 297,195개 셀 중 k=10 이상 67,267개만 candidate에 남겼습니다. 이는 기술적 최소화 검증일 뿐 public/Kaggle 배포 승인이 아니며 redistribution review와 episode reconstruction은 계속 차단합니다.

## 문서

- [아키텍처](docs/ko/architecture.md)
- [v1 데이터 소스](docs/ko/data-sources.md)
- [데이터/개인정보 정책](docs/ko/data-policy.md)
- [재현성](docs/ko/reproducibility.md)
- [Bounded source profiling](docs/ko/profiling.md)
- [Bounded history audit 결과](docs/ko/bounded-history-findings.md)
- [03→01 전환 후속 probe](docs/ko/reverse-transition-probe.md)
- [v1 Grain 결정](docs/ko/grain-decision.md)
- [Canonical PERMIT parent schema](docs/ko/canonical-permit-schema.md)
- [Canonical PERMIT_STATUS_EPISODE schema](docs/ko/canonical-episode-schema.md)
- [Bounded PERMIT_STATUS_EPISODE reconstruction](docs/ko/bounded-episode-reconstruction.md)
- [Nationwide history observation strategy cost gate](docs/ko/history-observation-strategy.md)
- [Canonical PERMIT transformer](docs/ko/canonical-permit-transformer.md)
- [Canonical PERMIT bounded real-data compatibility](docs/ko/canonical-permit-compatibility.md)
- [Canonical PERMIT full-snapshot dry run](docs/ko/canonical-permit-full-dry-run.md)
- [Canonical PERMIT production materialization](docs/ko/canonical-permit-materialization.md)
- [Geospatial source X/Y axis QA](docs/ko/geospatial-axis-qa.md)
- [Canonical PERMIT WGS84 enrichment](docs/ko/canonical-permit-geospatial.md)
- [Privacy-minimized public aggregate candidate](docs/ko/public-permit-aggregate.md)
- [History 표본 확장 계획](docs/ko/history-sample-expansion.md)
- [5개 자치단체 History 표본 확장 결과](docs/ko/expanded-history-findings.md)
- [첫 실행 feasibility](docs/ko/first-milestone.md)

현재 제품별 gate 상태는 다음 aggregate-only 명령으로 확인할 수 있습니다.

```bash
python scripts/release_readiness.py
```

## 라이선스

프로젝트 코드 및 데이터 재배포 라이선스는 아직 확정하지 않았습니다. 2026-09-07 재검수에서 세 v1 행정안전부 OpenAPI 모두 `이용허락범위 제한 없음`을 확인해 source-use metadata gate는 PASS로 기록했습니다. 다만 공공데이터포털의 제3자 권리 정책에 대한 source-specific 확인이 남아 있으므로 raw mirror와 privacy-minimized aggregate의 외부/Kaggle 재배포는 계속 `UNRESOLVED`입니다.
