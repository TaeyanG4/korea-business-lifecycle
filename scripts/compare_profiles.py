from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.profiling import compare_column_sets


def main() -> int:
    parser = argparse.ArgumentParser(description="Compare exact source column sets across profiles.")
    parser.add_argument("profiles", nargs="+", help="SOURCE_KEY=profile.json")
    args = parser.parse_args()
    inputs: list[tuple[str, dict[str, object]]] = []
    for item in args.profiles:
        if "=" not in item:
            parser.error(f"invalid profile argument: {item}")
        source_key, path_text = item.split("=", 1)
        path = Path(path_text)
        profile = json.loads(path.read_text(encoding="utf-8"))
        inputs.append((source_key, profile))
    result = compare_column_sets(inputs)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
