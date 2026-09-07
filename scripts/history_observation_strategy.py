from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.history_observation_strategy import history_observation_strategy_plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Compute network-free nationwide history observation cost scenarios."
    )
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = json.dumps(
        history_observation_strategy_plan(),
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        args.output.write_text(payload, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    main()
