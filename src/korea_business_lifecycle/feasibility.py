from __future__ import annotations

from typing import Any

from .config import load_json


PUBLICATION_BLOCKING_GATES = {
    "historical_finiteness",
    "kaggle_redistribution",
    "privacy_publication",
    "identity_semantics",
    "lifecycle_semantics",
    "coordinate_field_meanings",
}


def load_feasibility() -> dict[str, Any]:
    return load_json("provenance/feasibility.json")


def kaggle_publication_ready(feasibility: dict[str, Any]) -> bool:
    gates = feasibility.get("gates", {})
    return all(gates.get(name) == "PASS" for name in PUBLICATION_BLOCKING_GATES)

