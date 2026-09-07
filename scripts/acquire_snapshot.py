from __future__ import annotations

import argparse
import json

from korea_business_lifecycle.acquisition import (
    DEFAULT_MAX_ATTEMPTS,
    DEFAULT_MAX_DOWNLOAD_BYTES,
    DEFAULT_MIN_FREE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    acquire_current_snapshot,
)
from korea_business_lifecycle.provenance import V1_SOURCE_KEYS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Acquire one current official v1 bulk snapshot into external KBL_DATA_ROOT. "
            "This command never requests history and never writes source data into Git."
        )
    )
    parser.add_argument("source_key", choices=sorted(V1_SOURCE_KEYS))
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--min-free-gb", type=float, default=DEFAULT_MIN_FREE_BYTES / 1024**3)
    parser.add_argument("--max-attempts", type=int, default=DEFAULT_MAX_ATTEMPTS)
    parser.add_argument("--timeout-seconds", type=int, default=DEFAULT_TIMEOUT_SECONDS)
    parser.add_argument(
        "--max-download-gb",
        type=float,
        default=DEFAULT_MAX_DOWNLOAD_BYTES / 1024**3,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.min_free_gb < 0:
        raise SystemExit("--min-free-gb must be non-negative")
    if args.max_download_gb <= 0:
        raise SystemExit("--max-download-gb must be positive")
    result = acquire_current_snapshot(
        args.source_key,
        data_root=args.data_root,
        min_free_bytes=int(args.min_free_gb * 1024**3),
        max_attempts=args.max_attempts,
        timeout_seconds=args.timeout_seconds,
        max_download_bytes=int(args.max_download_gb * 1024**3),
    )
    print(
        json.dumps(
            {
                "artifact": str(result.artifact_path),
                "manifest": str(result.manifest_path),
                "sha256": result.manifest["artifact"]["sha256"],
                "bytes": result.manifest["artifact"]["bytes"],
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
