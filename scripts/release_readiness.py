from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.release_readiness import compute_release_readiness


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute aggregate-only release-readiness gates.")
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    payload = json.dumps(
        compute_release_readiness(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.write_text(payload, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
