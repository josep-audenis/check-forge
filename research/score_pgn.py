"""Compute W-L-D and an Elo estimate from a cutechess PGN.

The PGN is the ground truth for a match: even when the run wrapper dies before writing
its JSON (orphaned background task, killed shell), the completed games survive here. Use
this to recover a result, or as a library from run_cutechess.py.

    python research/score_pgn.py matches/expNNN.pgn --engine checkforge
"""

from __future__ import annotations

import argparse
import json
import math
import re
from pathlib import Path


def score_pgn(pgn_path: str, engine_name: str = "checkforge") -> dict:
    text = Path(pgn_path).read_text(encoding="utf-8", errors="replace")
    games = text.split("[Event")
    wins = losses = draws = 0
    illegal = "illegal" in text.lower()
    for g in games:
        mw = re.search(r'\[White "([^"]+)"', g)
        mb = re.search(r'\[Black "([^"]+)"', g)
        mr = re.search(r'\[Result "([^"]+)"', g)
        if not (mw and mb and mr):
            continue
        res = mr.group(1)
        if res == "1/2-1/2":
            draws += 1
            continue
        if res not in ("1-0", "0-1"):
            continue  # unterminated / *
        engine_is_white = mw.group(1) == engine_name
        engine_won = (res == "1-0" and engine_is_white) or (res == "0-1" and not engine_is_white)
        if engine_won:
            wins += 1
        else:
            losses += 1

    n = wins + losses + draws
    out: dict = {
        "engine": engine_name,
        "pgn": pgn_path,
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "games": n,
        "illegal": illegal,
    }
    if n > 0:
        score = (wins + 0.5 * draws) / n
        out["score"] = round(score, 4)
        if 0.0 < score < 1.0:
            out["elo_diff"] = round(-400 * math.log10(1 / score - 1), 1)
            se = math.sqrt(score * (1 - score) / n)
            out["elo_err"] = round(400 / math.log(10) * se / (score * (1 - score)), 1)
        else:
            out["elo_diff"] = None
            out["elo_err"] = None
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pgn")
    parser.add_argument("--engine", default="checkforge", help="engine name as written in the PGN")
    parser.add_argument("--output", default=None, help="optional JSON path to write")
    args = parser.parse_args()
    result = score_pgn(args.pgn, args.engine)
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
