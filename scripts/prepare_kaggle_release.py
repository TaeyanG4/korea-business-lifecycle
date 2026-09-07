from __future__ import annotations

import argparse
import json
import os

from korea_business_lifecycle.kaggle_release import KaggleReleaseError, prepare_kaggle_release


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Prepare the verified aggregate-only Kaggle package with CSV, Parquet, source summary, "
            "schema, documentation, and hashes under data/local/."
        )
    )
    parser.add_argument("--owner", default=os.environ.get("KAGGLE_USERNAME"))
    parser.add_argument("--data-root", default=None)
    args = parser.parse_args()
    try:
        result = prepare_kaggle_release(owner=args.owner, data_root=args.data_root)
    except KaggleReleaseError as exc:
        raise SystemExit(f"Kaggle release preparation blocked: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
