from __future__ import annotations

from typing import Any

from .config import load_json
from .provenance import V1_SOURCE_KEYS


FROZEN_V1_SOURCE_COLUMNS = {
    "개방자치단체코드",
    "관리번호",
    "인허가일자",
    "영업상태명",
    "폐업일자",
    "소재지면적",
    "소재지우편번호",
    "도로명우편번호",
    "사업장명",
    "업태구분명",
    "데이터갱신구분",
    "건물소유구분명",
    "공장사무직직원수",
    "공장생산직직원수",
    "공장판매직직원수",
    "급수시설구분명",
    "남성종사자수",
    "다중이용업소여부",
    "데이터갱신시점",
    "도로명주소",
    "등급구분명",
    "보증액",
    "본사직원수",
    "상세영업상태명",
    "상세영업상태코드",
    "시설총규모",
    "여성종사자수",
    "영업상태코드",
    "영업장주변구분명",
    "월세액",
    "위생업태명",
    "전통업소주된음식",
    "전통업소지정번호",
    "전화번호",
    "좌표정보(X)",
    "좌표정보(Y)",
    "지번주소",
    "홈페이지",
    "최종수정시점",
}

REQUIRED_CANONICAL_COLUMNS = {
    "source_key",
    "source_row_number",
    "source_artifact_sha256",
    "source_retrieved_at_utc",
    "authority_code",
    "management_number",
    "permit_date",
    "permit_date_quality",
    "source_status_code",
    "source_status_name",
    "source_detail_status_code",
    "source_detail_status_name",
    "closure_date",
    "closure_date_quality",
    "business_name",
    "business_type_name",
    "hygiene_business_type_name",
    "lot_postal_code",
    "road_postal_code",
    "lot_address",
    "road_address",
    "source_coordinate_x",
    "source_coordinate_y",
    "source_data_update_type",
    "source_data_updated_at_raw",
    "source_last_modified_at_raw",
}

FORBIDDEN_CANONICAL_COLUMNS = {
    "establishment_id",
    "canonical_active_flag",
    "canonical_closed_flag",
    "terminal_event_flag",
    "physical_open_date",
    "wgs84_latitude",
    "wgs84_longitude",
}


def load_permit_parent_schema() -> dict[str, Any]:
    return load_json("schemas/permit_parent.v1.json")


def validate_permit_parent_schema(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if schema.get("schema_name") != "permit_parent" or schema.get("schema_version") != 1:
        errors.append("permit parent schema identity/version changed")
    if schema.get("grain") != "PERMIT":
        errors.append("permit parent schema grain must remain PERMIT")

    scope = schema.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("permit parent schema source scope must exactly match v1")
    if scope.get("history_rows_used_to_materialize_parent") is not False:
        errors.append("history rows must not materialize permit parent rows in this milestone")
    if scope.get("establishment_identity_claim") is not False:
        errors.append("permit parent schema must not claim establishment identity")
    if scope.get("source_primary_key_claim") is not False:
        errors.append("permit parent schema must not claim a source primary key")

    columns = schema.get("columns", [])
    names = [item.get("name") for item in columns]
    name_set = set(names)
    if len(columns) != 26 or len(name_set) != 26:
        errors.append("permit parent schema must contain 26 uniquely named columns")
    if name_set != REQUIRED_CANONICAL_COLUMNS:
        missing = sorted(REQUIRED_CANONICAL_COLUMNS - name_set)
        extra = sorted(name_set - REQUIRED_CANONICAL_COLUMNS)
        errors.append(f"permit parent canonical columns changed; missing={missing}, extra={extra}")
    if name_set & FORBIDDEN_CANONICAL_COLUMNS:
        errors.append("permit parent schema contains a forbidden derived semantic field")

    by_name = {item.get("name"): item for item in columns}
    management = by_name.get("management_number", {})
    if management.get("source_column") != "관리번호" or management.get("nullable") is not False:
        errors.append("management_number mapping/nullability changed")
    authority = by_name.get("authority_code", {})
    if authority.get("source_column") != "개방자치단체코드" or authority.get("logical_type") != "string":
        errors.append("authority_code must remain a string mapped from 개방자치단체코드")

    expected_quality = ["VALID", "MISSING", "INVALID"]
    for name in ("permit_date_quality", "closure_date_quality"):
        item = by_name.get(name, {})
        if item.get("nullable") is not False or item.get("allowed_values") != expected_quality:
            errors.append(f"{name} quality contract changed")

    for name in ("source_coordinate_x", "source_coordinate_y"):
        if by_name.get(name, {}).get("logical_type") != "float64":
            errors.append(f"{name} must remain float64 source coordinates")
    for name in ("source_data_updated_at_raw", "source_last_modified_at_raw"):
        if by_name.get(name, {}).get("logical_type") != "string":
            errors.append(f"{name} must remain raw string until timezone semantics are resolved")

    inventory = set(schema.get("source_column_inventory", []))
    if inventory != FROZEN_V1_SOURCE_COLUMNS or len(schema.get("source_column_inventory", [])) != 39:
        errors.append("frozen v1 39-column source inventory changed")

    mapped = {item.get("source_column") for item in columns if item.get("source_column")}
    deferred_items = schema.get("deferred_source_columns", [])
    deferred = {item.get("source_column") for item in deferred_items}
    if len(mapped) != 20:
        errors.append(f"expected 20 directly mapped source columns, found {len(mapped)}")
    if len(deferred) != 19 or len(deferred_items) != 19:
        errors.append("expected exactly 19 uniquely deferred source columns")
    if mapped & deferred:
        errors.append("source columns cannot be both mapped and deferred")
    if mapped | deferred != FROZEN_V1_SOURCE_COLUMNS:
        errors.append("mapped and deferred source columns must fully partition the 39-column inventory")

    if "전화번호" not in deferred or "홈페이지" not in deferred:
        errors.append("telephone and homepage must remain deferred from the v1 permit parent")

    policy = schema.get("build_policy", {})
    if policy.get("expected_unique_candidate") != ["source_key", "management_number"]:
        errors.append("expected technical uniqueness candidate changed")
    if policy.get("expected_unique_candidate_is_primary_key_claim") is not False:
        errors.append("technical uniqueness candidate must not become a primary-key claim")
    if policy.get("on_candidate_duplicate") != "FAIL_CLOSED_AND_REVIEW_GRAIN":
        errors.append("candidate duplicate policy must fail closed")
    if policy.get("publication_policy") != "NOT_APPROVED_FOR_PUBLIC_ROW_LEVEL_BUILD":
        errors.append("permit parent publication must remain blocked")

    metadata = schema.get("metadata", {})
    if metadata.get("declared_source_crs") != "EPSG:5174":
        errors.append("declared source CRS evidence changed")
    if metadata.get("coordinate_axis_order_validated") is not False:
        errors.append("coordinate axis order must remain unvalidated until geospatial QA")

    explicit_absent = set(schema.get("explicitly_absent_fields", []))
    if explicit_absent != FORBIDDEN_CANONICAL_COLUMNS:
        errors.append("explicitly absent semantic/geospatial fields changed")

    return errors
