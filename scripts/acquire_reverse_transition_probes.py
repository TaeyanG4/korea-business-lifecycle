from __future__ import annotations

import argparse
import json

from korea_business_lifecycle.history_transition_runner import (
    HistoryTransitionRunnerError,
    run_transition_probe_batch,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Plan or execute the six-snapshot reverse-transition follow-up. "
            "Without --execute this performs no network requests."
        )
    )
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--max-requests", type=int, default=450)
    parser.add_argument("--request-delay-seconds", type=float, default=0.2)
    args = parser.parse_args()
    try:
        result = run_transition_probe_batch(
            data_root=args.data_root,
            execute=args.execute,
            max_requests=args.max_requests,
            request_delay_seconds=args.request_delay_seconds,
        )
    except HistoryTransitionRunnerError as exc:
        raise SystemExit(f"reverse-transition probe blocked: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

