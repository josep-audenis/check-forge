"""Evaluate aggregate benchmark result."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result")
    args = parser.parse_args()

    result_path = Path(args.result)
    result = json.loads(result_path.read_text(encoding="utf-8"))
    accepted = bool(result.get("accepted", result.get("passed", False)))
    failed = [
        step["name"]
        for step in result.get("steps", [])
        if not step.get("passed", False)
    ]
    decision = {
        "result": str(result_path),
        "accepted": accepted,
        "failed_steps": failed,
        "reason": result.get("reason") or ("All checks passed." if accepted else "Checks failed."),
    }
    print(json.dumps(decision))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
