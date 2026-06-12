"""Measure deterministic perft speed."""

from __future__ import annotations

import argparse
import json
import time

from harness import DEFAULT_CONFIG, base_metadata, run_engine, write_json


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--output", default="results/speed.json")
    parser.add_argument("--fen", default="startpos")
    parser.add_argument("--depth", type=int, default=5)
    args = parser.parse_args()

    start = time.perf_counter()
    completed = run_engine(args.engine, ["--perft", args.fen, str(args.depth)], config=args.config, timeout=60.0)
    elapsed = time.perf_counter() - start

    nodes = None
    passed = False
    if completed.returncode == 0:
        output = json.loads(completed.stdout)
        nodes = int(output["nodes"])
        passed = elapsed > 0

    result = {
        "benchmark": "speed",
        **base_metadata(args.engine, args.config),
        "passed": passed,
        "fen": args.fen,
        "depth": args.depth,
        "nodes": nodes,
        "elapsed_seconds": elapsed,
        "nodes_per_second": int(nodes / elapsed) if nodes is not None and elapsed > 0 else None,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "returncode": completed.returncode,
    }

    write_json(args.output, result)
    print(json.dumps(result))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
