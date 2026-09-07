from __future__ import annotations

import argparse
import json
import sys

from korea_business_lifecycle.history_authority_semantics import (
    EXPECTED_TASK_COUNT,
    HistoryAuthoritySemanticsError,
    run_deleted_authority_count_probe,
)


def _progress(event: dict) -> None:
    if event.get("event") != "task_complete":
        return
    print(
        f"[{event['task_index']}/{event['task_total']}] "
        f"{event['source_key']} {event['authority_code']} {event['base_date']} "
        f"totalCount={event['total_count']}",
        file=sys.stderr,
        flush=True,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or execute the exact 32-deleted-authority count-only history probe. "
            "Without --execute no network requests are made and no row values are emitted."
        )
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--max-requests", type=int, default=EXPECTED_TASK_COUNT)
    parser.add_argument("--request-delay-seconds", type=float, default=0.2)
    args = parser.parse_args()
    try:
        result = run_deleted_authority_count_probe(
            execute=args.execute,
            max_requests=args.max_requests,
            request_delay_seconds=args.request_delay_seconds,
            progress_callback=_progress if args.execute else None,
        )
    except HistoryAuthoritySemanticsError as exc:
        raise SystemExit(f"deleted-authority semantics probe blocked: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
