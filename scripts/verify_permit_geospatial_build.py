from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from korea_business_lifecycle.geospatial_enrichment_verify import (
    format_geospatial_verification_progress,
    verify_permit_geospatial_build,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Independently verify the immutable local PERMIT WGS84 enrichment build."
    )
    parser.add_argument("--build-id", default=None)
    parser.add_argument("--data-root", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    def progress(event: dict[str, object]) -> None:
        print(format_geospatial_verification_progress(event), file=sys.stderr, flush=True)

    result = verify_permit_geospatial_build(
        data_root=args.data_root,
        build_id=args.build_id,
        progress=progress,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
