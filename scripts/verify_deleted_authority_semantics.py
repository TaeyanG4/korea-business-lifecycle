from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.history_authority_semantics import (
    HistoryAuthoritySemanticsError,
    verify_completed_deleted_authority_probe,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Verify a completed 384-request deleted-authority count-only probe. "
            "Only aggregate verification output is printed."
        )
    )
    parser.add_argument("input", type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(args.input.read_text(encoding="utf-8"))
        summary = verify_completed_deleted_authority_probe(payload)
    except (OSError, json.JSONDecodeError, HistoryAuthoritySemanticsError) as exc:
        raise SystemExit(f"deleted-authority probe verification failed: {exc}") from exc
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
