"""Run fixed tactical bestmove checks."""

from __future__ import annotations

import argparse
import json

from harness import DEFAULT_CONFIG, base_metadata, run_engine, write_json


CASES = [
    {
        "id": "free-queen",
        "fen": "4k3/8/8/8/4q3/8/4R3/4K3 w - - 0 1",
        "depth": 1,
        "expected": ["e2e4"],
    },
    {
        "id": "free-rook",
        "fen": "4k3/8/8/8/4r3/3B4/8/4K3 w - - 0 1",
        "depth": 1,
        "expected": ["d3e4"],
    },
    {
        "id": "mate-back-rank",
        "fen": "6k1/5ppp/8/8/8/8/8/R3K3 w - - 0 1",
        "depth": 3,
        "expected": ["a1a8"],
    },
    {
        "id": "mate-scholars-qf7",
        "fen": "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5Q2/PPPP1PPP/RNB1K1NR w KQkq - 0 1",
        "depth": 3,
        "expected": ["f3f7"],
    },
    {
        "id": "win-bishop-rxd3",
        "fen": "4k3/8/8/8/8/3b4/3R4/4K3 w - - 0 1",
        "depth": 2,
        "expected": ["d2d3"],
    },
    {
        "id": "win-rook-fork-nxe6",
        "fen": "4k3/8/4r3/8/3N4/8/8/4K3 w - - 0 1",
        "depth": 3,
        "expected": ["d4e6"],
    },
    {
        "id": "win-knight-rxd5",
        "fen": "4k3/8/8/3n4/8/8/3R4/4K3 w - - 0 1",
        "depth": 2,
        "expected": ["d2d5"],
    },
    {
        "id": "royal-fork-nc7",
        "fen": "r3k3/8/8/3N4/8/8/8/4K3 w - - 0 1",
        "depth": 3,
        "expected": ["d5c7"],
    },
]


def run_case(engine: str, config: str, case: dict) -> dict:
    completed = run_engine(engine, ["--bestmove", case["fen"], "--depth", str(case["depth"])], config=config)
    bestmove = None
    if completed.returncode == 0:
        parts = completed.stdout.strip().split()
        if len(parts) >= 2 and parts[0] == "bestmove":
            bestmove = parts[1]

    return {
        "id": case["id"],
        "fen": case["fen"],
        "depth": case["depth"],
        "expected": case["expected"],
        "actual": bestmove,
        "passed": bestmove in case["expected"],
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--output", default="results/tactics.json")
    args = parser.parse_args()

    cases = [run_case(args.engine, args.config, case) for case in CASES]
    result = {
        "benchmark": "tactics",
        **base_metadata(args.engine, args.config),
        "passed": all(case["passed"] for case in cases),
        "solved": sum(1 for case in cases if case["passed"]),
        "total": len(cases),
        "cases": cases,
    }

    write_json(args.output, result)
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
