from __future__ import annotations

import json

from korea_business_lifecycle.history_observation_strategy import history_observation_strategy_plan


def main() -> None:
    print(json.dumps(history_observation_strategy_plan(), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
