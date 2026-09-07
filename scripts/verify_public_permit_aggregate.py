from __future__ import annotations

import argparse
import json

from korea_business_lifecycle.public_aggregate_verify import verify_public_permit_aggregate


def main() -> int:
    parser = argparse.ArgumentParser(description="Independently verify the local public permit aggregate candidate")
    parser.add_argument("--data-root")
    args = parser.parse_args()
    result = verify_public_permit_aggregate(data_root=args.data_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
