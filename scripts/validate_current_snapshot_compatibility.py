from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from korea_business_lifecycle.canonical_compatibility import (
    DEFAULT_COMPATIBILITY_ROWS,
    V1_SOURCE_ORDER,
    latest_retrieval_manifest,
    validate_snapshot_compatibility,
)
from korea_business_lifecycle.storage import resolve_data_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run a bounded, aggregate-only compatibility gate against local current snapshots."
    )
    parser.add_argument("--max-rows", type=int, default=DEFAULT_COMPATIBILITY_ROWS)
    parser.add_argument("--data-root", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = resolve_data_root(args.data_root)
    results = []
    for index, source_key in enumerate(V1_SOURCE_ORDER, start=1):
        print(
            f"[{index}/{len(V1_SOURCE_ORDER)}] START {source_key} bounded compatibility <= {args.max_rows} rows",
            file=sys.stderr,
            flush=True,
        )
        result = validate_snapshot_compatibility(
            latest_retrieval_manifest(source_key, data_root=root),
            data_root=root,
            max_rows=args.max_rows,
        )
        results.append(result)
        print(
            f"[{index}/{len(V1_SOURCE_ORDER)}] DONE {source_key} rows={result['rows_examined']} status={result['status']}",
            file=sys.stderr,
            flush=True,
        )

    summary = {
        "scope": list(V1_SOURCE_ORDER),
        "sample_policy": "HEAD_ROWS_AFTER_HEADER",
        "max_rows_per_source": args.max_rows,
        "rows_examined_total": sum(int(item["rows_examined"]) for item in results),
        "production_materialization_performed": False,
        "row_level_values_returned": False,
        "results": results,
        "status": "PASS",
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
