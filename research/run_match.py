"""Run deterministic internal engine-vs-engine games through UCI."""

from __future__ import annotations

import argparse
import json
import subprocess

from harness import DEFAULT_CONFIG, base_metadata, write_json


def uci_bestmove(engine: str, config: str, moves: list[str], depth: int) -> tuple[str | None, str, str, int]:
    command = [engine, "--config", config, "uci"]
    position = "position startpos"
    if moves:
        position += " moves " + " ".join(moves)
    script = "\n".join(["uci", "isready", position, f"go depth {depth}", "quit", ""])
    completed = subprocess.run(command, input=script, check=False, capture_output=True, text=True, timeout=30.0)

    best = None
    for line in completed.stdout.splitlines():
        parts = line.strip().split()
        if len(parts) >= 2 and parts[0] == "bestmove":
            best = parts[1]
            break

    if best == "0000":
        best = None
    return best, completed.stdout.strip(), completed.stderr.strip(), completed.returncode


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--opponent-engine")
    parser.add_argument("--config", default=DEFAULT_CONFIG)
    parser.add_argument("--opponent-config", default=DEFAULT_CONFIG)
    parser.add_argument("--output", default="results/match.json")
    parser.add_argument("--games", type=int, default=2)
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--max-plies", type=int, default=80)
    args = parser.parse_args()

    opponent = args.opponent_engine or args.engine
    games = []
    for game_index in range(args.games):
        moves: list[str] = []
        failed = None
        for ply in range(args.max_plies):
            use_primary = (ply % 2 == 0 and game_index % 2 == 0) or (ply % 2 == 1 and game_index % 2 == 1)
            engine = args.engine if use_primary else opponent
            config = args.config if use_primary else args.opponent_config
            move, _stdout, stderr, returncode = uci_bestmove(engine, config, moves, args.depth)
            if returncode != 0:
                failed = {"ply": ply + 1, "engine": engine, "stderr": stderr, "returncode": returncode}
                break
            if move is None:
                break
            moves.append(move)

        games.append({
            "game": game_index + 1,
            "white_engine": args.engine if game_index % 2 == 0 else opponent,
            "black_engine": opponent if game_index % 2 == 0 else args.engine,
            "plies": len(moves),
            "moves": moves,
            "result": "1/2-1/2" if len(moves) >= args.max_plies else "*",
            "failed": failed,
        })

    passed = all(game["failed"] is None and game["plies"] > 0 for game in games)
    result = {
        "benchmark": "match",
        **base_metadata(args.engine, args.config),
        "opponent": {
            "engine": opponent,
            "config": args.opponent_config,
        },
        "passed": passed,
        "games_requested": args.games,
        "max_plies": args.max_plies,
        "games": games,
        "note": "Internal UCI runner checks protocol stability and version-vs-version plies. Cutechess remains stronger external validation.",
    }

    write_json(args.output, result)
    print(json.dumps(result))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
