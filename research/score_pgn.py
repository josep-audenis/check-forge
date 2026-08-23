"""Score a Cute Chess PGN with paired statistics and explicit confidence.

PGN remains match ground truth. Completed colour-swapped opening pairs become
independent statistical units; raw games are used only when pairing is absent.
"""

from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path
from statistics import NormalDist
from typing import Any

try:  # Script execution (`python research/score_pgn.py`).
    from match_statistics import pentanomial_counts, sprt_snapshot, summarize_samples
except ModuleNotFoundError:  # Package import in unit tests.
    from research.match_statistics import pentanomial_counts, sprt_snapshot, summarize_samples


_TAG_RE = re.compile(r'^\[([A-Za-z0-9_]+)\s+"((?:\\"|[^"])*)"\]\s*$', re.MULTILINE)
_GAME_SPLIT_RE = re.compile(r'(?=^\[Event\s+")', re.MULTILINE)


def _round(value: float | None, digits: int = 4) -> float | None:
    return None if value is None else round(value, digits)


def _position_key(value: str) -> str:
    fields = value.strip().split()
    return " ".join(fields[:4]) if len(fields) >= 4 else value.strip()


def _schedule_position_keys(path: str) -> list[str]:
    return [
        _position_key(line)
        for line in Path(path).read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


def _json_statistics(summary: dict[str, Any]) -> dict[str, Any]:
    result = dict(summary)
    for key in ("mean_score", "score_se", "elo", "elo_se", "elo_margin", "elo_margin_95"):
        if key in result:
            result[key] = _round(result[key])
    for key in ("score_ci", "elo_ci"):
        if key in result:
            result[key] = [_round(value) for value in result[key]]
    return result


def _game_records(text: str, engine_name: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Parse completed games involving engine; return records and rejected blocks."""
    engine_key = engine_name.casefold()
    records: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    ordinal = 0
    for block in _GAME_SPLIT_RE.split(text):
        if not block.lstrip().startswith("[Event"):
            continue
        ordinal += 1
        tags = {key: value.replace(r'\"', '"') for key, value in _TAG_RE.findall(block)}
        missing = [key for key in ("White", "Black", "Result") if key not in tags]
        if missing:
            rejected.append({"game": ordinal, "reason": f"missing tags: {', '.join(missing)}"})
            continue
        white_key = tags["White"].casefold()
        black_key = tags["Black"].casefold()
        if engine_key not in (white_key, black_key):
            rejected.append({"game": ordinal, "reason": f"engine {engine_name!r} is not a player"})
            continue
        result = tags["Result"]
        if result not in ("1-0", "0-1", "1/2-1/2"):
            rejected.append({"game": ordinal, "reason": f"unfinished or invalid result: {result}"})
            continue
        if result == "1/2-1/2":
            score = 0.5
        else:
            engine_is_white = white_key == engine_key
            engine_won = (result == "1-0" and engine_is_white) or (
                result == "0-1" and not engine_is_white
            )
            score = 1.0 if engine_won else 0.0
        records.append({
            "game": ordinal,
            "white": tags["White"],
            "black": tags["Black"],
            "result": result,
            "score": score,
            "round": tags.get("Round"),
            "fen": tags.get("FEN", "startpos"),
            "termination": tags.get("Termination", "unknown"),
        })
    return records, rejected


def _paired_scores(records: list[dict[str, Any]]) -> tuple[list[float], list[dict[str, Any]], int]:
    """Validate consecutive Cute Chess colour pairs and return pair totals."""
    totals: list[float] = []
    rejected: list[dict[str, Any]] = []
    pairable = len(records) - (len(records) % 2)
    for offset in range(0, pairable, 2):
        first, second = records[offset], records[offset + 1]
        reasons = []
        if first["fen"] != second["fen"]:
            reasons.append("different opening FEN")
        if first["round"] and second["round"] and first["round"] != second["round"]:
            reasons.append("different round")
        if not (
            first["white"].casefold() == second["black"].casefold()
            and first["black"].casefold() == second["white"].casefold()
        ):
            reasons.append("colours not swapped")
        if reasons:
            rejected.append({
                "games": [first["game"], second["game"]],
                "reason": "; ".join(reasons),
            })
        else:
            totals.append(first["score"] + second["score"])
    return totals, rejected, len(records) % 2


def score_pgn(
    pgn_path: str,
    engine_name: str = "checkforge",
    *,
    confidence: float = 0.95,
    expected_games: int | None = None,
    require_pairs: bool = False,
    sprt: dict[str, float] | None = None,
    opening_schedule: str | None = None,
) -> dict[str, Any]:
    """Return W/D/L, paired pentanomial statistics, CI, and validation state."""
    text = Path(pgn_path).read_text(encoding="utf-8", errors="replace")
    records, rejected_games = _game_records(text, engine_name)
    scores = [record["score"] for record in records]
    wins = scores.count(1.0)
    losses = scores.count(0.0)
    draws = scores.count(0.5)
    games = len(scores)
    pair_totals, rejected_pairs, trailing_unpaired = _paired_scores(records)
    complete_pairing = bool(pair_totals) and len(pair_totals) * 2 == games and not rejected_pairs
    schedule_validation: dict[str, Any] = {
        "required": opening_schedule is not None,
        "path": str(Path(opening_schedule).resolve()) if opening_schedule else None,
        "complete": None,
        "expected_pairs": None,
        "actual_pairs": games // 2,
        "mismatches": [],
    }
    if opening_schedule:
        expected_positions = _schedule_position_keys(opening_schedule)
        actual_positions = [_position_key(records[offset]["fen"])
                            for offset in range(0, games - (games % 2), 2)]
        mismatches = [
            {
                "pair": index + 1,
                "expected": expected,
                "actual": actual,
            }
            for index, (expected, actual) in enumerate(zip(expected_positions, actual_positions))
            if expected != actual
        ]
        schedule_validation.update({
            "complete": len(expected_positions) == len(actual_positions) and not mismatches,
            "expected_pairs": len(expected_positions),
            "mismatches": mismatches,
        })
    schedule_complete = schedule_validation["complete"] is not False
    samples = [total / 2.0 for total in pair_totals] if complete_pairing else scores

    terminations = Counter(record["termination"] for record in records)
    time_forfeits = sum(
        1 for record in records if "time" in record["termination"].casefold()
    )
    engine_time_losses = sum(
        1 for record in records
        if record["score"] == 0.0 and "time" in record["termination"].casefold()
    )
    opponent_time_losses = time_forfeits - engine_time_losses
    illegal = "illegal" in text.casefold()
    validation_errors: list[str] = []
    if not games:
        validation_errors.append("no completed games for engine")
    if rejected_games:
        validation_errors.append(f"{len(rejected_games)} malformed, unfinished, or unrelated games")
    if illegal:
        validation_errors.append("illegal marker found in PGN")
    if time_forfeits:
        validation_errors.append(
            f"{time_forfeits} time forfeits ({engine_time_losses} engine, "
            f"{opponent_time_losses} opponent)"
        )
    if expected_games is not None and games != expected_games:
        validation_errors.append(f"completed {games} games; expected {expected_games}")
    if require_pairs and not complete_pairing:
        validation_errors.append(
            f"paired opening validation failed: {len(pair_totals)} valid pairs, "
            f"{len(rejected_pairs)} rejected pairs, {trailing_unpaired} trailing games"
        )
    if sprt and not complete_pairing:
        validation_errors.append("sequential test requires complete colour-swapped opening pairs")
    if sprt and not opening_schedule:
        validation_errors.append("sequential test requires a preassigned opening schedule")
    if opening_schedule and not schedule_complete:
        validation_errors.append(
            "PGN pair sequence does not match preassigned opening schedule: "
            f"{len(schedule_validation['mismatches'])} mismatches, "
            f"{schedule_validation['actual_pairs']} actual / "
            f"{schedule_validation['expected_pairs']} expected pairs"
        )

    out: dict[str, Any] = {
        "engine": engine_name,
        "pgn": str(Path(pgn_path).resolve()),
        "wins": wins,
        "losses": losses,
        "draws": draws,
        "games": games,
        "illegal": illegal,
        "time_forfeits": time_forfeits,
        "engine_time_losses": engine_time_losses,
        "opponent_time_losses": opponent_time_losses,
        "terminations": dict(terminations),
        "rejected_games": rejected_games,
        "valid": not validation_errors,
        "validation_errors": validation_errors,
        "pairing": {
            "required": require_pairs,
            "complete": complete_pairing,
            "pairs": len(pair_totals),
            "rejected_pairs": rejected_pairs,
            "trailing_unpaired_games": trailing_unpaired,
            "pentanomial": pentanomial_counts(pair_totals),
            "confidence_unit": "opening_pair" if complete_pairing else "game",
            "schedule_validation": schedule_validation,
        },
    }
    if not samples:
        return out

    summary = _json_statistics(summarize_samples(samples, confidence))
    score = (wins + 0.5 * draws) / games
    out.update({
        "score": round(score, 4),
        "elo_diff": _round(summary["elo"], 1),
        "elo_se": _round(summary["elo_se"], 1),
        "elo_ci": [_round(value, 1) for value in summary["elo_ci"]],
        "elo_err": _round(summary.get("elo_margin"), 1),
        "elo_error_confidence": confidence,
        "score_ci": summary["score_ci"],
        "statistics": summary,
    })
    score_se = summary.get("score_se")
    if score_se and score_se > 0:
        out["los_percent"] = round(
            100.0 * NormalDist().cdf((summary["mean_score"] - 0.5) / score_se), 2
        )
    else:
        out["los_percent"] = None
    if sprt and complete_pairing and opening_schedule and schedule_complete:
        out["sprt"] = sprt_snapshot(
            samples,
            sprt["elo0"],
            sprt["elo1"],
            sprt.get("alpha", 0.05),
            sprt.get("beta", 0.05),
        )
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("pgn")
    parser.add_argument("--engine", default="checkforge", help="engine name as written in PGN")
    parser.add_argument("--output", default=None, help="optional JSON path to write")
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--expected-games", type=int, default=None)
    parser.add_argument("--require-pairs", action="store_true")
    parser.add_argument("--opening-schedule", default=None,
                        help="preassigned EPD schedule whose order must match PGN pairs")
    parser.add_argument("--sprt-elo0", type=float, default=None)
    parser.add_argument("--sprt-elo1", type=float, default=None)
    parser.add_argument("--sprt-alpha", type=float, default=0.05)
    parser.add_argument("--sprt-beta", type=float, default=0.05)
    parser.add_argument("--strict", action="store_true", help="exit non-zero when validation fails")
    args = parser.parse_args()
    if (args.sprt_elo0 is None) != (args.sprt_elo1 is None):
        parser.error("--sprt-elo0 and --sprt-elo1 must be provided together")
    if args.sprt_alpha + args.sprt_beta >= 1.0:
        parser.error("SPRT alpha + beta must be less than 1")
    if args.sprt_elo0 is not None and not args.opening_schedule:
        parser.error("sequential testing requires --opening-schedule")
    sprt = None
    if args.sprt_elo0 is not None:
        sprt = {
            "elo0": args.sprt_elo0,
            "elo1": args.sprt_elo1,
            "alpha": args.sprt_alpha,
            "beta": args.sprt_beta,
        }
    result = score_pgn(
        args.pgn,
        args.engine,
        confidence=args.confidence,
        expected_games=args.expected_games,
        require_pairs=args.require_pairs or sprt is not None,
        sprt=sprt,
        opening_schedule=args.opening_schedule,
    )
    if args.output:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result))
    return 1 if args.strict and not result["valid"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
