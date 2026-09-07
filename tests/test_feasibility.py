from korea_business_lifecycle.feasibility import kaggle_publication_ready, load_feasibility


def test_v1_aggregate_is_kaggle_ready() -> None:
    feasibility = load_feasibility()
    assert feasibility["decision"] == "LOCAL_V1_CORE_COMPLETE_HISTORY_OPTIONAL_AGGREGATE_KAGGLE_READY"
    assert kaggle_publication_ready(feasibility) is True


def test_history_is_optional_and_authenticated_execution_available() -> None:
    gates = load_feasibility()["gates"]
    assert gates["historical_finiteness"] == "CONDITIONAL_PASS_PER_DATE_AND_AUTHORITY_CODE"
    assert gates["history_service_key"] == "PASS_AUTHENTICATED_EXECUTION_AVAILABLE"
    assert gates["history_event_log_completeness"] == "NOT_SUPPORTED_BY_DOCUMENTED_SEMANTICS"


def test_all_five_stop_or_redesign_domains_are_explicit() -> None:
    gates = load_feasibility()["gates"]
    for gate in (
        "historical_finiteness",
        "kaggle_redistribution",
        "identity_semantics",
        "lifecycle_semantics",
        "coordinate_field_meanings",
    ):
        assert gate in gates
