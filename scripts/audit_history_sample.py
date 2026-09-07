from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.artifacts import sha256_file
from korea_business_lifecycle.history_audit import (
    HistoryAuditError,
    compare_history_snapshots,
    summarize_history_audits,
)
from korea_business_lifecycle.provenance import V1_SOURCE_KEYS
from korea_business_lifecycle.storage import resolve_data_root


def _single_snapshot_dir(
    root: Path,
    *,
    source_key: str,
    base_date: str,
    authority_code: str,
) -> Path:
    parent = root / "history" / source_key / base_date / authority_code
    manifests = sorted(parent.glob("*/manifest.json")) if parent.is_dir() else []
    if len(manifests) != 1:
        raise HistoryAuditError(
            f"expected exactly one snapshot for {source_key}/{base_date}/{authority_code}; "
            f"found {len(manifests)}"
        )
    return manifests[0].parent


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit a bounded multi-authority history sample using aggregate-only output."
    )
    parser.add_argument("--authority", action="append", required=True)
    parser.add_argument("--start-date", default="20260101")
    parser.add_argument("--end-date", default="20260906")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--output", type=Path, default=None)
    args = parser.parse_args()

    root = resolve_data_root(args.data_root)
    audits: list[dict] = []
    for authority in sorted(set(args.authority)):
        for source in sorted(V1_SOURCE_KEYS):
            start = _single_snapshot_dir(
                root,
                source_key=source,
                base_date=args.start_date,
                authority_code=authority,
            )
            end = _single_snapshot_dir(
                root,
                source_key=source,
                base_date=args.end_date,
                authority_code=authority,
            )
            audit = compare_history_snapshots(start, end)
            audit["evidence"] = {
                "start_manifest_sha256": sha256_file(start / "manifest.json"),
                "end_manifest_sha256": sha256_file(end / "manifest.json"),
            }
            audits.append(audit)

    payload = {
        "sample": summarize_history_audits(audits),
        "audits": sorted(audits, key=lambda item: (item["authority_code"], item["source_key"])),
    }
    rendered = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
