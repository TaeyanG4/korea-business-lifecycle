from __future__ import annotations

import argparse
import json
import sys

from korea_business_lifecycle.history_acquisition import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MAX_PAGES,
    DEFAULT_TIMEOUT_SECONDS,
    HistoryAcquisitionError,
    acquire_history_snapshot,
)
from korea_business_lifecycle.history_progress import format_history_progress
from korea_business_lifecycle.provenance import V1_SOURCE_KEYS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Acquire one bounded history snapshot for one v1 source, date and authority code. "
            "The service key is never written to output or manifests."
        )
    )
    parser.add_argument("source_key", choices=sorted(V1_SOURCE_KEYS))
    parser.add_argument("base_date", help="YYYYMMDD")
    parser.add_argument("authority_code", help="7-digit observed OPN_ATMY_GRP_CD")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--max-pages", type=int, default=DEFAULT_MAX_PAGES)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    def progress(event: dict) -> None:
        print(
            format_history_progress({**event, "task_index": 1, "task_total": 1}),
            file=sys.stderr,
            flush=True,
        )

    progress(
        {
            "event": "task_start",
            "source_key": args.source_key,
            "authority_code": args.authority_code,
            "base_date": args.base_date,
            "max_pages": args.max_pages,
        }
    )
    try:
        result = acquire_history_snapshot(
            args.source_key,
            base_date=args.base_date,
            authority_code=args.authority_code,
            data_root=args.data_root,
            max_pages=args.max_pages,
            max_attempts=args.max_attempts,
            timeout_seconds=args.timeout_seconds,
            progress_callback=progress,
        )
    except HistoryAcquisitionError as exc:
        raise SystemExit(f"history acquisition blocked: {exc}") from exc
    progress(
        {
            "event": "task_complete",
            "source_key": args.source_key,
            "authority_code": args.authority_code,
            "base_date": args.base_date,
            "finished_tasks": 1,
            "observed_rows": result.manifest["observed"]["total_count"],
            "observed_pages": result.manifest["observed"]["total_pages"],
        }
    )
    print(
        json.dumps(
            {
                "snapshot_dir": str(result.snapshot_dir),
                "manifest": str(result.manifest_path),
                "total_count": result.manifest["observed"]["total_count"],
                "total_pages": result.manifest["observed"]["total_pages"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
