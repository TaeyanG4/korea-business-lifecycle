from __future__ import annotations

from datetime import date

import pytest

from korea_business_lifecycle.canonical_schema import REQUIRED_EPISODE_COLUMNS
from korea_business_lifecycle.episode_reconstruction import (
    DEFAULT_MAX_BOUNDED_OBSERVATIONS,
    EpisodeReconstructionError,
    reconstruct_bounded_status_episodes,
)


def _observation(
    observed_date: str,
    *,
    management_number: str = "m-001",
    status_code: str | None = "01",
    status_name: str | None = "영업/정상",
    detail_code: str | None = "01",
    detail_name: str | None = "영업",
    closure_date: str | None = None,
    closure_quality: str = "MISSING",
) -> dict[str, object]:
    return {
        "source_key": "general_restaurants",
        "management_number": management_number,
        "observed_date": observed_date,
        "source_status_code": status_code,
        "source_status_name": status_name,
        "source_detail_status_code": detail_code,
        "source_detail_status_name": detail_name,
        "source_closure_date": closure_date,
        "source_closure_date_quality": closure_quality,
    }


def test_same_source_state_coalesces_and_preserves_closure_context() -> None:
    rows = reconstruct_bounded_status_episodes(
        [
            _observation("2026-01-01"),
            _observation("2026-01-05", closure_date="2026-01-04", closure_quality="VALID"),
        ],
        observation_window_start_date="20260101",
        observation_window_end_date="20260105",
    )
    assert len(rows) == 1
    row = rows[0]
    assert set(row) == REQUIRED_EPISODE_COLUMNS
    assert row["observation_count"] == 2
    assert row["first_observed_date"] == date(2026, 1, 1)
    assert row["last_observed_date"] == date(2026, 1, 5)
    assert row["start_censoring"] == "LEFT_CENSORED"
    assert row["start_boundary_lower_date"] is None
    assert row["end_censoring"] == "RIGHT_CENSORED"
    assert row["end_boundary_upper_date"] is None
    assert row["right_censored"] is True
    assert row["source_closure_date_first_observed"] is None
    assert row["source_closure_date_first_quality"] == "MISSING"
    assert row["source_closure_date_last_observed"] == date(2026, 1, 4)
    assert row["source_closure_date_last_quality"] == "VALID"


def test_03_to_01_is_two_interval_censored_source_state_episodes_not_reopening_semantics() -> None:
    rows = reconstruct_bounded_status_episodes(
        [
            _observation(
                "2026-03-16",
                status_code="03",
                status_name="폐업",
                detail_code="02",
                detail_name="폐업",
                closure_date="2026-03-16",
                closure_quality="VALID",
            ),
            _observation(
                "2026-03-17",
                status_code="01",
                status_name="영업/정상",
                detail_code="01",
                detail_name="영업",
            ),
        ],
        observation_window_start_date="2026-03-16",
        observation_window_end_date="2026-03-17",
    )
    assert len(rows) == 2
    closed, active = rows
    assert closed["episode_number"] == 1
    assert closed["source_status_code"] == "03"
    assert closed["start_censoring"] == "LEFT_CENSORED"
    assert closed["end_censoring"] == "INTERVAL_CENSORED"
    assert closed["end_boundary_lower_date"] == date(2026, 3, 16)
    assert closed["end_boundary_upper_date"] == date(2026, 3, 17)
    assert closed["right_censored"] is False
    assert active["episode_number"] == 2
    assert active["source_status_code"] == "01"
    assert active["start_censoring"] == "INTERVAL_CENSORED"
    assert active["start_boundary_lower_date"] == date(2026, 3, 16)
    assert active["start_boundary_upper_date"] == date(2026, 3, 17)
    assert active["end_censoring"] == "RIGHT_CENSORED"
    assert active["right_censored"] is True
    for row in rows:
        assert "reopened_flag" not in row
        assert "terminal_event_flag" not in row
        assert "exact_close_date" not in row


def test_repeated_state_after_intervening_state_creates_new_window_local_episode() -> None:
    rows = reconstruct_bounded_status_episodes(
        [
            _observation("2026-01-01", status_code="01"),
            _observation("2026-02-01", status_code="03", status_name="폐업", detail_code="02", detail_name="폐업"),
            _observation("2026-03-01", status_code="01"),
        ],
        observation_window_start_date="2026-01-01",
        observation_window_end_date="2026-03-01",
    )
    assert [row["episode_number"] for row in rows] == [1, 2, 3]
    assert [row["source_status_code"] for row in rows] == ["01", "03", "01"]


def test_status_05_is_preserved_without_semantic_mapping() -> None:
    rows = reconstruct_bounded_status_episodes(
        [
            _observation(
                "2026-01-01",
                status_code="05",
                status_name="기타",
                detail_code=None,
                detail_name=None,
            )
        ],
        observation_window_start_date="2026-01-01",
        observation_window_end_date="2026-01-01",
    )
    assert rows[0]["source_status_code"] == "05"
    assert rows[0]["source_detail_status_code"] is None
    assert "canonical_active_flag" not in rows[0]
    assert "canonical_closed_flag" not in rows[0]


def test_input_order_does_not_change_deterministic_episode_output() -> None:
    observations = [
        _observation("2026-01-03", management_number="m-002"),
        _observation("2026-01-01", management_number="m-001"),
        _observation("2026-01-02", management_number="m-001"),
    ]
    forward = reconstruct_bounded_status_episodes(
        observations,
        observation_window_start_date="2026-01-01",
        observation_window_end_date="2026-01-03",
    )
    reverse = reconstruct_bounded_status_episodes(
        reversed(observations),
        observation_window_start_date="2026-01-01",
        observation_window_end_date="2026-01-03",
    )
    assert forward == reverse
    assert [(row["management_number"], row["episode_number"]) for row in forward] == [
        ("m-001", 1),
        ("m-002", 1),
    ]


def test_duplicate_permit_date_observation_fails_closed() -> None:
    with pytest.raises(EpisodeReconstructionError, match="duplicate permit/date observation"):
        reconstruct_bounded_status_episodes(
            [_observation("2026-01-01"), _observation("2026-01-01")],
            observation_window_start_date="2026-01-01",
            observation_window_end_date="2026-01-01",
        )


def test_observation_outside_window_fails_closed() -> None:
    with pytest.raises(EpisodeReconstructionError, match="outside"):
        reconstruct_bounded_status_episodes(
            [_observation("2025-12-31")],
            observation_window_start_date="2026-01-01",
            observation_window_end_date="2026-01-02",
        )


@pytest.mark.parametrize(
    ("closure_date", "quality"),
    [(None, "VALID"), ("2026-01-01", "MISSING"), ("2026-01-01", "INVALID")],
)
def test_closure_date_quality_consistency_fails_closed(
    closure_date: str | None, quality: str
) -> None:
    with pytest.raises(EpisodeReconstructionError):
        reconstruct_bounded_status_episodes(
            [
                _observation(
                    "2026-01-01",
                    closure_date=closure_date,
                    closure_quality=quality,
                )
            ],
            observation_window_start_date="2026-01-01",
            observation_window_end_date="2026-01-01",
        )


def test_bounded_observation_cap_blocks_production_scale_use() -> None:
    assert DEFAULT_MAX_BOUNDED_OBSERVATIONS == 100_000
    with pytest.raises(EpisodeReconstructionError, match="production reconstruction remains disabled"):
        reconstruct_bounded_status_episodes(
            [_observation("2026-01-01"), _observation("2026-01-02")],
            observation_window_start_date="2026-01-01",
            observation_window_end_date="2026-01-02",
            max_observations=1,
        )
