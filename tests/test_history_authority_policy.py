from __future__ import annotations

from korea_business_lifecycle.history_authority_policy import (
    REFORM_DATE,
    date_effective_authority_codes,
)
from korea_business_lifecycle.provenance import load_authority_domain_reference


def test_pre_reform_domain_is_current_minus_new_plus_deleted() -> None:
    reference = load_authority_domain_reference()
    current = {item["code"] for item in reference["official_current_numeric_authorities"]}
    new = {item["code"] for item in reference["official_new_numeric_authorities"]}
    deleted = {item["code"] for item in reference["official_deleted_numeric_authorities"]}
    observed = set(date_effective_authority_codes("20260630", authority_reference=reference))
    assert len(observed) == 244
    assert observed == (current - new) | deleted
    assert observed.isdisjoint(new)
    assert deleted <= observed


def test_post_reform_domain_is_current_only() -> None:
    reference = load_authority_domain_reference()
    current = {item["code"] for item in reference["official_current_numeric_authorities"]}
    deleted = {item["code"] for item in reference["official_deleted_numeric_authorities"]}
    observed = set(date_effective_authority_codes(REFORM_DATE, authority_reference=reference))
    assert len(observed) == 244
    assert observed == current
    assert observed.isdisjoint(deleted)


def test_api_queryability_does_not_change_date_effective_membership() -> None:
    before = set(date_effective_authority_codes("2026-06-30"))
    after = set(date_effective_authority_codes("2026-07-01"))
    assert len(before) == len(after) == 244
    assert len(before - after) == 32
    assert len(after - before) == 32
