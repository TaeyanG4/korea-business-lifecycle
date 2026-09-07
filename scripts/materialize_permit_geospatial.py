from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from korea_business_lifecycle.geospatial_enrichment import (
    format_geospatial_enrichment_progress,
    geospatial_enrichment_plan,
    materialize_permit_geospatial,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a local WGS84 enrichment sidecar from the independently verified immutable PERMIT build. "
            "Default mode prints the plan only; --execute performs materialization."
        )
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--data-root", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.execute:
        plan = geospatial_enrichment_plan(data_root=args.data_root)
        plan["execute_command"] = "python scripts/materialize_permit_geospatial.py --execute"
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    def progress(event: dict[str, object]) -> None:
        print(format_geospatial_enrichment_progress(event), file=sys.stderr, flush=True)

    result = materialize_permit_geospatial(data_root=args.data_root, progress=progress)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
