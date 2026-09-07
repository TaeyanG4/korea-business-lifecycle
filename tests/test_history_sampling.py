from korea_business_lifecycle.history_sampling import (
    AuthorityScale,
    common_authority_scales,
    select_scale_representatives,
)


def test_common_authorities_require_presence_in_every_source() -> None:
    counts = {
        "a": {"1000000": 1, "2000000": 3, "3000000": 5},
        "b": {"1000000": 2, "2000000": 4},
        "c": {"1000000": 3, "2000000": 5, "4000000": 9},
    }
    scales = common_authority_scales(counts)
    assert [(item.authority_code, item.total_rows) for item in scales] == [
        ("1000000", 6),
        ("2000000", 12),
    ]


def test_scale_selection_is_deterministic() -> None:
    scales = [
        AuthorityScale(str(i).zfill(7), i, {"a": i})
        for i in range(1, 11)
    ]
    selected = select_scale_representatives(scales)
    assert [(label, item.total_rows) for label, item in selected] == [
        ("q10", 2),
        ("q50", 5),
        ("q90", 9),
        ("max", 10),
    ]


def test_scale_selection_respects_exclusion() -> None:
    counts = {
        "a": {"1000000": 1, "2000000": 2},
        "b": {"1000000": 1, "2000000": 2},
        "c": {"1000000": 1, "2000000": 2},
    }
    scales = common_authority_scales(counts, exclude={"1000000"})
    assert [item.authority_code for item in scales] == ["2000000"]

