from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.history_audit import compare_history_snapshots


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Audit one bounded history pair and emit aggregate-only identity/lifecycle evidence. "
            "No MNG_NO, business name, address or coordinate values are emitted."
        )
    )
    parser.add_argument("start_dir", type=Path)
    parser.add_argument("end_dir", type=Path)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    result = compare_history_snapshots(args.start_dir, args.end_dir)
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
