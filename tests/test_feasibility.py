from korea_business_lifecycle.feasibility import kaggle_publication_ready, load_feasibility


def test_first_milestone_is_not_kaggle_ready() -> None:
    feasibility = load_feasibility()
    assert feasibility["decision"] == "FEASIBLE_FOR_BOUNDED_PROFILING_ONLY"
    assert kaggle_publication_ready(feasibility) is False


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

