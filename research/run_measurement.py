"""Run reproducible screen, verification, or rating-claim match suites.

Default mode is plan-only because verification profiles can consume thousands
of games. Pass ``--execute`` after reviewing preflight output.
"""

from __future__ import annotations

import argparse
import json
import math
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    from aggregate_anchors import aggregate_anchor_results
    from harness import base_metadata, file_metadata, utc_id, write_json
except ModuleNotFoundError:
    from research.aggregate_anchors import aggregate_anchor_results
    from research.harness import base_metadata, file_metadata, utc_id, write_json


PROFILES: dict[str, dict[str, Any]] = {
    "smoke": {
        "minimum_openings": 12,
        "minimum_anchors": 0,
        "strength_claim": False,
        "stages": [
            {"name": "smoke", "tc": "8+0.08", "games": 24,
             "sprt": None, "integrity_only": True},
        ],
    },
    "screen": {
        "minimum_openings": 12,
        "minimum_anchors": 0,
        "stages": [
            {"name": "stc", "tc": "8+0.08", "games": 400,
             "sprt": {"elo0": 0.0, "elo1": 20.0, "alpha": 0.05, "beta": 0.05}},
        ],
    },
    "verify": {
        "minimum_openings": 100,
        "minimum_anchors": 1,
        "stages": [
            {"name": "stc", "tc": "8+0.08", "games": 5000,
             "sprt": {"elo0": 0.0, "elo1": 10.0, "alpha": 0.05, "beta": 0.05}},
            {"name": "ltc", "tc": "60+0.6", "games": 1200, "sprt": None},
        ],
    },
    "claim": {
        "minimum_openings": 500,
        "minimum_anchors": 3,
        "target_elo": 2500.0,
        "stages": [
            {"name": "stc", "tc": "8+0.08", "games": 4600, "sprt": None,
             "minimum_relative_elo": 15.0},
            {"name": "ltc", "tc": "60+0.6", "games": 1200, "sprt": None,
             "minimum_relative_elo": 15.0},
        ],
    },
}


def load_anchors(path: str | None) -> list[dict[str, Any]]:
    if not path:
        return []
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    anchors = payload.get("anchors") if isinstance(payload, dict) else payload
    if not isinstance(anchors, list):
        raise ValueError("anchors JSON must be a list or contain an 'anchors' list")
    required = ("name", "family", "engine", "rating")
    for index, anchor in enumerate(anchors):
        if not isinstance(anchor, dict) or any(key not in anchor for key in required):
            raise ValueError(f"anchor {index} must contain name, family, engine, and rating")
        if not isinstance(anchor.get("options", {}), dict):
            raise ValueError(f"anchor {index} options must be an object")
        if (
            not isinstance(anchor["rating"], (int, float))
            or isinstance(anchor["rating"], bool)
            or not math.isfinite(float(anchor["rating"]))
        ):
            raise ValueError(f"anchor {index} rating must be numeric")
        if not isinstance(anchor["family"], str) or not anchor["family"].strip():
            raise ValueError(f"anchor {index} family must be a non-empty string")
    return anchors


