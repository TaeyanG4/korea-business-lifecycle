from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.geospatial_qa import (
    DEFAULT_MAX_COORDINATE_PAIRS,
    probe_latest_coordinate_axes,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run bounded aggregate-only EPSG:5174 source X/Y axis plausibility QA. "
            "No row-level coordinates or WGS84 columns are emitted."
        )
    )
    parser.add_argument("--max-pairs", type=int, default=DEFAULT_MAX_COORDINATE_PAIRS)
    parser.add_argument("--data-root", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = probe_latest_coordinate_axes(data_root=args.data_root, max_pairs=args.max_pairs)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
