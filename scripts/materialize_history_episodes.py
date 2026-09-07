from __future__ import annotations

import argparse
import json

from korea_business_lifecycle.episode_materialization import (
    EpisodeMaterializationError,
    materialize_production_history_episodes,
    production_episode_preflight,
)


def _progress(event: dict) -> None:
    import sys

    kind = str(event.get("event", "PROGRESS")).upper()
    if kind.startswith("SNAPSHOT"):
        print(
            f"[{event.get('task_index', 0)}/{event.get('task_total', 0)}] {kind} "
            f"{event.get('source_key', '')} {event.get('base_date', '')} {event.get('authority_code', '')} "
            f"observations={event.get('observation_rows', 0)}",
            file=sys.stderr,
            flush=True,
        )
    elif kind == "BUCKET_COMPLETE":
        print(
            f"BUCKET {event.get('source_key', '')} {event.get('bucket', 0)}/{event.get('bucket_total', 0)} "
            f"episodes={event.get('episode_rows', 0)} observations={event.get('observation_rows', 0)}",
            file=sys.stderr,
            flush=True,
        )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize production PERMIT_STATUS_EPISODE from the complete approved monthly history snapshot set."
    )
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            production_episode_preflight(data_root=args.data_root)
            if args.preflight
            else materialize_production_history_episodes(data_root=args.data_root, progress_callback=_progress)
        )
    except EpisodeMaterializationError as exc:
        raise SystemExit(f"episode materialization blocked: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
