from __future__ import annotations

import argparse
import json

from korea_business_lifecycle.history_sample_runner import (
    HistorySampleRunnerError,
    run_history_sample,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or execute the tracked four-authority history expansion sample. "
            "Without --execute this command performs no network acquisition."
        )
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--max-requests", type=int, default=2500)
    parser.add_argument("--request-delay-seconds", type=float, default=0.2)
    args = parser.parse_args()
    try:
        result = run_history_sample(
            data_root=args.data_root,
            execute=args.execute,
            max_requests=args.max_requests,
            request_delay_seconds=args.request_delay_seconds,
        )
    except HistorySampleRunnerError as exc:
        raise SystemExit(f"history sample blocked: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
