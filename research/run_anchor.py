"""Measure CheckForge's ABSOLUTE Elo against a known-rated anchor opponent.

Until this script existed, every CheckForge match was version-vs-version, so no
absolute rating could be stated. Here the opponent is Stockfish pinned to a known
strength via ``UCI_LimitStrength`` + ``UCI_Elo``. cutechess-cli reports the Elo
difference between the two engines; CheckForge's absolute Elo is then simply

    checkforge_elo = anchor_elo + elo_difference

The anchor is *tunable*: set ``--anchor-elo`` near CheckForge's expected level so the
match scores close to 50%. A near-50% score gives the tightest error bars; a saturated
(near 0% or 100%) score barely constrains the estimate.

Stockfish's documented ``UCI_Elo`` floor is 1320 (SF16+), so anchors below that are not
available through this knob.
"""

from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
from pathlib import Path

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


def find_stockfish() -> str | None:
    found = shutil.which("stockfish")
    if found:
        return found
    winget_root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if winget_root.exists():
        matches = sorted(winget_root.rglob("stockfish-windows-*.exe"))
        # Prefer avx2 build when present.
        for m in matches:
            if "avx2" in m.name:
                return str(m)
        if matches:
            return str(matches[0])
    return None


def parse_results(text: str) -> dict:
    """Pull score (W-L-D from CheckForge's perspective) and Elo difference."""
    out: dict = {}
    # cutechess prints a running score after every game; take the final one.
    scores = re.findall(r"Score of \S+ vs \S+:\s*(\d+)\s*-\s*(\d+)\s*-\s*(\d+)", text)
    if scores:
        wins, losses, draws = (int(v) for v in scores[-1])
        out["wins"], out["losses"], out["draws"] = wins, losses, draws
        out["games"] = wins + losses + draws
    elos = re.findall(r"Elo difference:\s*(-?[\d.]+)\s*\+/-\s*([\d.]+|nan|inf)", text)
    if elos:
        diff, err = elos[-1]
        out["elo_difference"] = float(diff)
        out["elo_error"] = None if err in ("nan", "inf") else float(err)
    los = re.findall(r"LOS:\s*([\d.]+)\s*%", text)
    if los:
        out["los_percent"] = float(los[-1])
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True, help="CheckForge engine under test")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--anchor-engine", default=None,
                        help="Path to anchor engine (Stockfish). Auto-detected if omitted.")
    parser.add_argument("--anchor-elo", type=float, default=1500.0,
                        help="Known Elo to pin the anchor to (UCI_Elo). Floor 1320 for Stockfish.")
    parser.add_argument("--anchor-name", default=None)
    parser.add_argument("--anchor-family", default=None,
                        help="Independent engine/codebase family used by aggregation gates")
    parser.add_argument("--anchor-option", action="append", default=[], metavar="NAME=VALUE",
                        help="Additional UCI option sent to anchor; repeatable")
    parser.add_argument("--anchor-no-default-options", action="store_true",
                        help="Do not send Stockfish UCI_LimitStrength/UCI_Elo defaults")
    parser.add_argument("--games", type=int, default=200)
    parser.add_argument("--tc", default="8+0.08")
    parser.add_argument("--openings", default="data/openings.epd")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--min-openings", type=int, default=1)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--output", default="results/anchor.json")
    parser.add_argument("--pgn", default="matches/anchor.pgn")
    parser.add_argument("--detach", action="store_true",
                        help="Launch detached (survives parent/job termination); poll PGN + score_pgn.py.")
    args = parser.parse_args()

    if args.games <= 0:
        parser.error("--games must be positive")
    if args.concurrency <= 0:
        parser.error("--concurrency must be positive")
    if args.min_openings < 0:
        parser.error("--min-openings cannot be negative")
    if not 0.0 < args.confidence < 1.0:
        parser.error("--confidence must be between 0 and 1")
    if any("=" not in option for option in args.anchor_option):
        parser.error("--anchor-option values must use NAME=VALUE")
    if not math.isfinite(args.anchor_elo):
        parser.error("--anchor-elo must be finite")
    if not args.anchor_no_default_options and not args.anchor_elo.is_integer():
        parser.error("Stockfish UCI_Elo anchor rating must be an integer")
    if not args.anchor_no_default_options and args.anchor_elo < 1320:
        parser.error("Stockfish UCI_Elo anchor rating must be at least 1320")
    if args.anchor_no_default_options and not args.anchor_family:
        parser.error("--anchor-family is required with --anchor-no-default-options")
    if not args.anchor_no_default_options and args.anchor_family and args.anchor_family.casefold() != "stockfish":
        parser.error("default UCI_LimitStrength mode requires --anchor-family stockfish")

    # Python 3.14 on Windows no longer resolves relative executable paths against
    # cwd, so resolve to absolute before any subprocess use (incl. base_metadata).
    args.engine = str(Path(args.engine).resolve())
    cutechess = find_cutechess()
    anchor = args.anchor_engine or find_stockfish()
    if not cutechess or not anchor:
        result = {
            "benchmark": "anchor",
            **base_metadata(args.engine, args.config),
            "passed": False,
            "skipped": True,
            "reason": f"cutechess={cutechess!r} anchor={anchor!r} (one not found)",
        }
        write_json(args.output, result)
        print(json.dumps(result))
        return 2

    openings_path = Path(args.openings) if args.openings else None
    openings_meta = file_metadata(args.openings, count_nonempty_lines=True) if args.openings else None
    if openings_path and not openings_path.is_file():
        result = {
            "benchmark": "anchor",
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
            "benchmark": "anchor",
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
    config_path = str(Path(args.config).resolve())
    anchor_path = str(Path(anchor).resolve())
    anchor_name = args.anchor_name or f"SF{args.anchor_elo:g}"
    anchor_family = args.anchor_family or "stockfish"
    anchor_options: list[tuple[str, str]] = []
    if not args.anchor_no_default_options:
        anchor_options += [
            ("UCI_LimitStrength", "true"),
            ("UCI_Elo", str(int(args.anchor_elo))),
        ]
    for option in args.anchor_option:
        name, value = option.split("=", 1)
        anchor_options.append((name.strip(), value.strip()))
    initstr = "\n".join(
        f"setoption name {name} value {value}" for name, value in anchor_options
    )
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
        "-engine", f"cmd={engine_path}", "arg=--config", f"arg={config_path}", "arg=uci",
        "proto=uci", "name=checkforge",
        "-engine", f"cmd={anchor_path}", "proto=uci", f"name={anchor_name}",
        "-each", f"tc={args.tc}",
        "-concurrency", str(args.concurrency),
        "-srand", str(args.seed),
        "-games", str(args.games),
        "-pgnout", pgn_path,
    ]
    if initstr:
        command[command.index("-each"):command.index("-each")] = [f"initstr={initstr}"]
    if schedule_path:
        command += [
            "-openings", f"file={schedule_path}", "format=epd", "order=sequential",
            "-repeat",
        ]

    reproducibility = {
        "cutechess": executable_metadata(
            cutechess, version=command_version(cutechess, "-version")
        ),
        "anchor_artifact": executable_metadata(anchor_path),
        "anchor_options": [
            {"name": name, "value": value} for name, value in anchor_options
        ],
        "openings": openings_meta,
        "opening_schedule": opening_schedule,
        "seed": args.seed,
        "concurrency": args.concurrency,
        "time_control": args.tc,
        "games": args.games,
        "paired_openings": require_pairs,
        "confidence": args.confidence,
    }

    if args.detach:
        # Survive harness/job reaping on long unattended runs; PGN is ground truth.
        DETACHED_PROCESS = 0x00000008
        CREATE_NEW_PROCESS_GROUP = 0x00000200
        CREATE_BREAKAWAY_FROM_JOB = 0x01000000
        flags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB
        log_path = str(Path(args.pgn).with_suffix(".cutechess.log"))
        with open(log_path, "w", encoding="utf-8") as log:
            proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT,
                                    stdin=subprocess.DEVNULL, creationflags=flags, close_fds=True)
        info = {"benchmark": "anchor", "detached": True, "pid": proc.pid, "pgn": args.pgn,
                "log": log_path, "anchor_elo": args.anchor_elo, "games_requested": args.games,
                **base_metadata(args.engine, args.config),
                "command": command, "reproducibility": reproducibility,
                "note": "detached match; poll PGN + score with research/score_pgn.py "
                        "(checkforge_elo = anchor_elo + elo_diff)"}
        write_json(args.output, info)
        print(json.dumps(info))
        return 0

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    combined = completed.stdout + "\n" + completed.stderr
    parsed = parse_results(combined)

    try:
        scored = score_pgn(
            pgn_path,
            "checkforge",
            confidence=args.confidence,
            expected_games=args.games,
            require_pairs=require_pairs,
            opening_schedule=schedule_path,
        )
    except Exception as exc:
        scored = {"valid": False, "error": str(exc)}

    checkforge_elo = None
    if scored.get("elo_diff") is not None:
        checkforge_elo = round(args.anchor_elo + scored["elo_diff"], 1)
    absolute_ci = None
    elo_ci = scored.get("elo_ci")
    if isinstance(elo_ci, list) and len(elo_ci) == 2 and None not in elo_ci:
        absolute_ci = [round(args.anchor_elo + value, 1) for value in elo_ci]

    lowered = combined.lower()
    passed = (
        completed.returncode == 0
        and "disconnects" not in lowered
        and "illegal" not in lowered
        and "could not initialize" not in lowered
        and bool(scored.get("valid", False))
    )

    result = {
        "benchmark": "anchor",
        **base_metadata(args.engine, args.config),
        "anchor": {
            "engine": anchor_path,
            "name": anchor_name,
            "family": anchor_family,
            "rating": args.anchor_elo,
            "calibration": "declared external rating; not assumed to equal FIDE Elo",
        },
        "tc": args.tc,
        "passed": passed,
        "measurement_valid": passed,
        "skipped": False,
        "results": scored,
        "cutechess_summary": parsed,
        "checkforge_elo": checkforge_elo,
        "checkforge_elo_ci": absolute_ci,
        "checkforge_elo_error": scored.get("elo_err"),
        "confidence": args.confidence,
        "reproducibility": reproducibility,
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "pgn": pgn_path,
    }
    write_json(args.output, result)
    if checkforge_elo is not None:
        err = scored.get("elo_err")
        err_s = f" +/- {err} ({args.confidence:.0%} CI)" if err is not None else ""
        print(f"CheckForge absolute Elo ~= {checkforge_elo}{err_s} "
              f"(anchor {anchor_name}, {scored.get('wins','?')}-{scored.get('losses','?')}-{scored.get('draws','?')})")
    else:
        print(json.dumps(result))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
