from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from korea_business_lifecycle.canonical_full_dry_run import (
    DEFAULT_PROGRESS_EVERY_ROWS,
    V1_SOURCE_ORDER,
    dry_run_latest_full_snapshots,
    format_full_dry_run_progress,
    full_dry_run_plan,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Stream current snapshots through the frozen PERMIT transformer without writing "
            "canonical output. Default mode prints the plan only; --execute performs the full scan."
        )
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument(
        "--source",
        choices=["all", *V1_SOURCE_ORDER],
        default="all",
        help="scan all v1 sources or one source only",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=DEFAULT_PROGRESS_EVERY_ROWS,
        help="emit aggregate progress after this many transformed rows",
    )
    parser.add_argument("--data-root", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    source_keys = V1_SOURCE_ORDER if args.source == "all" else (args.source,)
    if not args.execute:
        plan = full_dry_run_plan(source_keys=source_keys)
        plan["execute_command"] = (
            "python scripts/dry_run_full_current_snapshot.py --execute"
            if args.source == "all"
            else f"python scripts/dry_run_full_current_snapshot.py --execute --source {args.source}"
        )
        print(json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    def progress(event: dict[str, object]) -> None:
        print(format_full_dry_run_progress(event), file=sys.stderr, flush=True)

    result = dry_run_latest_full_snapshots(
        data_root=args.data_root,
        source_keys=source_keys,
        progress_every_rows=args.progress_every,
        progress=progress,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
