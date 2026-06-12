"""Run full pre-autoresearch benchmark suite and write one experiment JSON."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from harness import DEFAULT_CONFIG, base_metadata, utc_id, write_json


def run_step(name: str, command: list[str], output: str) -> dict:
    completed = subprocess.run(command + ["--output", output], check=False, capture_output=True, text=True)
    payload = None
    if Path(output).exists():
        payload = json.loads(Path(output).read_text(encoding="utf-8"))
    return {
        "name": name,
        "command": command + ["--output", output],
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "output": output,
        "result": payload,
        "passed": completed.returncode == 0 and bool(payload and payload.get("passed", payload.get("perft_passed", False))),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--opponent-engine")
    parser.add_argument("--opponent-config", default=DEFAULT_CONFIG)
    parser.add_argument("--output", default="results/latest.json")
    parser.add_argument("--experiment-id")
    args = parser.parse_args()

    experiment_id = args.experiment_id or utc_id("baseline")
    result_dir = Path("results") / experiment_id
    result_dir.mkdir(parents=True, exist_ok=True)

    steps = [
        run_step("perft", ["python", "research/run_perft.py", "--engine", args.engine, "--config", args.config], str(result_dir / "perft.json")),
        run_step("tactics", ["python", "research/run_tactics.py", "--engine", args.engine, "--config", args.config], str(result_dir / "tactics.json")),
        run_step("speed", ["python", "research/run_speed.py", "--engine", args.engine, "--config", args.config], str(result_dir / "speed.json")),
        run_step("match", [
            "python", "research/run_match.py",
            "--engine", args.engine,
            "--config", args.config,
            "--opponent-engine", args.opponent_engine or args.engine,
            "--opponent-config", args.opponent_config,
        ], str(result_dir / "match.json")),
    ]

    accepted = all(step["passed"] for step in steps)
    payload = {
        "experiment_id": experiment_id,
        **base_metadata(args.engine, args.config),
        "opponent": {
            "engine": args.opponent_engine or args.engine,
            "config": args.opponent_config,
        },
        "steps": steps,
        "accepted": accepted,
        "reason": "All correctness and smoke benchmarks passed." if accepted else "At least one benchmark failed.",
    }

    write_json(args.output, payload)
    write_json(str(result_dir / "summary.json"), payload)
    print(json.dumps(payload))
    return 0 if accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
