from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.canonical_materialization_verify import verify_permit_parent_build


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Independently verify the immutable local PERMIT Parquet/ZSTD production build."
    )
    parser.add_argument("--build-id", default=None)
    parser.add_argument("--data-root", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = verify_permit_parent_build(data_root=args.data_root, build_id=args.build_id)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