def preflight(
    profile: dict[str, Any],
    openings: str,
    engine: str,
    baseline_engine: str | None,
    anchors: list[dict[str, Any]],
    target_elo: float | None = None,
    config: str | None = None,
    baseline_config: str | None = None,
) -> tuple[list[str], dict[str, Any]]:
    errors = []
    openings_meta = file_metadata(openings, count_nonempty_lines=True)
    opening_count = int((openings_meta or {}).get("unique_positions", 0))
    if not openings_meta or not openings_meta.get("exists"):
        errors.append(f"opening file not found: {openings}")
    elif opening_count < profile["minimum_openings"]:
        errors.append(
            f"opening suite has {opening_count} unique positions; profile requires "
            f"{profile['minimum_openings']}"
        )
    if not Path(engine).is_file():
        errors.append(f"engine executable not found: {engine}")
    if config and not Path(config).is_file():
        errors.append(f"engine config not found: {config}")
    if baseline_engine and not Path(baseline_engine).is_file():
        errors.append(f"baseline executable not found: {baseline_engine}")
    if baseline_engine and baseline_config and not Path(baseline_config).is_file():
        errors.append(f"baseline config not found: {baseline_config}")
    if not baseline_engine and not anchors:
        errors.append("provide --baseline-engine, --anchors, or both")
    if not baseline_engine and anchors and target_elo is None:
        errors.append("provide --target-elo when measuring only against anchors")
    missing_anchors = [str(anchor["engine"]) for anchor in anchors if not Path(anchor["engine"]).is_file()]
    if missing_anchors:
        errors.append(f"missing anchor executables: {', '.join(missing_anchors)}")
    unique_anchor_hashes = {
        (file_metadata(str(anchor["engine"])) or {}).get("sha256")
        for anchor in anchors if Path(anchor["engine"]).is_file()
    } - {None}
    unique_anchor_families = {
        str(anchor.get("family", "")).strip().casefold() for anchor in anchors
        if str(anchor.get("family", "")).strip()
    }
    if len(anchors) < profile["minimum_anchors"]:
        errors.append(
            f"profile has {len(anchors)} anchors; require {profile['minimum_anchors']}"
        )
    if len(unique_anchor_hashes) < profile["minimum_anchors"]:
        errors.append(
            f"profile has {len(unique_anchor_hashes)} unique anchor binaries; "
            f"require {profile['minimum_anchors']}"
        )
    if len(unique_anchor_families) < profile["minimum_anchors"]:
        errors.append(
            f"profile has {len(unique_anchor_families)} independent anchor families; "
            f"require {profile['minimum_anchors']}"
        )
    return errors, {
        "openings": openings_meta,
        "anchors": len(anchors),
        "unique_anchor_artifacts": len(unique_anchor_hashes),
        "independent_anchor_families": len(unique_anchor_families),
    }


def _run(command: list[str], output_path: Path) -> dict[str, Any]:
    completed = subprocess.run(command, check=False, capture_output=True, text=True)
    payload = None
    if output_path.is_file():
        payload = json.loads(output_path.read_text(encoding="utf-8"))
    return {
        "command": command,
        "returncode": completed.returncode,
        "stdout": completed.stdout.strip(),
        "stderr": completed.stderr.strip(),
        "output": str(output_path),
        "result": payload,
        "measurement_valid": completed.returncode == 0 and bool(
            payload and payload.get("measurement_valid", payload.get("passed", False))
        ),
    }


def relative_decision(run: dict[str, Any], stage: dict[str, Any]) -> dict[str, Any]:
    """Separate strength decision from match/PGN integrity."""
    if not run.get("measurement_valid"):
        return {"passed": False, "status": "invalid_measurement"}
    if stage.get("integrity_only"):
        return {
            "passed": True,
            "status": "integrity_passed",
            "criterion": "integrity-only smoke; no strength inference",
        }
    results = ((run.get("result") or {}).get("results") or {})
    if stage.get("sprt"):
        sequential = results.get("sprt") or {}
        status = sequential.get("status", "missing")
        method = sequential.get("method")
        return {
            "passed": status == "accept_h1" and method == "paired_hoeffding_e_process",
            "status": status,
            "criterion": "paired anytime-valid sequential test must accept H1",
        }
    estimate = results.get("elo_diff")
    elo_ci = results.get("elo_ci")
    minimum = float(stage.get("minimum_relative_elo", 15.0))
    passed = (
        isinstance(estimate, (int, float))
        and isinstance(elo_ci, list)
        and len(elo_ci) == 2
        and isinstance(elo_ci[0], (int, float))
        and estimate >= minimum
        and elo_ci[0] > 0.0
    )
    return {
        "passed": passed,
        "status": "accepted" if passed else "rejected_or_inconclusive",
        "criterion": f"estimate >= {minimum:.1f} Elo and confidence interval lower bound > 0",
    }


