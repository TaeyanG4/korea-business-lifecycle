from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.authority_domain import build_authority_domain_reference
from korea_business_lifecycle.storage import resolve_data_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Parse the official authority-code workbook and compare its current numeric domain "
            "with the verified local PERMIT build."
        )
    )
    parser.add_argument("--reference-xlsx", type=Path, default=None)
    parser.add_argument("--data-root", type=Path, default=None)
    parser.add_argument("--build-id", default=None)
    parser.add_argument("--output", type=Path, default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = resolve_data_root(args.data_root)
    reference = args.reference_xlsx or (
        root / "reference" / "official-authority-status-20260702.xlsx"
    )
    result = build_authority_domain_reference(
        reference_xlsx=reference,
        data_root=root,
        build_id=args.build_id,
    )
    payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output is None:
        print(payload, end="")
    else:
        output = args.output.expanduser().resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(payload, encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
