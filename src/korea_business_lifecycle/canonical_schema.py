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

REQUIRED_GEOSPATIAL_COLUMNS = {
    "source_key",
    "source_row_number",
    "management_number",
    "parent_permit_build_id",
    "wgs84_longitude",
    "wgs84_latitude",
    "coordinate_quality",
}

GEOSPATIAL_QUALITY_VALUES = ["TRANSFORMED", "MISSING_SOURCE_COORDINATES"]

REQUIRED_PUBLIC_AGGREGATE_COLUMNS = {
    "source_key",
    "authority_code",
    "source_status_code",
    "source_detail_status_code",
    "permit_year",
    "closure_year",
    "cell_count",
}

PUBLIC_AGGREGATE_GROUPING_COLUMNS = [
    "source_key",
    "authority_code",
    "source_status_code",
    "source_detail_status_code",
    "permit_year",
    "closure_year",
]

REQUIRED_EPISODE_COLUMNS = {
    "source_key",
    "management_number",
    "episode_number",
    "observation_window_start_date",
    "observation_window_end_date",
    "first_observed_date",
    "last_observed_date",
    "observation_count",
    "source_status_code",
    "source_status_name",
    "source_detail_status_code",
    "source_detail_status_name",
    "start_boundary_lower_date",
    "start_boundary_upper_date",
    "start_censoring",
    "end_boundary_lower_date",
    "end_boundary_upper_date",
    "end_censoring",
    "right_censored",
    "source_closure_date_first_observed",
    "source_closure_date_first_quality",
    "source_closure_date_last_observed",
    "source_closure_date_last_quality",
}

FORBIDDEN_EPISODE_COLUMNS = {
    "establishment_id",
    "episode_id",
    "canonical_active_flag",
    "canonical_closed_flag",
    "terminal_event_flag",
    "event_date",
    "exact_open_date",
    "exact_close_date",
    "reopened_flag",
    "duration_days",
}

EPISODE_STATE_PARTITION_FIELDS = [
    "source_status_code",
    "source_status_name",
    "source_detail_status_code",
    "source_detail_status_name",
]

EPISODE_ROW_INVARIANTS = {
    "observation_window_start_date <= first_observed_date <= last_observed_date <= observation_window_end_date",
    "start_boundary_upper_date == first_observed_date",
    "end_boundary_lower_date == last_observed_date",
    "LEFT_CENSORED implies start_boundary_lower_date is null",
    "INTERVAL_CENSORED start implies start_boundary_lower_date < start_boundary_upper_date",
    "RIGHT_CENSORED implies end_boundary_upper_date is null and right_censored is true",
    "INTERVAL_CENSORED end implies end_boundary_upper_date is non-null, end_boundary_lower_date < end_boundary_upper_date, and right_censored is false",
    "episode_number is unique only within source_key + management_number + observation window",
}


def load_permit_parent_schema() -> dict[str, Any]:
    return load_json("schemas/permit_parent.v1.json")


def load_permit_status_episode_schema() -> dict[str, Any]:
    return load_json("schemas/permit_status_episode.v1.json")


def load_permit_geospatial_schema() -> dict[str, Any]:
    return load_json("schemas/permit_geospatial.v1.json")


def load_public_permit_aggregate_schema() -> dict[str, Any]:
    return load_json("schemas/public_permit_aggregate.v1.json")


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


