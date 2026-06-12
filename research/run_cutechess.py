"""Run external cutechess validation when cutechess-cli is installed."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
import os

from harness import DEFAULT_CONFIG, base_metadata, write_json


def find_cutechess() -> str | None:
    found = shutil.which("cutechess-cli")
    if found:
        return found

    winget_root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if winget_root.exists():
        matches = list(winget_root.rglob("cutechess-cli.exe"))
        if matches:
            return str(matches[0])

    return None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--opponent-engine", required=True)
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--opponent-config", default=DEFAULT_CONFIG)
    parser.add_argument("--games", type=int, default=20)
    parser.add_argument("--tc", default="10+0.1")
    parser.add_argument("--output", default="results/cutechess.json")
    parser.add_argument("--pgn", default="matches/latest.pgn")
    args = parser.parse_args()

    cutechess = find_cutechess()
    if not cutechess:
        result = {
            "benchmark": "cutechess",
            **base_metadata(args.engine, args.config),
            "passed": False,
            "skipped": True,
            "reason": "cutechess-cli not found on PATH",
        }
        write_json(args.output, result)
        print(json.dumps(result))
        return 2

    Path(args.pgn).parent.mkdir(parents=True, exist_ok=True)
    engine_path = str(Path(args.engine).resolve())
    opponent_path = str(Path(args.opponent_engine).resolve())
    config_path = str(Path(args.config).resolve())
    opponent_config_path = str(Path(args.opponent_config).resolve())
    command = [
        cutechess,
        "-engine", f"cmd={engine_path}", "arg=--config", f"arg={config_path}", "arg=uci", "proto=uci", "name=checkforge",
        "-engine", f"cmd={opponent_path}", "arg=--config", f"arg={opponent_config_path}", "arg=uci", "proto=uci", "name=opponent",
        "-each", f"tc={args.tc}",
        "-games", str(args.games),
        "-pgnout", args.pgn,
    ]
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    combined = completed.stdout + "\n" + completed.stderr
    lowered = combined.lower()
    passed = (
        completed.returncode == 0
        and "disconnects" not in lowered
        and "illegal" not in lowered
        and "could not initialize" not in lowered
        and "error" not in lowered
    )
    result = {
        "benchmark": "cutechess",
        **base_metadata(args.engine, args.config),
        "opponent": {"engine": args.opponent_engine, "config": args.opponent_config},
        "passed": passed,
        "skipped": False,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "pgn": args.pgn,
    }
    write_json(args.output, result)
    print(json.dumps(result))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
