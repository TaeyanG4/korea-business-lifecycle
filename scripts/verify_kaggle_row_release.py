from __future__ import annotations

import argparse
import json

from korea_business_lifecycle.kaggle_row_release_verify import verify_prepared_kaggle_row_release


def main() -> int:
    parser = argparse.ArgumentParser(description="Independently verify the prepared 3,010,802-row Kaggle package")
    parser.add_argument("--data-root", default=None)
    args = parser.parse_args()
    print(json.dumps(verify_prepared_kaggle_row_release(data_root=args.data_root), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