def validate_permit_geospatial_schema(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("schema_name") != "permit_geospatial" or schema.get("schema_version") != 1:
        errors.append("permit geospatial schema identity/version changed")
    if schema.get("grain") != "PERMIT_GEOSPATIAL_ENRICHMENT":
        errors.append("permit geospatial grain changed")

    scope = schema.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("permit geospatial scope must exactly match v1 sources")
    if scope.get("parent_schema") != "schemas/permit_parent.v1.json":
        errors.append("permit geospatial parent schema reference changed")
    if scope.get("parent_build_id") != "permit-v1-9908225df465e2ff":
        errors.append("permit geospatial parent build id changed")
    if scope.get("parent_rows") != 3_010_802:
        errors.append("permit geospatial parent row count changed")
    for key in ("parent_mutated", "establishment_identity_claim", "source_primary_key_claim", "public_row_level_release_approved"):
        if scope.get(key) is not False:
            errors.append(f"permit geospatial scope must keep {key}=false")

    policy = schema.get("derivation_policy", {})
    if policy.get("axis_evidence") != "provenance/geospatial_full_axis.json":
        errors.append("permit geospatial axis evidence reference changed")
    if policy.get("source_crs") != "EPSG:5174" or policy.get("target_crs") != "EPSG:4326":
        errors.append("permit geospatial CRS contract changed")
    if policy.get("source_x_interpretation") != "EASTING":
        errors.append("permit geospatial source X interpretation changed")
    if policy.get("source_y_interpretation") != "NORTHING":
        errors.append("permit geospatial source Y interpretation changed")
    for key in ("exact_parent_build_required", "future_snapshot_revalidation_required"):
        if policy.get(key) is not True:
            errors.append(f"permit geospatial policy must keep {key}=true")
    if policy.get("partial_coordinate_policy") != "FAIL_CLOSED":
        errors.append("permit geospatial partial-coordinate policy changed")
    if policy.get("nonfinite_transform_policy") != "FAIL_CLOSED":
        errors.append("permit geospatial nonfinite-transform policy changed")
    if policy.get("publication_policy") != "LOCAL_PRIVATE_ONLY_PUBLICATION_REVIEW_REQUIRED":
        errors.append("permit geospatial publication policy changed")

    linkage = schema.get("parent_linkage", {})
    if linkage.get("columns") != ["source_key", "source_row_number", "management_number"]:
        errors.append("permit geospatial parent linkage changed")
    if linkage.get("official_primary_key_claim") is not False:
        errors.append("permit geospatial linkage must not claim an official primary key")

    columns = schema.get("columns", [])
    names = [item.get("name") for item in columns]
    if len(columns) != 7 or len(set(names)) != 7 or set(names) != REQUIRED_GEOSPATIAL_COLUMNS:
        errors.append("permit geospatial schema must contain exactly the frozen seven columns")
    by_name = {item.get("name"): item for item in columns}
    for name in ("source_key", "management_number", "parent_permit_build_id", "coordinate_quality"):
        item = by_name.get(name, {})
        if item.get("logical_type") != "string" or item.get("nullable") is not False:
            errors.append(f"{name} geospatial contract changed")
    if by_name.get("source_row_number", {}).get("logical_type") != "int64" or by_name.get("source_row_number", {}).get("nullable") is not False:
        errors.append("source_row_number geospatial contract changed")
    for name in ("wgs84_longitude", "wgs84_latitude"):
        item = by_name.get(name, {})
        if item.get("logical_type") != "float64" or item.get("nullable") is not True:
            errors.append(f"{name} must remain nullable float64")
    if by_name.get("coordinate_quality", {}).get("allowed_values") != GEOSPATIAL_QUALITY_VALUES:
        errors.append("permit geospatial quality enum changed")
    return errors


def validate_public_permit_aggregate_schema(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if schema.get("schema_name") != "public_permit_aggregate" or schema.get("schema_version") != 1:
        errors.append("public permit aggregate schema identity/version changed")
    if schema.get("grain") != "PRIVACY_MINIMIZED_PERMIT_AGGREGATE_CELL":
        errors.append("public permit aggregate grain changed")

    scope = schema.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("public permit aggregate scope must exactly match v1 sources")
    if scope.get("parent_schema") != "schemas/permit_parent.v1.json":
        errors.append("public permit aggregate parent schema changed")
    if scope.get("parent_build_id") != "permit-v1-9908225df465e2ff":
        errors.append("public permit aggregate parent build changed")
    if scope.get("parent_rows") != 3_010_802:
        errors.append("public permit aggregate parent row count changed")
    for key in ("row_level_public_projection_approved", "aggregate_publication_approved"):
        if scope.get(key) is not False:
            errors.append(f"public permit aggregate must keep {key}=false")
    if scope.get("redistribution_status") != "UNRESOLVED":
        errors.append("public permit aggregate redistribution must remain unresolved")

    privacy = schema.get("privacy_policy", {})
    if privacy.get("minimum_cell_count") != 10:
        errors.append("public permit aggregate minimum cell count changed")
    if privacy.get("minimum_cell_count_is_legal_privacy_guarantee") is not False:
        errors.append("minimum cell count must not be represented as a legal privacy guarantee")
    if privacy.get("cells_below_threshold") != "SUPPRESS_ENTIRE_CELL":
        errors.append("public permit aggregate suppression policy changed")
    for key in (
        "exact_dates_included",
        "precise_coordinates_included",
        "business_names_included",
        "addresses_included",
        "management_numbers_included",
        "source_row_numbers_included",
        "telephone_or_homepage_included",
    ):
        if privacy.get(key) is not False:
            errors.append(f"public permit aggregate must keep {key}=false")
    if privacy.get("publication_requires_separate_redistribution_clearance") is not True:
        errors.append("public permit aggregate must require separate redistribution clearance")

    semantics = schema.get("semantic_policy", {})
    for key in (
        "permit_year_is_physical_open_year",
        "closure_year_is_irreversible_terminal_event",
        "canonical_status_mapping_enabled",
        "status_code_03_irreversible",
        "status_code_05_semantics_resolved",
    ):
        if semantics.get(key) is not False:
            errors.append(f"public permit aggregate semantic policy must keep {key}=false")

    if schema.get("grouping_columns") != PUBLIC_AGGREGATE_GROUPING_COLUMNS:
        errors.append("public permit aggregate grouping columns changed")
    columns = schema.get("columns", [])
    names = [item.get("name") for item in columns]
    if len(columns) != 7 or len(set(names)) != 7 or set(names) != REQUIRED_PUBLIC_AGGREGATE_COLUMNS:
        errors.append("public permit aggregate schema must contain exactly the frozen seven columns")
    by_name = {item.get("name"): item for item in columns}
    for name in ("source_key", "authority_code"):
        item = by_name.get(name, {})
        if item.get("logical_type") != "string" or item.get("nullable") is not False:
            errors.append(f"{name} public aggregate contract changed")
    for name in ("source_status_code", "source_detail_status_code"):
        item = by_name.get(name, {})
        if item.get("logical_type") != "string" or item.get("nullable") is not True:
            errors.append(f"{name} public aggregate contract changed")
    for name in ("permit_year", "closure_year"):
        item = by_name.get(name, {})
        if item.get("logical_type") != "int32" or item.get("nullable") is not True:
            errors.append(f"{name} public aggregate contract changed")
    cell_count = by_name.get("cell_count", {})
    if cell_count.get("logical_type") != "int64" or cell_count.get("nullable") is not False:
        errors.append("cell_count public aggregate contract changed")
    if cell_count.get("constraints") != [">= 10"]:
        errors.append("cell_count minimum constraint changed")

    parent_columns = REQUIRED_CANONICAL_COLUMNS
    excluded = set(schema.get("explicitly_excluded_parent_fields", []))
    directly_retained_parent = {
        "source_key",
        "authority_code",
        "source_status_code",
        "source_detail_status_code",
    }
    if excluded | directly_retained_parent != parent_columns or excluded & directly_retained_parent:
        errors.append("public permit aggregate parent-field partition changed")
    return errors


def validate_permit_status_episode_schema(schema: dict[str, Any]) -> list[str]:
    errors: list[str] = []

    if schema.get("schema_name") != "permit_status_episode" or schema.get("schema_version") != 1:
        errors.append("permit status episode schema identity/version changed")
    if schema.get("grain") != "PERMIT_STATUS_EPISODE":
        errors.append("permit status episode grain must remain PERMIT_STATUS_EPISODE")

    scope = schema.get("scope", {})
    if set(scope.get("sources", [])) != V1_SOURCE_KEYS:
        errors.append("permit status episode source scope must exactly match v1")
    if scope.get("parent_schema") != "schemas/permit_parent.v1.json":
        errors.append("permit status episode parent schema reference changed")
    if scope.get("production_reconstruction_enabled") is not False:
        errors.append("production episode reconstruction must remain disabled")
    if scope.get("establishment_identity_claim") is not False:
        errors.append("permit status episode schema must not claim establishment identity")
    if scope.get("terminal_event_claim") is not False:
        errors.append("permit status episode schema must not claim a terminal event")

    policy = schema.get("episode_policy", {})
    if policy.get("parent_linkage") != ["source_key", "management_number"]:
        errors.append("permit status episode parent linkage changed")
    if policy.get("parent_linkage_is_primary_key_claim") is not False:
        errors.append("permit status episode linkage must not become a primary-key claim")
    if policy.get("state_partition_fields") != EPISODE_STATE_PARTITION_FIELDS:
        errors.append("episode state partition must remain the source status four-tuple")
    if policy.get("episode_number_persistent_identity") is not False:
        errors.append("episode_number must remain window-local rather than persistent identity")
    if policy.get("first_episode_start_censoring") != "LEFT_CENSORED":
        errors.append("first episode start must remain left-censored")
    if policy.get("between_episode_boundary_censoring") != "INTERVAL_CENSORED":
        errors.append("between-episode transitions must remain interval-censored")
    if policy.get("last_episode_end_censoring") != "RIGHT_CENSORED":
        errors.append("last episode end must remain right-censored")
    if policy.get("exact_transition_time_claimed") is not False:
        errors.append("sparse observations must not claim an exact transition time")
    if policy.get("canonical_status_mapping_enabled") is not False:
        errors.append("canonical status mapping must remain disabled")
    if policy.get("status_code_03_irreversible") is not False:
        errors.append("status code 03 must not become an irreversible terminal state")
    if policy.get("closure_date_permanent_terminal_event") is not False:
        errors.append("closure date must not become a permanent terminal event")
    if policy.get("status_code_05_semantics_resolved") is not False:
        errors.append("status code 05 must remain semantically unresolved")
    if policy.get("publication_policy") != "NOT_APPROVED_FOR_PUBLIC_ROW_LEVEL_BUILD":
        errors.append("permit status episode publication must remain blocked")

    columns = schema.get("columns", [])
    names = [item.get("name") for item in columns]
    name_set = set(names)
    if len(columns) != 23 or len(name_set) != 23:
        errors.append("permit status episode schema must contain 23 uniquely named columns")
    if name_set != REQUIRED_EPISODE_COLUMNS:
        missing = sorted(REQUIRED_EPISODE_COLUMNS - name_set)
        extra = sorted(name_set - REQUIRED_EPISODE_COLUMNS)
        errors.append(f"permit status episode columns changed; missing={missing}, extra={extra}")
    if name_set & FORBIDDEN_EPISODE_COLUMNS:
        errors.append("permit status episode schema contains a forbidden inferred semantic field")

    by_name = {item.get("name"): item for item in columns}
    for name in ("source_key", "management_number"):
        item = by_name.get(name, {})
        if item.get("logical_type") != "string" or item.get("nullable") is not False:
            errors.append(f"{name} episode linkage contract changed")

    for name in (
        "observation_window_start_date",
        "observation_window_end_date",
        "first_observed_date",
        "last_observed_date",
        "start_boundary_upper_date",
        "end_boundary_lower_date",
    ):
        item = by_name.get(name, {})
        if item.get("logical_type") != "date32" or item.get("nullable") is not False:
            errors.append(f"{name} must remain a non-null date32")

    for name in (
        "start_boundary_lower_date",
        "end_boundary_upper_date",
        "source_closure_date_first_observed",
        "source_closure_date_last_observed",
    ):
        item = by_name.get(name, {})
        if item.get("logical_type") != "date32" or item.get("nullable") is not True:
            errors.append(f"{name} must remain a nullable date32")

    if by_name.get("episode_number", {}).get("constraints") != [">= 1"]:
        errors.append("episode_number sequence constraint changed")
    if by_name.get("observation_count", {}).get("constraints") != [">= 1"]:
        errors.append("observation_count constraint changed")
    for name in ("episode_number", "observation_count"):
        item = by_name.get(name, {})
        if item.get("logical_type") != "int32" or item.get("nullable") is not False:
            errors.append(f"{name} must remain a non-null int32")

    for name in EPISODE_STATE_PARTITION_FIELDS:
        item = by_name.get(name, {})
        if item.get("logical_type") != "string" or item.get("nullable") is not True:
            errors.append(f"{name} must remain a nullable source-state string")

    if by_name.get("start_censoring", {}).get("allowed_values") != [
        "LEFT_CENSORED",
        "INTERVAL_CENSORED",
    ]:
        errors.append("start_censoring enum changed")
    if by_name.get("end_censoring", {}).get("allowed_values") != [
        "INTERVAL_CENSORED",
        "RIGHT_CENSORED",
    ]:
        errors.append("end_censoring enum changed")
    for name in ("start_censoring", "end_censoring"):
        item = by_name.get(name, {})
        if item.get("logical_type") != "string" or item.get("nullable") is not False:
            errors.append(f"{name} must remain a non-null string")

    right_censored = by_name.get("right_censored", {})
    if right_censored.get("logical_type") != "bool" or right_censored.get("nullable") is not False:
        errors.append("right_censored must remain a non-null bool")
    if right_censored.get("derivation") != "end_censoring == RIGHT_CENSORED":
        errors.append("right_censored derivation changed")

    expected_quality = ["VALID", "MISSING", "INVALID"]
    for name in ("source_closure_date_first_quality", "source_closure_date_last_quality"):
        item = by_name.get(name, {})
        if (
            item.get("logical_type") != "string"
            or item.get("nullable") is not False
            or item.get("allowed_values") != expected_quality
        ):
            errors.append(f"{name} quality contract changed")

    row_invariants = schema.get("row_invariants", [])
    if len(row_invariants) != len(EPISODE_ROW_INVARIANTS) or set(row_invariants) != EPISODE_ROW_INVARIANTS:
        errors.append("permit status episode row invariants changed")

    explicit_absent = set(schema.get("explicitly_absent_fields", []))
    if explicit_absent != FORBIDDEN_EPISODE_COLUMNS:
        errors.append("explicitly absent episode semantic fields changed")

    if schema.get("next_gate") != (
        "implement deterministic PERMIT parent transformation first; keep nationwide episode reconstruction disabled"
    ):
        errors.append("permit status episode next gate changed")

    return errors
