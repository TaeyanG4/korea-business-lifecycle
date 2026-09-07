from __future__ import annotations

import argparse
import json

from korea_business_lifecycle.episode_materialization_verify import (
    EpisodeBuildVerificationError,
    verify_production_episode_build,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Independently verify a local production lifecycle-episode build.")
    parser.add_argument("--data-root", default=None)
    parser.add_argument("--build-id", default=None)
    args = parser.parse_args()
    try:
        result = verify_production_episode_build(data_root=args.data_root, build_id=args.build_id)
    except EpisodeBuildVerificationError as exc:
        raise SystemExit(f"episode build verification failed: {exc}") from exc
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
