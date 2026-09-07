from __future__ import annotations

import argparse
import json
import sys

from korea_business_lifecycle.history_nationwide import (
    PRODUCTION_NETWORK_REQUEST_CAP,
    PRODUCTION_REQUEST_DELAY_SECONDS,
    HistoryNationwideError,
    nationwide_history_acquisition_plan,
    run_nationwide_history_acquisition,
)


def _progress(event: dict) -> None:
    index = int(event.get("task_index", 0))
    total = int(event.get("task_total", 0))
    kind = str(event.get("event", "PROGRESS")).upper()
    source = str(event.get("source_key", ""))
    base_date = str(event.get("base_date", ""))
    authority = str(event.get("authority_code", ""))
    requests = int(event.get("network_requests_used", 0))
    if kind == "PAGE_COMPLETE":
        page = int(event.get("page_no", 0))
        pages = int(event.get("total_pages", 0))
        print(
            f"[{index}/{total}] PAGE {source} {base_date} {authority} {page}/{pages} requests={requests}",
            file=sys.stderr,
            flush=True,
        )
    else:
        print(
            f"[{index}/{total}] {kind} {source} {base_date} {authority} requests={requests}",
            file=sys.stderr,
            flush=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or execute the approved resumable nationwide monthly history acquisition. "
            "Without --execute, no network requests are made."
        )
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--plan", action="store_true")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--max-network-requests", type=int, default=PRODUCTION_NETWORK_REQUEST_CAP)
    parser.add_argument("--request-delay-seconds", type=float, default=PRODUCTION_REQUEST_DELAY_SECONDS)
    parser.add_argument("--max-attempts", type=int, default=3)
    parser.add_argument("--timeout-seconds", type=int, default=30)
    args = parser.parse_args()
    if args.plan:
        print(json.dumps(nationwide_history_acquisition_plan(), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    try:
        result = run_nationwide_history_acquisition(
            data_root=args.data_root,
            execute=args.execute,
            max_network_requests=args.max_network_requests,
            request_delay_seconds=args.request_delay_seconds,
            max_attempts=args.max_attempts,
            timeout_seconds=args.timeout_seconds,
            progress_callback=_progress if args.execute else None,
        )
    except HistoryNationwideError as exc:
        raise SystemExit(f"nationwide history acquisition blocked: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
