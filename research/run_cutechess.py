"""Run external cutechess validation when cutechess-cli is installed."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
import os

try:
    from harness import (
        DEFAULT_CONFIG,
        base_metadata,
        command_version,
        executable_metadata,
        file_metadata,
        prepare_opening_schedule,
        write_json,
    )
except ModuleNotFoundError:
    from research.harness import (
        DEFAULT_CONFIG,
        base_metadata,
        command_version,
        executable_metadata,
        file_metadata,
        prepare_opening_schedule,
        write_json,
    )
try:
    from score_pgn import score_pgn
except ModuleNotFoundError:
    from research.score_pgn import score_pgn


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
    parser.add_argument("--seed", type=int, default=1,
                        help="Cute Chess RNG seed; recorded for reproducibility")
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--min-openings", type=int, default=1,
                        help="Reject an opening file with fewer semantic EPD positions")
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--sprt-elo0", type=float, default=None)
    parser.add_argument("--sprt-elo1", type=float, default=None)
    parser.add_argument("--sprt-alpha", type=float, default=0.05)
    parser.add_argument("--sprt-beta", type=float, default=0.05)
    parser.add_argument("--detach", action="store_true",
                        help="Launch cutechess fully detached (survives parent/job termination) "
                             "and return immediately. Poll the PGN and score with score_pgn.py.")
    args = parser.parse_args()

    if args.games <= 0:
        parser.error("--games must be positive")
    if args.concurrency <= 0:
        parser.error("--concurrency must be positive")
    if args.min_openings < 0:
        parser.error("--min-openings cannot be negative")
    if not 0.0 < args.confidence < 1.0:
        parser.error("--confidence must be between 0 and 1")
    if (args.sprt_elo0 is None) != (args.sprt_elo1 is None):
        parser.error("--sprt-elo0 and --sprt-elo1 must be provided together")
    if args.sprt_elo0 is not None and args.sprt_elo0 >= args.sprt_elo1:
        parser.error("--sprt-elo0 must be less than --sprt-elo1")
    if not 0.0 < args.sprt_alpha < 1.0 or not 0.0 < args.sprt_beta < 1.0:
        parser.error("SPRT alpha and beta must be between 0 and 1")
    if args.sprt_alpha + args.sprt_beta >= 1.0:
        parser.error("SPRT alpha + beta must be less than 1")

    sprt = None
    if args.sprt_elo0 is not None:
        sprt = {
            "elo0": args.sprt_elo0,
            "elo1": args.sprt_elo1,
            "alpha": args.sprt_alpha,
            "beta": args.sprt_beta,
        }

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

    openings_path = Path(args.openings) if args.openings else None
    if sprt and not openings_path:
        parser.error("paired sequential testing requires --openings")
    if sprt and args.concurrency != 1:
        parser.error("paired sequential testing requires --concurrency 1 to preserve pair order")
    openings_meta = file_metadata(args.openings, count_nonempty_lines=True) if args.openings else None
    if openings_path and not openings_path.is_file():
        result = {
            "benchmark": "cutechess",
            **base_metadata(args.engine, args.config),
            "passed": False,
            "skipped": False,
            "reason": f"opening file not found: {args.openings}",
            "openings": openings_meta,
        }
        write_json(args.output, result)
        print(json.dumps(result))
        return 2
    opening_count = int((openings_meta or {}).get("unique_positions", 0))
    if openings_path and opening_count < args.min_openings:
        result = {
            "benchmark": "cutechess",
            **base_metadata(args.engine, args.config),
            "passed": False,
            "skipped": False,
            "reason": f"opening suite has {opening_count} unique positions; require {args.min_openings}",
            "openings": openings_meta,
        }
        write_json(args.output, result)
        print(json.dumps(result))
        return 2
    require_pairs = bool(openings_path)
    if require_pairs and args.games % 2:
        parser.error("--games must be even when paired openings are enabled")

    Path(args.pgn).parent.mkdir(parents=True, exist_ok=True)
    engine_path = str(Path(args.engine).resolve())
    opponent_path = str(Path(args.opponent_engine).resolve())
    config_path = str(Path(args.config).resolve())
    opponent_config_path = str(Path(args.opponent_config).resolve())
    pgn_path = str(Path(args.pgn).resolve())
    opening_schedule = None
    schedule_path = None
    if openings_path:
        schedule_path = str(Path(args.pgn).with_suffix(".openings.epd").resolve())
        opening_schedule = prepare_opening_schedule(
            str(openings_path), schedule_path, pairs=args.games // 2, seed=args.seed
        )
    command = [
        cutechess,
        "-engine", f"cmd={engine_path}", "arg=--config", f"arg={config_path}", "arg=uci", "proto=uci", "name=checkforge",
        "-engine", f"cmd={opponent_path}", "arg=--config", f"arg={opponent_config_path}", "arg=uci", "proto=uci", "name=opponent",
        "-each", f"tc={args.tc}",
        "-concurrency", str(args.concurrency),
        "-srand", str(args.seed),
        "-games", str(args.games),
        "-pgnout", pgn_path,
    ]

    # Varied openings make two deterministic engines diverge so games can be decisive.
    # Without this, identical/near-identical clones draw every game by 3-fold repetition.
    if schedule_path:
        command += [
            "-openings", f"file={schedule_path}", "format=epd", "order=sequential",
            "-repeat",
        ]
    reproducibility = {
        "cutechess": executable_metadata(
            cutechess, version=command_version(cutechess, "-version")
        ),
        "opponent_artifact": executable_metadata(opponent_path),
        "opponent_config": file_metadata(opponent_config_path),
        "openings": openings_meta,
        "opening_schedule": opening_schedule,
        "seed": args.seed,
        "concurrency": args.concurrency,
        "time_control": args.tc,
        "games_max": args.games,
        "paired_openings": require_pairs,
        "confidence": args.confidence,
        "sprt": sprt,
    }
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
            **base_metadata(args.engine, args.config),
            "pgn": pgn_path, "log": log_path, "games_requested": args.games,
            "command": command, "reproducibility": reproducibility,
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
        scored = score_pgn(
            pgn_path,
            "checkforge",
            confidence=args.confidence,
            expected_games=args.games,
            require_pairs=require_pairs,
            sprt=sprt,
            opening_schedule=schedule_path,
        )
    except Exception as exc:  # never let scoring failure lose the run record
        scored = {"error": str(exc)}

    result = {
        "benchmark": "cutechess",
        **base_metadata(args.engine, args.config),
        "opponent": {"engine": args.opponent_engine, "config": args.opponent_config},
        "passed": passed and bool(scored.get("valid", False)),
        "measurement_valid": passed and bool(scored.get("valid", False)),
        "skipped": False,
        "results": scored,
        "sequential_test": scored.get("sprt"),
        "reproducibility": reproducibility,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "pgn": pgn_path,
    }
    write_json(args.output, result)
    print(json.dumps(result))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
