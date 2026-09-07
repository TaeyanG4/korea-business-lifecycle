from __future__ import annotations

from typing import Any

from .config import load_json


AGGREGATE_PUBLICATION_GATES = {
    "authoritative_v1_sources": "PASS",
    "current_snapshot_profile": "PASS",
    "kaggle_redistribution": "PASS_AGGREGATE_ONLY",
    "privacy_publication": "PASS_AGGREGATE_ONLY_ROW_LEVEL_BLOCKED",
}


def load_feasibility() -> dict[str, Any]:
    return load_json("provenance/feasibility.json")


def kaggle_publication_ready(feasibility: dict[str, Any]) -> bool:
    gates = feasibility.get("gates", {})
    return all(gates.get(name) == expected for name, expected in AGGREGATE_PUBLICATION_GATES.items())
