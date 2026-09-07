from __future__ import annotations

import argparse
import json
from pathlib import Path

from korea_business_lifecycle.artifacts import build_artifact_manifest
from korea_business_lifecycle.config import project_root
from korea_business_lifecycle.profiling import profile_csv
from korea_business_lifecycle.provenance import V1_SOURCE_KEYS
from korea_business_lifecycle.storage import require_external_artifact, resolve_data_root


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Profile an already-downloaded v1 CSV artifact without network access."
    )
    parser.add_argument("source_key", choices=sorted(V1_SOURCE_KEYS))
    parser.add_argument("artifact")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--distinct-cap", type=int, default=10_000)
    parser.add_argument("--top-n", type=int, default=20)
    parser.add_argument("--type-probe-cap", type=int, default=10_000)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = resolve_data_root(args.data_root)
    artifact = require_external_artifact(args.artifact, root)
    profile = profile_csv(
        artifact,
        distinct_cap=args.distinct_cap,
        top_n=args.top_n,
        type_probe_cap=args.type_probe_cap,
    )
    manifest = build_artifact_manifest(
        source_key=args.source_key,
        path=artifact,
        project_root=project_root(),
        observed={
            "encoding": profile["encoding"],
            "delimiter": profile["dialect"]["delimiter"],
            "column_count": profile["header"]["column_count"],
            "data_row_count": profile["rows"]["parsed_data_rows"],
        },
    )

    output_dir = root / "staging" / "profiles" / args.source_key / manifest["artifact"]["sha256"]
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (output_dir / "profile.json").write_text(
        json.dumps(profile, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(output_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
