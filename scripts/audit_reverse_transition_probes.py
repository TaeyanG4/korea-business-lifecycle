from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.history_transition_audit import (
    HistoryTransitionAuditError,
    audit_reverse_transition_windows,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit the tracked three-date reverse-transition windows without emitting row values."
    )
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()
    try:
        result = audit_reverse_transition_windows(data_root=args.data_root)
    except HistoryTransitionAuditError as exc:
        raise SystemExit(f"reverse-transition audit blocked: {exc}") from exc
    rendered = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

