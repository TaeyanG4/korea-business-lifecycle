# Canonical PERMIT Transformer

확인일: **2026-09-07**

`PERMIT` parent schema 동결 다음 단계로, current snapshot source row를 frozen 26컬럼 `PERMIT` row로 바꾸는 **결정론적 변환 코어**를 구현했습니다. 이 milestone은 합성 fixture에서만 검증하며 전국 실데이터 materialization은 수행하지 않습니다.

## 입력 계약

한 입력 row는 이미 strict decoding이 끝난 source text mapping이며 frozen 39컬럼 inventory와 정확히 일치해야 합니다. 컬럼 누락/추가는 fail-closed입니다.

lineage context는 다음 세 값을 요구합니다.

- v1 `source_key`
- retrieval artifact의 lowercase 64자리 SHA-256
- timezone-aware retrieval UTC timestamp

기존 acquisition `retrieval.json`의 `source_key`, `artifact.sha256`, `request.completed.utc`에서 같은 context를 만들 수 있습니다.

## 변환 규칙

- 문자열은 앞뒤 공백만 제거하고 blank는 null로 만듭니다.
- authority code, management number, postal code는 문자열로 유지하여 leading zero를 보존합니다.
- `인허가일자`, `폐업일자`는 `YYYYMMDD`, `YYYY-MM-DD`, `YYYY/MM/DD`를 date로 파싱합니다.
  - blank: null + `MISSING`
  - parse 가능: date + `VALID`
  - nonblank parse 불가: null + `INVALID`
- X/Y는 nonblank 값만 finite float64로 파싱합니다. CRS 변환이나 범위 보정은 하지 않습니다.
- status code/name 4필드는 원문 의미를 유지하며 canonical active/closed 상태로 변환하지 않습니다.
- `전화번호`, `홈페이지`를 포함한 deferred source column은 canonical output으로 전달하지 않습니다.

## Fail-closed identity invariant

한 current snapshot batch 안에서 `source_key + management_number`가 중복되면 변환 전체가 실패합니다. 이는 frozen schema의 expected uniqueness candidate 검증이며 source PK 선언이 아닙니다. 오류 메시지에는 실제 management number를 넣지 않습니다.

## 의도적으로 하지 않는 것

- `establishment_id` 생성
- `03`을 terminal closure로 변환
- `05` 의미 매핑
- WGS84 생성
- 전국 raw artifact 읽기/쓰기
- Parquet/ZSTD materialization
- episode reconstruction

현재 함수는 synthetic/bounded in-memory validation용입니다. production streaming writer라고 주장하지 않습니다.

## 다음 gate

다음 한 단계는 Git-ignored `data/local/`의 실제 current snapshot을 대상으로 **row-level 값을 출력하지 않는 bounded compatibility validation**을 추가하는 것입니다. 이 gate에서도 production canonical dataset을 아직 쓰지 않습니다.
