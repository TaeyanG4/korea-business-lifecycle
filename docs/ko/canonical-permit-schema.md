# Canonical PERMIT Parent Schema

확인일: **2026-09-07**

Phase 4의 첫 단계로 `PERMIT` parent schema를 동결합니다. 아직 Parquet 빌드나 `PERMIT_STATUS_EPISODE` 생성은 하지 않습니다.

## 행의 의미

한 행은 **선택된 current snapshot에 존재하는 하나의 source permit record**입니다. 사업장명·주소·좌표 유사성으로 서로 다른 permit을 병합하지 않습니다.

`management_number`는 bounded history에서 continuity가 강했던 연결 후보이지만 공식 PK로 선언하지 않습니다. 빌드 시 `(source_key, management_number)` 기대 uniqueness가 깨지면 중복 제거하지 않고 즉시 실패하여 grain을 재검토합니다.

## 26개 canonical 컬럼

### Lineage / technical

- `source_key`: v1 source key
- `source_row_number`: CSV header 다음 1-based data row 번호
- `source_artifact_sha256`: 원본 artifact SHA-256
- `source_retrieved_at_utc`: retrieval manifest UTC 시각

### Permit / lifecycle source attributes

- `authority_code` ← `개방자치단체코드`
- `management_number` ← `관리번호`
- `permit_date` + `permit_date_quality` ← `인허가일자`
- `source_status_code` / `source_status_name`
- `source_detail_status_code` / `source_detail_status_name`
- `closure_date` + `closure_date_quality` ← `폐업일자`

`permit_date_quality`와 `closure_date_quality`는 `VALID | MISSING | INVALID`입니다. 비어 있지 않지만 파싱할 수 없는 날짜는 버리거나 임의 보정하지 않고 canonical date를 null로 두고 `INVALID`를 기록합니다. 원문은 raw/staging에 남습니다.

### Business context

- `business_name`
- `business_type_name`
- `hygiene_business_type_name`

### Location

- `lot_postal_code`, `road_postal_code`
- `lot_address`, `road_address`
- `source_coordinate_x`, `source_coordinate_y`

좌표는 `float64`로만 파싱하며 아직 WGS84로 변환하지 않습니다. 공식 catalog의 `EPSG:5174`는 metadata로 기록하지만 X/Y 축 의미와 변환 QA가 끝날 때까지 latitude/longitude를 만들지 않습니다.

### Source update lineage

- `source_data_update_type`
- `source_data_updated_at_raw`
- `source_last_modified_at_raw`

두 시각 필드는 timezone 의미가 문서화되지 않았으므로 이번 schema에서는 문자열 원형을 유지합니다.

## Source 39컬럼 처리

39개 공통 source 컬럼을 전부 inventory로 고정했습니다. 그중 20개는 위 canonical 컬럼에 직접 매핑되고 19개는 raw/staging에 보존하되 parent canonical에서 제외합니다.

제외 대상에는 직원수·보증액·월세액·시설 관련 희소 속성, 특수 전통업소 속성, 전화번호·홈페이지가 포함됩니다. 이는 원천에서 삭제한다는 뜻이 아니라 **PERMIT parent의 핵심 의미에 넣지 않는다는 뜻**입니다.

## 명시적으로 만들지 않는 필드

- `establishment_id`
- canonical active/closed flag
- terminal event flag
- physical open date
- WGS84 latitude/longitude

특히 `03→01` source-state reversal이 확인됐으므로 parent table에서 `03`이나 폐업일자를 terminal survival label로 변환하지 않습니다.

## Publication

이 schema는 내부 canonical processing 계약입니다. row-level public allowlist와 Kaggle redistribution gate는 여전히 승인되지 않았으므로 canonical 컬럼 정의가 공개 허가를 의미하지 않습니다.

기계 판독 schema는 `schemas/permit_parent.v1.json`에 있습니다.
