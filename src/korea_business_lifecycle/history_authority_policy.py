from __future__ import annotations

from datetime import date, datetime
from typing import Any, Mapping

from .provenance import (
    load_authority_domain_reference,
    load_history_authority_partition_full_probe,
)


REFORM_DATE = date(2026, 7, 1)


class HistoryAuthorityPolicyError(RuntimeError):
    """Raised when the date-effective current-state authority policy is inconsistent."""


def _coerce_date(value: date | str) -> date:
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
    raise HistoryAuthorityPolicyError("base date must be YYYY-MM-DD or YYYYMMDD")


def _codes(rows: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(rows, list):
        raise HistoryAuthorityPolicyError(f"{field} must be a list")
    codes = tuple(str(item.get("code", "")) for item in rows if isinstance(item, Mapping))
    if len(codes) != len(rows) or len(codes) != len(set(codes)):
        raise HistoryAuthorityPolicyError(f"{field} must contain unique authority codes")
    if any(len(code) != 7 or not code.isdigit() for code in codes):
        raise HistoryAuthorityPolicyError(f"{field} must contain seven-digit numeric authority codes")
    return tuple(sorted(codes))


def date_effective_authority_codes(
    base_date: date | str,
    *,
    authority_reference: Mapping[str, Any] | None = None,
) -> tuple[str, ...]:
    """Return the approved current-state authority domain for an as-of date.

    API queryability is deliberately ignored here. New partitions can answer pre-reform
    BASE_DATE queries and deleted partitions can answer post-reform queries, but those
    responses are not treated as date-effective current-state membership.
    """
    observed_date = _coerce_date(base_date)
    reference = authority_reference or load_authority_domain_reference()
    window = reference.get("history_window_change_reference", {})
    if window.get("date_effective_current_state_enumeration_policy_approved") is not True:
        raise HistoryAuthorityPolicyError("date-effective authority policy is not approved")
    if window.get("change_effective_date") != REFORM_DATE.isoformat():
        raise HistoryAuthorityPolicyError("authority reform date changed")

    current = _codes(reference.get("official_current_numeric_authorities"), field="current domain")
    new = _codes(reference.get("official_new_numeric_authorities"), field="new domain")
    deleted = _codes(reference.get("official_deleted_numeric_authorities"), field="deleted domain")
    pre_reform = _codes(
        reference.get("official_pre_reform_numeric_authorities"), field="pre-reform domain"
    )
    if len(current) != 244 or len(new) != 32 or len(deleted) != 32 or len(pre_reform) != 244:
        raise HistoryAuthorityPolicyError("tracked authority-domain cardinalities changed")
    if set(new) - set(current):
        raise HistoryAuthorityPolicyError("new authority codes are not a current-domain subset")
    if set(current) & set(deleted):
        raise HistoryAuthorityPolicyError("current and deleted authority domains overlap")
    derived_pre = (set(current) - set(new)) | set(deleted)
    if set(pre_reform) != derived_pre:
        raise HistoryAuthorityPolicyError("tracked pre-reform domain differs from current-new+deleted")

    return pre_reform if observed_date < REFORM_DATE else current


def build_history_authority_policy() -> dict[str, Any]:
    reference = load_authority_domain_reference()
    full_probe = load_history_authority_partition_full_probe()
    before = date_effective_authority_codes("20260630", authority_reference=reference)
    after = date_effective_authority_codes("20260701", authority_reference=reference)
    window = reference["history_window_change_reference"]
    official = reference["official_reference"]
    if full_probe["assessment"]["pairs_with_equal_counts_20260630_20260701_20260906"] != 96:
        raise HistoryAuthorityPolicyError("deleted-partition post-reform count-freeze evidence changed")
    if len(set(before) - set(after)) != 32 or len(set(after) - set(before)) != 32:
        raise HistoryAuthorityPolicyError("reform boundary must exchange exactly 32 numeric authority codes")
    return {
        "checked_at": "2026-09-07",
        "decision": "DATE_EFFECTIVE_CURRENT_STATE_AUTHORITY_POLICY_APPROVED",
        "evidence": {
            "authority_reference": "provenance/authority_domain_reference.json",
            "deleted_partition_full_probe": "provenance/history_authority_partition_full_probe.json",
            "official_change_effective_date": REFORM_DATE.isoformat(),
            "official_reference_attachment_sha256": official["attachment_sha256"],
            "api_deleted_partition_post_reform_count_freeze_pairs": 96,
        },
        "pre_reform": {
            "date_rule": "BASE_DATE < 2026-07-01",
            "policy": "CURRENT_MINUS_NEW_PLUS_DELETED",
            "numeric_authority_count": len(before),
            "numeric_authority_list_sha256": window["pre_reform_numeric_authority_list_sha256"],
            "new_numeric_codes_excluded": 32,
            "deleted_numeric_codes_included": 32,
        },
        "post_reform": {
            "date_rule": "BASE_DATE >= 2026-07-01",
            "policy": "CURRENT_ONLY_EXCLUDE_DELETED",
            "numeric_authority_count": len(after),
            "numeric_authority_list_sha256": official["current_numeric_authority_list_sha256"],
            "new_numeric_codes_included": 32,
            "deleted_numeric_codes_excluded": 32,
        },
        "overlap_semantics": {
            "same_date_old_new_union_used": False,
            "same_date_old_new_deduplication_required_by_policy": False,
            "api_queryability_defines_date_effective_membership": False,
            "cross_reform_management_number_may_link_observations": True,
            "management_number_is_source_primary_key": False,
            "duplicate_management_number_within_one_source_date_fails_closed": True,
        },
        "scope_limits": {
            "authority_code_domain_completeness_claimed_from_official_change_reference": True,
            "row_level_api_completeness_guaranteed": False,
            "history_is_lossless_event_log": False,
            "aggregate_all_tokens_used_for_row_enumeration": False,
        },
        "implementation": {
            "module": "src/korea_business_lifecycle/history_authority_policy.py",
            "script": "scripts/history_authority_policy.py",
            "network_required": False,
        },
        "next_gate": "select one production observation cadence and enforce a bounded resumable nationwide acquisition budget",
    }
