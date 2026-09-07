from korea_business_lifecycle.feasibility import kaggle_publication_ready, load_feasibility


def test_first_milestone_is_not_kaggle_ready() -> None:
    feasibility = load_feasibility()
    assert feasibility["decision"] == "CURRENT_SNAPSHOTS_PROFILED_HISTORY_AUTH_REQUIRED"
    assert kaggle_publication_ready(feasibility) is False


def test_history_execution_is_blocked_on_user_service_key() -> None:
    gates = load_feasibility()["gates"]
    assert gates["historical_finiteness"] == "CONDITIONAL_PASS_PER_DATE_AND_AUTHORITY_CODE"
    assert gates["history_service_key"] == "BLOCKED_USER_CREDENTIAL_REQUIRED"
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
