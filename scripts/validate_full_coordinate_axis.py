from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from korea_business_lifecycle.geospatial_qa import (
    DEFAULT_FULL_PROGRESS_EVERY_ROWS,
    format_full_geospatial_progress,
    full_geospatial_axis_plan,
    validate_full_snapshot_coordinate_axes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run aggregate-only full-snapshot EPSG:5174 source-field axis QA. "
            "Default mode prints the plan; --execute scans all current rows."
        )
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--progress-every", type=int, default=DEFAULT_FULL_PROGRESS_EVERY_ROWS)
    parser.add_argument("--data-root", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.execute:
        plan = full_geospatial_axis_plan()
        plan["execute_command"] = "python scripts/validate_full_coordinate_axis.py --execute"
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    def progress(event: dict[str, object]) -> None:
        print(format_full_geospatial_progress(event), file=sys.stderr, flush=True)

    result = validate_full_snapshot_coordinate_axes(
        data_root=args.data_root,
        progress_every_rows=args.progress_every,
        progress=progress,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
