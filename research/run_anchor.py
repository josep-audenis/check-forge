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
import os
import re
import shutil
import subprocess
from pathlib import Path

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
    parser.add_argument("--anchor-elo", type=int, default=1500,
                        help="Known Elo to pin the anchor to (UCI_Elo). Floor 1320 for Stockfish.")
    parser.add_argument("--games", type=int, default=200)
    parser.add_argument("--tc", default="8+0.08")
    parser.add_argument("--openings", default="data/openings.epd")
    parser.add_argument("--output", default="results/anchor.json")
    parser.add_argument("--pgn", default="matches/anchor.pgn")
    parser.add_argument("--detach", action="store_true",
                        help="Launch detached (survives parent/job termination); poll PGN + score_pgn.py.")
    args = parser.parse_args()

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

    Path(args.pgn).parent.mkdir(parents=True, exist_ok=True)
    engine_path = str(Path(args.engine).resolve())
    config_path = str(Path(args.config).resolve())
    anchor_path = str(Path(anchor).resolve())
    anchor_name = f"SF{args.anchor_elo}"
    initstr = (
        f"setoption name UCI_LimitStrength value true\n"
        f"setoption name UCI_Elo value {args.anchor_elo}"
    )

    command = [
        cutechess,
        "-engine", f"cmd={engine_path}", "arg=--config", f"arg={config_path}", "arg=uci",
        "proto=uci", "name=checkforge",
        "-engine", f"cmd={anchor_path}", "proto=uci", f"name={anchor_name}", f"initstr={initstr}",
        "-each", f"tc={args.tc}",
        "-games", str(args.games),
        "-pgnout", args.pgn,
    ]
    openings_path = Path(args.openings) if args.openings else None
    if openings_path and openings_path.exists():
        command += [
            "-openings", f"file={openings_path.resolve()}", "format=epd", "order=random",
            "-repeat",
        ]

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
                "note": "detached match; poll PGN + score with research/score_pgn.py "
                        "(checkforge_elo = anchor_elo + elo_diff)"}
        write_json(args.output, info)
        print(json.dumps(info))
        return 0

    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    combined = completed.stdout + "\n" + completed.stderr
    parsed = parse_results(combined)

    checkforge_elo = None
    if "elo_difference" in parsed:
        checkforge_elo = round(args.anchor_elo + parsed["elo_difference"], 1)

    lowered = combined.lower()
    passed = (
        completed.returncode == 0
        and "disconnects" not in lowered
        and "illegal" not in lowered
        and "could not initialize" not in lowered
        and "elo_difference" in parsed
    )

    result = {
        "benchmark": "anchor",
        **base_metadata(args.engine, args.config),
        "anchor": {"engine": anchor_path, "name": anchor_name, "rating": args.anchor_elo},
        "tc": args.tc,
        "passed": passed,
        "skipped": False,
        "results": parsed,
        "checkforge_elo": checkforge_elo,
        "checkforge_elo_error": parsed.get("elo_error"),
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "pgn": args.pgn,
    }
    write_json(args.output, result)
    if checkforge_elo is not None:
        err = parsed.get("elo_error")
        err_s = f" +/- {err}" if err is not None else ""
        print(f"CheckForge absolute Elo ~= {checkforge_elo}{err_s} "
              f"(anchor {anchor_name}, {parsed.get('wins','?')}-{parsed.get('losses','?')}-{parsed.get('draws','?')})")
    else:
        print(json.dumps(result))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
