"""Run core perft correctness checks."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from harness import DEFAULT_CONFIG, base_metadata

CASES = [
    ("startpos", 1, 20),
    ("startpos", 2, 400),
    ("startpos", 3, 8902),
    ("startpos", 4, 197281),
    ("startpos", 5, 4865609),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 1, 48),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", 2, 2039),
]


def run_case(engine: str, config: str, fen: str, depth: int, expected: int) -> dict:
    completed = subprocess.run(
        [engine, "--config", config, "--perft", fen, str(depth)],
        check=False,
        capture_output=True,
        text=True,
    )

    if completed.returncode != 0:
        return {
            "fen": fen,
            "depth": depth,
            "expected": expected,
            "passed": False,
            "error": completed.stderr.strip(),
        }

    output = json.loads(completed.stdout)
    actual = output["nodes"]
    return {
        "fen": fen,
        "depth": depth,
        "expected": expected,
        "actual": actual,
        "passed": actual == expected,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--output", default="results/latest.json")
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    cases = [run_case(args.engine, args.config, fen, depth, expected) for fen, depth, expected in CASES]
    perft_passed = all(case["passed"] for case in cases)

    result = {
        "benchmark": "perft",
        **base_metadata(args.engine, args.config),
        "perft_passed": perft_passed,
        "passed": perft_passed,
        "cases": cases,
    }

    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0 if perft_passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
