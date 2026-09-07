from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.artifacts import sha256_file
from korea_business_lifecycle.provenance import V1_SOURCE_KEYS
from korea_business_lifecycle.snapshot_audit import audit_snapshot, retrieval_date_from_manifest
from korea_business_lifecycle.storage import require_external_artifact, resolve_data_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Audit current-snapshot grain/key/closure contradictions without creating lifecycle labels."
    )
    parser.add_argument("source_key", choices=sorted(V1_SOURCE_KEYS))
    parser.add_argument("artifact")
    parser.add_argument("--data-root", default=None)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = resolve_data_root(args.data_root)
    artifact = require_external_artifact(args.artifact, root)
    manifest_path = artifact.parent / "retrieval.json"
    if not manifest_path.is_file():
        raise SystemExit(f"retrieval manifest not found: {manifest_path}")
    retrieval_date = retrieval_date_from_manifest(manifest_path)
    sha256 = sha256_file(artifact)
    output_dir = root / "staging" / "audits" / args.source_key / sha256
    output_dir.mkdir(parents=True, exist_ok=True)
    sqlite_path = output_dir / "audit-work.sqlite"
    audit = audit_snapshot(
        artifact,
        retrieval_date=retrieval_date,
        sqlite_path=sqlite_path,
    )
    if sqlite_path.exists():
        sqlite_path.unlink()
    output_path = output_dir / "audit.json"
    output_path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
