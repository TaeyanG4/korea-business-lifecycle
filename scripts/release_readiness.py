from __future__ import annotations

import json

from korea_business_lifecycle.release_readiness import compute_release_readiness


def main() -> int:
    print(json.dumps(compute_release_readiness(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
