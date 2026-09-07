from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.cross_category_audit import (
    audit_cross_category_current_snapshots,
)
from korea_business_lifecycle.storage import require_external_artifact, resolve_data_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit cross-category current-snapshot identifier overlap without entity merging."
    )
    parser.add_argument("assignments", nargs="+", help="source_key=/absolute/path/to/source.csv")
    parser.add_argument("--data-root", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = resolve_data_root(args.data_root)
    sources: dict[str, Path] = {}
    for assignment in args.assignments:
        source_key, separator, raw_path = assignment.partition("=")
        if not separator:
            raise SystemExit(f"invalid assignment: {assignment}")
        sources[source_key] = require_external_artifact(raw_path, root)
    output_dir = root / "staging" / "audits" / "cross_category"
    output_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = output_dir / "cross-category-work.sqlite"
    result = audit_cross_category_current_snapshots(
        sources,
        sqlite_path=sqlite_path,
    )
    if sqlite_path.exists():
        sqlite_path.unlink()
    output_path = output_dir / "audit.json"
    output_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
