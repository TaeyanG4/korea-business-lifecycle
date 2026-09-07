from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Iterable, Mapping

from .canonical_schema import EPISODE_STATE_PARTITION_FIELDS
from .provenance import V1_SOURCE_KEYS


DEFAULT_MAX_BOUNDED_OBSERVATIONS = 100_000
DATE_QUALITY_VALUES = {"VALID", "MISSING", "INVALID"}


class EpisodeReconstructionError(RuntimeError):
    """Raised when bounded sparse observations cannot be reconstructed safely."""


@dataclass(frozen=True)
class EpisodeObservation:
    source_key: str
    management_number: str
    observed_date: date
    source_status_code: str | None
    source_status_name: str | None
    source_detail_status_code: str | None
    source_detail_status_name: str | None
    source_closure_date: date | None
    source_closure_date_quality: str

    @property
    def state(self) -> tuple[str | None, str | None, str | None, str | None]:
        return (
            self.source_status_code,
            self.source_status_name,
            self.source_detail_status_code,
            self.source_detail_status_name,
        )


def _coerce_date(value: Any, *, field: str, nullable: bool = False) -> date | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        if nullable:
            return None
        raise EpisodeReconstructionError(f"{field} is required")
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str):
        raw = value.strip()
        for fmt in ("%Y-%m-%d", "%Y%m%d"):
            try:
                return datetime.strptime(raw, fmt).date()
            except ValueError:
                pass
    raise EpisodeReconstructionError(f"{field} must be a valid ISO/basic calendar date")


