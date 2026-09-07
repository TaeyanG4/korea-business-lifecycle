from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from korea_business_lifecycle.canonical_materialization import (
    format_materialization_progress,
    materialization_plan,
    materialize_permit_parent,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build the local-only frozen PERMIT parent as Parquet/ZSTD. Default mode prints a plan; "
            "--execute performs the long production materialization."
        )
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--data-root", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if not args.execute:
        plan = materialization_plan(data_root=args.data_root)
        plan["execute_command"] = "python scripts/materialize_permit_parent.py --execute"
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    def progress(event: dict[str, object]) -> None:
        print(format_materialization_progress(event), file=sys.stderr, flush=True)

    result = materialize_permit_parent(data_root=args.data_root, progress=progress)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
