from __future__ import annotations

import argparse
import json
import os

from korea_business_lifecycle.kaggle_row_release import KaggleRowReleaseError, prepare_kaggle_row_release


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepare approved 3,010,802-row canonical PERMIT Kaggle release in CSV and Parquet")
    parser.add_argument("--owner", default=os.environ.get("KAGGLE_USERNAME") or "taeyangg4")
    parser.add_argument("--data-root", default=None)
    args = parser.parse_args()
    try:
        result = prepare_kaggle_row_release(owner=args.owner, data_root=args.data_root)
    except KaggleRowReleaseError as exc:
        raise SystemExit(f"Kaggle row-level release preparation blocked: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
