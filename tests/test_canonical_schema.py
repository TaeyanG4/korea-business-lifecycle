from korea_business_lifecycle.canonical_schema import (
    FROZEN_V1_SOURCE_COLUMNS,
    load_permit_parent_schema,
    validate_permit_parent_schema,
)


def test_permit_parent_schema_is_frozen_and_valid() -> None:
    schema = load_permit_parent_schema()
    assert validate_permit_parent_schema(schema) == []
    assert schema["grain"] == "PERMIT"
    assert len(schema["columns"]) == 26
    assert len(schema["source_column_inventory"]) == 39


def test_permit_parent_source_inventory_is_fully_partitioned() -> None:
    schema = load_permit_parent_schema()
    mapped = {item["source_column"] for item in schema["columns"] if "source_column" in item}
    deferred = {item["source_column"] for item in schema["deferred_source_columns"]}
    assert len(mapped) == 20
    assert len(deferred) == 19
    assert mapped.isdisjoint(deferred)
    assert mapped | deferred == FROZEN_V1_SOURCE_COLUMNS


def test_permit_parent_does_not_invent_establishment_or_terminal_semantics() -> None:
    schema = load_permit_parent_schema()
    names = {item["name"] for item in schema["columns"]}
    assert "establishment_id" not in names
    assert "terminal_event_flag" not in names
    assert "physical_open_date" not in names
    assert "canonical_active_flag" not in names
    assert schema["build_policy"]["expected_unique_candidate_is_primary_key_claim"] is False
    assert schema["build_policy"]["publication_policy"] == "NOT_APPROVED_FOR_PUBLIC_ROW_LEVEL_BUILD"


def test_permit_parent_keeps_coordinates_untransformed() -> None:
    schema = load_permit_parent_schema()
    columns = {item["name"]: item for item in schema["columns"]}
    assert columns["source_coordinate_x"]["logical_type"] == "float64"
    assert columns["source_coordinate_y"]["logical_type"] == "float64"
    assert schema["metadata"]["declared_source_crs"] == "EPSG:5174"
    assert schema["metadata"]["coordinate_axis_order_validated"] is False
    assert "wgs84_latitude" in schema["explicitly_absent_fields"]
    assert "wgs84_longitude" in schema["explicitly_absent_fields"]
