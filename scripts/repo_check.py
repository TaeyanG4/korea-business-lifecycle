from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FORBIDDEN_BASENAMES = {"AGENTS.md", "SKILL.md", "CLAUDE.md"}
FORBIDDEN_TRACKED_PREFIXES = ("data/local/",)


def tracked_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def violations(paths: list[str]) -> list[str]:
    found: list[str] = []
    for path in paths:
        name = Path(path).name
        if name in FORBIDDEN_BASENAMES:
            found.append(path)
        for prefix in FORBIDDEN_TRACKED_PREFIXES:
            if path.startswith(prefix):
                found.append(path)
    return sorted(set(found))


def main() -> int:
    found = violations(tracked_files())
    if found:
        print("Repository hygiene violations:")
        for path in found:
            print(f"- {path}")
        return 1
    print("Repository hygiene check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
