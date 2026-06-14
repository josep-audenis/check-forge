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
    parser.add_argument("--games", type=int, default=200)
    parser.add_argument("--tc", default="10+0.1")
    parser.add_argument("--output", default="results/cutechess.json")
    parser.add_argument("--pgn", default="matches/latest.pgn")
    parser.add_argument("--openings", default="data/openings.epd",
                        help="EPD opening file for varied starts; pass '' to play from startpos")
    parser.add_argument("--detach", action="store_true",
                        help="Launch cutechess fully detached (survives parent/job termination) "
                             "and return immediately. Poll the PGN and score with score_pgn.py.")
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

    # Varied openings make two deterministic engines diverge so games can be decisive.
    # Without this, identical/near-identical clones draw every game by 3-fold repetition.
    openings_path = Path(args.openings) if args.openings else None
    if openings_path and openings_path.exists():
        command += [
            "-openings", f"file={openings_path.resolve()}", "format=epd", "order=random",
            "-repeat",
        ]
    if args.detach:
        # Long matches were being killed mid-run when the harness reaped the background
        # process tree (job-object kill) / on Windows idle. Break the child away from the
        # parent's job and console so it keeps running independently; its PGN is the
        # ground-truth record (score with research/score_pgn.py).
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_BREAKAWAY_FROM_JOB = 0x01000000
        flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB
        log_path = str(Path(args.pgn).with_suffix(".cutechess.log"))
        with open(log_path, "w", encoding="utf-8") as log:
            proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
        info = {
            "benchmark": "cutechess", "detached": True, "pid": proc.pid,
            "pgn": args.pgn, "log": log_path, "games_requested": args.games,
            "note": "detached match; poll PGN + score with research/score_pgn.py",
        }
        write_json(args.output, info)
        print(json.dumps(info))
        return 0

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
    # Derive W-L-D / Elo from the PGN (ground truth), so the structured result survives
    # even if cutechess stdout is unusual. See research/score_pgn.py.
    try:
        from score_pgn import score_pgn
        scored = score_pgn(args.pgn, "checkforge")
    except Exception as exc:  # never let scoring failure lose the run record
        scored = {"error": str(exc)}

    result = {
        "benchmark": "cutechess",
        **base_metadata(args.engine, args.config),
        "opponent": {"engine": args.opponent_engine, "config": args.opponent_config},
        "passed": passed,
        "skipped": False,
        "results": scored,
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
