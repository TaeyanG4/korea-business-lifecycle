from korea_business_lifecycle.provenance import load_source_registry, validate_source_registry


def test_source_registry_invariants() -> None:
    registry = load_source_registry()
    assert validate_source_registry(registry) == []


def test_v1_catalog_planning_scale() -> None:
    registry = load_source_registry()
    rows = [item["catalog_row_count"] for item in registry["categories"]]
    assert rows == [2_129_830, 561_397, 60_302]
    assert sum(rows) == 2_751_529


def test_no_category_claims_a_primary_key() -> None:
    registry = load_source_registry()
    assert all(item["documented_primary_key"] is None for item in registry["categories"])
