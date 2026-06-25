"""SPSA tuning for CheckForge eval/search weights (exp036).

Simultaneous Perturbation Stochastic Approximation: each iteration perturbs all tuned
parameters at once by +/- c_k along a random sign vector, plays a short self-match between
the two perturbed configs (same engine binary, only --config differs), and steps the
parameters toward the winner. Two engine evaluations per iteration regardless of dimension
— that's the point of SPSA.

State is checkpointed to results/spsa_state.json after every iteration, so a killed run
resumes where it left off (the harness sometimes reaps long background processes).

Usage:
    python research/run_spsa.py --engine build/engine/checkforge.exe --iterations 30 --games 24
"""

from __future__ import annotations

import argparse
import json
import os
import random
import shutil
import subprocess
from pathlib import Path

from score_pgn import score_pgn

# Parameters to tune: name -> (init, lo, hi). Mobility weights (the +96 lever, exp032).
PARAMS = {
    "mob_knight": (4, 1, 12),
    "mob_bishop": (4, 1, 12),
    "mob_rook":   (2, 1, 10),
    "mob_queen":  (1, 1, 8),
}

# Fixed (non-tuned) config fields, written into every trial config.
BASE = {
    "pawn": 100, "knight": 320, "bishop": 330, "rook": 500, "queen": 900,
    "default_depth": 3, "quiescence_depth": 4,
}


def find_cutechess() -> str | None:
    found = shutil.which("cutechess-cli")
    if found:
        return found
    root = Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages"
    if root.exists():
        m = list(root.rglob("cutechess-cli.exe"))
        if m:
            return str(m[0])
    return None


def write_config(path: str, theta: dict) -> None:
    cfg = {
        "piece_values": {k: BASE[k] for k in ("pawn", "knight", "bishop", "rook", "queen")},
        "eval_weights": {k: int(round(theta[k])) for k in PARAMS},
        "search_params": {"default_depth": BASE["default_depth"],
                          "quiescence_depth": BASE["quiescence_depth"]},
    }
    Path(path).write_text(json.dumps(cfg), encoding="utf-8")


def clamp(name: str, v: float) -> float:
    _, lo, hi = PARAMS[name]
    return max(lo, min(hi, v))


def play(cutechess: str, engine: str, cfg_plus: str, cfg_minus: str, games: int,
         tc: str, openings: str, pgn: str) -> float:
    """Play cfg_plus ('checkforge') vs cfg_minus; return plus's score in [0,1]."""
    eng = str(Path(engine).resolve())
    cmd = [
        cutechess,
        "-engine", f"cmd={eng}", "arg=--config", f"arg={str(Path(cfg_plus).resolve())}", "arg=uci", "proto=uci", "name=checkforge",
        "-engine", f"cmd={eng}", "arg=--config", f"arg={str(Path(cfg_minus).resolve())}", "arg=uci", "proto=uci", "name=opponent",
        "-each", f"tc={tc}", "-games", str(games), "-pgnout", pgn,
    ]
    op = Path(openings)
    if openings and op.exists():
        cmd += ["-openings", f"file={op.resolve()}", "format=epd", "order=random", "-repeat"]
    subprocess.run(cmd, check=False, capture_output=True, text=True)
    res = score_pgn(pgn, "checkforge")
    n = res.get("games", 0)
    return res["score"] if n else 0.5


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--engine", required=True)
    ap.add_argument("--iterations", type=int, default=30)
    ap.add_argument("--games", type=int, default=24)
    ap.add_argument("--tc", default="4+0.04")  # fast TC: SPSA needs many games
    ap.add_argument("--openings", default="data/openings.epd")
    ap.add_argument("--state", default="results/spsa_state.json")
    ap.add_argument("--seed", type=int, default=12345)
    # SPSA gains (integer-parameter friendly).
    ap.add_argument("--a", type=float, default=0.6)
    ap.add_argument("--c", type=float, default=2.0)
    ap.add_argument("--alpha", type=float, default=0.602)
    ap.add_argument("--gamma", type=float, default=0.101)
    args = ap.parse_args()

    cutechess = find_cutechess()
    if not cutechess:
        print(json.dumps({"error": "cutechess-cli not found"}))
        return 2

    # Resume from checkpoint if present.
    if Path(args.state).exists():
        state = json.loads(Path(args.state).read_text())
    else:
        state = {"theta": {k: float(v[0]) for k, v in PARAMS.items()}, "iter": 0, "history": []}

    rng = random.Random(args.seed + state["iter"])
    A = max(1, args.iterations // 10)
    Path("configs").mkdir(exist_ok=True)
    Path("matches").mkdir(exist_ok=True)

    while state["iter"] < args.iterations:
        k = state["iter"]
        ck = args.c / ((k + 1) ** args.gamma)
        ak = args.a / ((k + 1 + A) ** args.alpha)
        theta = state["theta"]

        delta = {name: (1 if rng.random() < 0.5 else -1) for name in PARAMS}
        plus = {n: clamp(n, theta[n] + ck * delta[n]) for n in PARAMS}
        minus = {n: clamp(n, theta[n] - ck * delta[n]) for n in PARAMS}
        write_config("configs/_spsa_plus.json", plus)
        write_config("configs/_spsa_minus.json", minus)

        score = play(cutechess, args.engine, "configs/_spsa_plus.json",
                     "configs/_spsa_minus.json", args.games, args.tc, args.openings,
                     "matches/_spsa_iter.pgn")

        # Gradient estimate (maximize plus's score): ghat_i = (2*score-1)/(2*ck*delta_i).
        g = (2.0 * score - 1.0)
        for n in PARAMS:
            ghat = g / (2.0 * ck * delta[n])
            theta[n] = clamp(n, theta[n] + ak * ghat)

        state["iter"] = k + 1
        state["theta"] = theta
        snap = {n: int(round(theta[n])) for n in PARAMS}
        state["history"].append({"iter": k + 1, "score_plus": round(score, 3), "theta": snap})
        Path(args.state).write_text(json.dumps(state, indent=2))
        print(f"iter {k+1}/{args.iterations} plus_score={score:.3f} theta={snap}", flush=True)

    final = {n: int(round(state["theta"][n])) for n in PARAMS}
    write_config("configs/spsa_tuned.json", state["theta"])
    print("SPSA done. tuned=" + json.dumps(final) + " -> configs/spsa_tuned.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
