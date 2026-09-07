from __future__ import annotations

import argparse
import json

from korea_business_lifecycle.history_probe import probe_history
from korea_business_lifecycle.provenance import V1_SOURCE_KEYS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one authenticated v1 history page-1 probe. The data.go.kr service key "
            "is read only from KBL_DATA_GO_KR_SERVICE_KEY and is never printed."
        )
    )
    parser.add_argument("source_key", choices=sorted(V1_SOURCE_KEYS))
    parser.add_argument("base_date", help="YYYYMMDD, official range starts at 20260101")
    parser.add_argument("authority_code", help="observed 7-digit 개방자치단체코드")
    parser.add_argument("--num-rows", type=int, default=1)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = probe_history(
        args.source_key,
        base_date=args.base_date,
        authority_code=args.authority_code,
        num_rows=args.num_rows,
        timeout_seconds=args.timeout_seconds,
    )
    print(json.dumps(result.as_dict(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
