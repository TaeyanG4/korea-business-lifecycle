# Canonical PERMIT 실데이터 Bounded Compatibility

확인일: **2026-09-07**

synthetic fixture에서 검증한 `PERMIT` transformer를 Git-ignored `data/local/`의 실제 current snapshot에 처음 적용했습니다. 이 단계는 **호환성 확인만** 수행하며 production canonical dataset은 생성하지 않습니다.

## 범위

- 대상: `general_restaurants`, `rest_cafes`, `bakeries`
- 선택 규칙: 각 source의 최신 immutable retrieval manifest
- 샘플 규칙: CSV header 다음의 첫 256 data row
- 총 검증 행: 768
- row-level 값 출력/기록: 없음
- full snapshot scan: 수행하지 않음
- Parquet/ZSTD materialization: 수행하지 않음

## 결과

세 source 모두 `PASS`였습니다.

| source | rows | encoding | source → canonical columns | duplicate linkage |
| --- | ---: | --- | --- | ---: |
| general restaurants | 256 | CP949 | 39 → 26 | 0 |
| rest cafes | 256 | CP949 | 39 → 26 | 0 |
| bakeries | 256 | CP949 | 39 → 26 | 0 |

768행 모두 frozen transformer를 통과했습니다. bounded sample의 `permit_date_quality`는 모두 `VALID`였고, closure date는 `VALID` 485행 / `MISSING` 283행이었습니다. X/Y는 각각 68행에서 null이었으며 값 자체는 provenance에 기록하지 않습니다.

## 이 결과가 뜻하지 않는 것

첫 256행은 통계적으로 대표적인 sample이 아닙니다. 따라서 이번 `PASS`는 다음을 증명하지 않습니다.

- 전국 artifact 모든 행이 transformer를 통과한다는 보장
- full snapshot 전체에서 linkage candidate 중복이 없다는 새 증명
- 기존 profiling에서 확인된 invalid permit-date anomaly의 부재
- geospatial axis/CRS transform의 정당성
- production canonical dataset 생성 승인

특히 bounded sample에서 `INVALID` permit date가 없었다는 사실은 이전 full-snapshot profiling 결과를 대체하지 않습니다.

## 개인정보/공개 경계

검증 과정에서 관리번호, 사업장명, 주소, 전화번호, 좌표값을 Git provenance에 기록하지 않습니다. 결과 파일 `provenance/permit_parent_compatibility.json`에는 source key, artifact hash, 건수와 quality aggregate만 들어갑니다.

## 다음 gate

다음 한 단계는 **full-snapshot streaming dry-run validator**를 구현하는 것입니다. 전국 current snapshot 약 3백만 행을 읽을 수 있으므로 진행률을 표시하고, 장시간 로컬 실행은 사용자에게 정확한 명령어를 제공해 직접 실행하도록 합니다. 이 단계에서도 canonical output 파일은 쓰지 않습니다.
