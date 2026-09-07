from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from korea_business_lifecycle.kaggle_regional_market import build_regional_market_notebook  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the Kaggle regional food-service market notebook")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(build_regional_market_notebook(), ensure_ascii=False, indent=1) + "\n",
        encoding="utf-8",
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