def absolute_decision(aggregate: dict[str, Any], target_elo: float) -> dict[str, Any]:
    """Require aggregate lower confidence bound to clear declared engine-pool target."""
    elo_ci = aggregate.get("elo_ci")
    passed = bool(
        aggregate.get("valid")
        and isinstance(elo_ci, list)
        and len(elo_ci) == 2
        and isinstance(elo_ci[0], (int, float))
        and elo_ci[0] >= target_elo
    )
    return {
        "passed": passed,
        "status": "accepted" if passed else "rejected_or_inconclusive",
        "criterion": f"aggregate confidence interval lower bound >= {target_elo:.1f} engine-pool Elo",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--engine", required=True)
    parser.add_argument("--config", default="configs/default.json")
    parser.add_argument("--baseline-engine", default=None)
    parser.add_argument("--baseline-config", default="configs/default.json")
    parser.add_argument("--anchors", default=None, help="JSON file describing independent anchors")
    parser.add_argument("--profile", choices=sorted(PROFILES), default="screen")
    parser.add_argument("--openings", default="data/openings.epd")
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--concurrency", type=int, default=1)
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--target-elo", type=float, default=None,
                        help="Absolute engine-pool Elo target; claim profile defaults to 2500")
    parser.add_argument("--result-dir", default=None)
    parser.add_argument("--output", default="results/measurement-latest.json")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()

    if args.concurrency <= 0:
        parser.error("--concurrency must be positive")
    if args.concurrency != 1 and any(stage.get("sprt") for stage in PROFILES[args.profile]["stages"]):
        parser.error("sequential profiles require --concurrency 1 to preserve pair order")
    if not 0.0 < args.confidence < 1.0:
        parser.error("--confidence must be between 0 and 1")
    if args.target_elo is not None and not math.isfinite(args.target_elo):
        parser.error("--target-elo must be finite")

    profile = PROFILES[args.profile]
    target_elo = args.target_elo if args.target_elo is not None else profile.get("target_elo")
    anchors = load_anchors(args.anchors)
    errors, preflight_metadata = preflight(
        profile, args.openings, args.engine, args.baseline_engine, anchors, target_elo,
        args.config, args.baseline_config,
    )
    run_id = utc_id(f"measurement-{args.profile}")
    result_dir = Path(args.result_dir or (Path("results") / run_id))
    pgn_dir = Path("matches") / run_id

    plan = {
        "benchmark": "measurement_suite",
        "mode": "execute" if args.execute else "plan",
        "profile": args.profile,
        "profile_policy": profile,
        "target_elo": target_elo,
        **base_metadata(args.engine, args.config),
        "baseline": {
            "engine": args.baseline_engine,
            "config": args.baseline_config,
        } if args.baseline_engine else None,
        "anchor_definitions": anchors,
        "preflight": preflight_metadata,
        "validation_errors": errors,
        "result_dir": str(result_dir),
        "runs": [],
        "measurement_valid": None,
        "profile_passed": None,
    }
    if errors:
        plan["valid"] = False
        write_json(args.output, plan)
        print(json.dumps(plan))
        return 2
    if not args.execute:
        plan["valid"] = True
        plan["note"] = "Plan validated. Re-run with --execute to start potentially long matches."
        write_json(args.output, plan)
        print(json.dumps(plan))
        return 0

    result_dir.mkdir(parents=True, exist_ok=True)
    pgn_dir.mkdir(parents=True, exist_ok=True)
    for stage_index, stage in enumerate(profile["stages"]):
        seed = args.seed + stage_index
        if args.baseline_engine:
            output_path = result_dir / f"relative-{stage['name']}.json"
            pgn_path = pgn_dir / f"relative-{stage['name']}.pgn"
            command = [
                sys.executable, "research/run_cutechess.py",
                "--engine", args.engine, "--config", args.config,
                "--opponent-engine", args.baseline_engine,
                "--opponent-config", args.baseline_config,
                "--games", str(stage["games"]), "--tc", stage["tc"],
                "--openings", args.openings,
                "--min-openings", str(profile["minimum_openings"]),
                "--seed", str(seed), "--concurrency", str(args.concurrency),
                "--confidence", str(args.confidence),
                "--output", str(output_path), "--pgn", str(pgn_path),
            ]
            if stage["sprt"]:
                command += [
                    "--sprt-elo0", str(stage["sprt"]["elo0"]),
                    "--sprt-elo1", str(stage["sprt"]["elo1"]),
                    "--sprt-alpha", str(stage["sprt"]["alpha"]),
                    "--sprt-beta", str(stage["sprt"]["beta"]),
                ]
            relative_run = {
                "kind": "relative", "stage": stage["name"], **_run(command, output_path)
            }
            relative_run["decision"] = relative_decision(relative_run, stage)
            relative_run["profile_passed"] = relative_run["decision"]["passed"]
            plan["runs"].append(relative_run)

        stage_anchor_paths = []
        for anchor_index, anchor in enumerate(anchors):
            anchor_seed = seed + (anchor_index + 1) * 1_000_003
            slug = f"anchor-{anchor_index + 1}-{stage['name']}"
            output_path = result_dir / f"{slug}.json"
            pgn_path = pgn_dir / f"{slug}.pgn"
            command = [
                sys.executable, "research/run_anchor.py",
                "--engine", args.engine, "--config", args.config,
                "--anchor-engine", str(anchor["engine"]),
                "--anchor-name", str(anchor["name"]),
                "--anchor-family", str(anchor["family"]),
                "--anchor-elo", str(anchor["rating"]),
                "--games", str(stage["games"]), "--tc", stage["tc"],
                "--openings", args.openings,
                "--min-openings", str(profile["minimum_openings"]),
                "--seed", str(anchor_seed), "--concurrency", str(args.concurrency),
                "--confidence", str(args.confidence),
                "--output", str(output_path), "--pgn", str(pgn_path),
            ]
            if not anchor.get("default_stockfish_options", False):
                command.append("--anchor-no-default-options")
            for name, value in anchor.get("options", {}).items():
                command += ["--anchor-option", f"{name}={value}"]
            run = {"kind": "anchor", "stage": stage["name"], "anchor": anchor["name"],
                   **_run(command, output_path)}
            plan["runs"].append(run)
            if run["measurement_valid"]:
                stage_anchor_paths.append(str(output_path))
        if stage_anchor_paths:
            aggregate = aggregate_anchor_results(
                stage_anchor_paths,
                confidence=args.confidence,
                minimum_anchors=max(1, profile["minimum_anchors"]),
            )
            aggregate_path = result_dir / f"anchor-aggregate-{stage['name']}.json"
            write_json(str(aggregate_path), aggregate)
            aggregate_decision = (
                absolute_decision(aggregate, target_elo) if target_elo is not None else None
            )
            plan["runs"].append({
                "kind": "anchor_aggregate", "stage": stage["name"],
                "output": str(aggregate_path), "result": aggregate,
                "measurement_valid": aggregate["valid"],
                "decision": aggregate_decision,
                "profile_passed": aggregate_decision["passed"] if aggregate_decision else None,
            })

    plan["measurement_valid"] = bool(plan["runs"]) and all(
        run["measurement_valid"] for run in plan["runs"]
    )
    decisions = [
        run["profile_passed"] for run in plan["runs"]
        if isinstance(run.get("profile_passed"), bool)
    ]
    plan["profile_passed"] = bool(
        plan["measurement_valid"] and decisions and all(decisions)
    )
    plan["valid"] = plan["measurement_valid"]
    plan["reason"] = (
        "Measurements valid and profile criteria passed."
        if plan["profile_passed"] else
        "Measurements valid, but strength criteria rejected or remain inconclusive."
        if plan["measurement_valid"] else
        "One or more measurements failed integrity validation."
    )
    write_json(args.output, plan)
    write_json(str(result_dir / "summary.json"), plan)
    print(json.dumps(plan))
    return 0 if plan["profile_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
