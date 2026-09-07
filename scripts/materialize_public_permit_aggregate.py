from __future__ import annotations

import argparse
import json
import sys

from korea_business_lifecycle.public_aggregate import (
    format_public_aggregate_progress,
    materialize_public_permit_aggregate,
    public_aggregate_plan,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a local privacy-minimized permit aggregate candidate")
    parser.add_argument("--execute", action="store_true", help="run the full local parent scan and materialize output")
    parser.add_argument("--data-root")
    args = parser.parse_args()
    if not args.execute:
        print(json.dumps(public_aggregate_plan(data_root=args.data_root), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    def progress(event: dict[str, object]) -> None:
        print(format_public_aggregate_progress(event), file=sys.stderr, flush=True)

    result = materialize_public_permit_aggregate(data_root=args.data_root, progress=progress)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
