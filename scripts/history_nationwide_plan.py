from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.history_nationwide import nationwide_history_acquisition_plan


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the network-free approved nationwide history acquisition plan.")
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    payload = json.dumps(nationwide_history_acquisition_plan(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(payload, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