def _nullable_text(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _required_text(value: Any, *, field: str) -> str:
    text = _nullable_text(value)
    if text is None:
        raise EpisodeReconstructionError(f"{field} is required")
    return text


def normalize_episode_observation(value: Mapping[str, Any]) -> EpisodeObservation:
    source_key = _required_text(value.get("source_key"), field="source_key")
    if source_key not in V1_SOURCE_KEYS:
        raise EpisodeReconstructionError(f"unsupported source_key: {source_key}")
    management_number = _required_text(value.get("management_number"), field="management_number")
    observed_date = _coerce_date(value.get("observed_date"), field="observed_date")
    quality = _required_text(
        value.get("source_closure_date_quality"), field="source_closure_date_quality"
    )
    if quality not in DATE_QUALITY_VALUES:
        raise EpisodeReconstructionError("source_closure_date_quality is invalid")
    closure_date = _coerce_date(
        value.get("source_closure_date"), field="source_closure_date", nullable=True
    )
    if quality == "VALID" and closure_date is None:
        raise EpisodeReconstructionError("VALID closure quality requires a parsed closure date")
    if quality in {"MISSING", "INVALID"} and closure_date is not None:
        raise EpisodeReconstructionError(
            f"{quality} closure quality requires source_closure_date to be null"
        )
    assert observed_date is not None
    return EpisodeObservation(
        source_key=source_key,
        management_number=management_number,
        observed_date=observed_date,
        source_status_code=_nullable_text(value.get("source_status_code")),
        source_status_name=_nullable_text(value.get("source_status_name")),
        source_detail_status_code=_nullable_text(value.get("source_detail_status_code")),
        source_detail_status_name=_nullable_text(value.get("source_detail_status_name")),
        source_closure_date=closure_date,
        source_closure_date_quality=quality,
    )


def _episode_row(
    observations: list[EpisodeObservation],
    *,
    episode_number: int,
    window_start: date,
    window_end: date,
    previous_episode: list[EpisodeObservation] | None,
    next_episode: list[EpisodeObservation] | None,
) -> dict[str, Any]:
    first = observations[0]
    last = observations[-1]
    if previous_episode is None:
        start_lower = None
        start_censoring = "LEFT_CENSORED"
    else:
        start_lower = previous_episode[-1].observed_date
        start_censoring = "INTERVAL_CENSORED"
    if next_episode is None:
        end_upper = None
        end_censoring = "RIGHT_CENSORED"
        right_censored = True
    else:
        end_upper = next_episode[0].observed_date
        end_censoring = "INTERVAL_CENSORED"
        right_censored = False
    return {
        "source_key": first.source_key,
        "management_number": first.management_number,
        "episode_number": episode_number,
        "observation_window_start_date": window_start,
        "observation_window_end_date": window_end,
        "first_observed_date": first.observed_date,
        "last_observed_date": last.observed_date,
        "observation_count": len(observations),
        "source_status_code": first.source_status_code,
        "source_status_name": first.source_status_name,
        "source_detail_status_code": first.source_detail_status_code,
        "source_detail_status_name": first.source_detail_status_name,
        "start_boundary_lower_date": start_lower,
        "start_boundary_upper_date": first.observed_date,
        "start_censoring": start_censoring,
        "end_boundary_lower_date": last.observed_date,
        "end_boundary_upper_date": end_upper,
        "end_censoring": end_censoring,
        "right_censored": right_censored,
        "source_closure_date_first_observed": first.source_closure_date,
        "source_closure_date_first_quality": first.source_closure_date_quality,
        "source_closure_date_last_observed": last.source_closure_date,
        "source_closure_date_last_quality": last.source_closure_date_quality,
    }


def reconstruct_bounded_status_episodes(
    observations: Iterable[Mapping[str, Any]],
    *,
    observation_window_start_date: date | str,
    observation_window_end_date: date | str,
    max_observations: int = DEFAULT_MAX_BOUNDED_OBSERVATIONS,
) -> list[dict[str, Any]]:
    """Reconstruct window-local sparse source-state episodes without production semantics.

    This function is intentionally bounded and in-memory. It does not acquire history,
    infer missing observations, map source statuses, or enable nationwide production
    reconstruction.
    """

    window_start = _coerce_date(
        observation_window_start_date, field="observation_window_start_date"
    )
    window_end = _coerce_date(observation_window_end_date, field="observation_window_end_date")
    assert window_start is not None and window_end is not None
    if window_start > window_end:
        raise EpisodeReconstructionError("observation window start must be <= end")
    if max_observations < 1:
        raise EpisodeReconstructionError("max_observations must be >= 1")

    normalized: list[EpisodeObservation] = []
    for index, raw in enumerate(observations, start=1):
        if index > max_observations:
            raise EpisodeReconstructionError(
                "bounded observation cap exceeded; nationwide production reconstruction remains disabled"
            )
        observation = normalize_episode_observation(raw)
        if not window_start <= observation.observed_date <= window_end:
            raise EpisodeReconstructionError("observation falls outside the declared observation window")
        normalized.append(observation)

    grouped: dict[tuple[str, str], list[EpisodeObservation]] = defaultdict(list)
    seen_dates: set[tuple[str, str, date]] = set()
    for observation in normalized:
        date_key = (
            observation.source_key,
            observation.management_number,
            observation.observed_date,
        )
        if date_key in seen_dates:
            raise EpisodeReconstructionError(
                "duplicate permit/date observation; one as-of state per permit/date is required"
            )
        seen_dates.add(date_key)
        grouped[(observation.source_key, observation.management_number)].append(observation)

    output: list[dict[str, Any]] = []
    for permit_key in sorted(grouped):
        permit_observations = sorted(grouped[permit_key], key=lambda item: item.observed_date)
        episode_groups: list[list[EpisodeObservation]] = []
        for observation in permit_observations:
            if not episode_groups or episode_groups[-1][-1].state != observation.state:
                episode_groups.append([observation])
            else:
                episode_groups[-1].append(observation)

        for index, episode in enumerate(episode_groups):
            previous_episode = episode_groups[index - 1] if index > 0 else None
            next_episode = episode_groups[index + 1] if index + 1 < len(episode_groups) else None
            output.append(
                _episode_row(
                    episode,
                    episode_number=index + 1,
                    window_start=window_start,
                    window_end=window_end,
                    previous_episode=previous_episode,
                    next_episode=next_episode,
                )
            )

    expected_columns = {
        "source_key",
        "management_number",
        "episode_number",
        "observation_window_start_date",
        "observation_window_end_date",
        "first_observed_date",
        "last_observed_date",
        "observation_count",
        *EPISODE_STATE_PARTITION_FIELDS,
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
    if any(set(row) != expected_columns for row in output):
        raise EpisodeReconstructionError("reconstructed episode columns differ from frozen contract")
    return output
