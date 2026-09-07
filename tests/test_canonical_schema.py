from copy import deepcopy

from korea_business_lifecycle.canonical_schema import (
    EPISODE_STATE_PARTITION_FIELDS,
    FROZEN_V1_SOURCE_COLUMNS,
    FORBIDDEN_EPISODE_COLUMNS,
    REQUIRED_EPISODE_COLUMNS,
    load_permit_parent_schema,
    load_permit_status_episode_schema,
    validate_permit_parent_schema,
    validate_permit_status_episode_schema,
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


def test_permit_status_episode_schema_is_frozen_and_valid() -> None:
    schema = load_permit_status_episode_schema()
    assert validate_permit_status_episode_schema(schema) == []
    assert schema["grain"] == "PERMIT_STATUS_EPISODE"
    assert len(schema["columns"]) == 23
    assert {item["name"] for item in schema["columns"]} == REQUIRED_EPISODE_COLUMNS
    assert schema["scope"]["production_reconstruction_enabled"] is False


def test_permit_status_episode_links_to_parent_without_pk_or_establishment_claim() -> None:
    parent = load_permit_parent_schema()
    episode = load_permit_status_episode_schema()
    linkage = episode["episode_policy"]["parent_linkage"]
    assert linkage == parent["build_policy"]["expected_unique_candidate"]
    assert episode["episode_policy"]["parent_linkage_is_primary_key_claim"] is False
    assert episode["scope"]["establishment_identity_claim"] is False
    assert "establishment_id" in episode["explicitly_absent_fields"]
    assert "episode_id" in episode["explicitly_absent_fields"]


def test_permit_status_episode_preserves_source_state_and_censoring_contract() -> None:
    schema = load_permit_status_episode_schema()
    policy = schema["episode_policy"]
    columns = {item["name"]: item for item in schema["columns"]}

    assert policy["state_partition_fields"] == EPISODE_STATE_PARTITION_FIELDS
    assert policy["canonical_status_mapping_enabled"] is False
    assert policy["first_episode_start_censoring"] == "LEFT_CENSORED"
    assert policy["between_episode_boundary_censoring"] == "INTERVAL_CENSORED"
    assert policy["last_episode_end_censoring"] == "RIGHT_CENSORED"
    assert policy["exact_transition_time_claimed"] is False
    assert columns["start_censoring"]["allowed_values"] == ["LEFT_CENSORED", "INTERVAL_CENSORED"]
    assert columns["end_censoring"]["allowed_values"] == ["INTERVAL_CENSORED", "RIGHT_CENSORED"]
    assert columns["right_censored"]["derivation"] == "end_censoring == RIGHT_CENSORED"


def test_permit_status_episode_rejects_terminal_and_unresolved_status_semantic_drift() -> None:
    schema = load_permit_status_episode_schema()
    policy = schema["episode_policy"]
    assert policy["status_code_03_irreversible"] is False
    assert policy["closure_date_permanent_terminal_event"] is False
    assert policy["status_code_05_semantics_resolved"] is False
    assert policy["canonical_status_mapping_enabled"] is False
    assert set(schema["explicitly_absent_fields"]) == FORBIDDEN_EPISODE_COLUMNS

    mutations = []
    for key in (
        "exact_transition_time_claimed",
        "canonical_status_mapping_enabled",
        "status_code_03_irreversible",
        "closure_date_permanent_terminal_event",
        "status_code_05_semantics_resolved",
    ):
        mutated = deepcopy(schema)
        mutated["episode_policy"][key] = True
        mutations.append(mutated)

    mutated = deepcopy(schema)
    mutated["scope"]["production_reconstruction_enabled"] = True
    mutations.append(mutated)

    mutated = deepcopy(schema)
    mutated["columns"].append(
        {"name": "terminal_event_flag", "logical_type": "bool", "nullable": False, "role": "inferred"}
    )
    mutations.append(mutated)

    for mutated in mutations:
        assert validate_permit_status_episode_schema(mutated)
