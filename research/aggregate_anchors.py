"""Combine independent anchor families with gated random-effects estimation."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import NormalDist
from typing import Any

try:
    from harness import write_json
except ModuleNotFoundError:
    from research.harness import write_json


def aggregate_anchor_results(
    paths: list[str],
    *,
    confidence: float = 0.95,
    minimum_anchors: int = 3,
    require_independent_artifacts: bool = True,
    require_independent_families: bool = True,
    max_anchor_spread: float = 100.0,
    max_i_squared: float = 50.0,
) -> dict[str, Any]:
    """Combine valid v2 anchors with random-effects and heterogeneity gates."""
    if not paths:
        raise ValueError("at least one anchor result is required")
    if not 0.0 < confidence < 1.0:
        raise ValueError("confidence must be between 0 and 1")
    if minimum_anchors < 1:
        raise ValueError("minimum_anchors must be positive")
    if max_anchor_spread <= 0:
        raise ValueError("max_anchor_spread must be positive")
    if not 0.0 <= max_i_squared <= 100.0:
        raise ValueError("max_i_squared must be between 0 and 100")

    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, str]] = []
    for path in paths:
        payload = json.loads(Path(path).read_text(encoding="utf-8"))
        estimate = payload.get("checkforge_elo")
        se = (payload.get("results") or {}).get("elo_se")
        artifact_hash = (
            (payload.get("reproducibility") or {}).get("anchor_artifact") or {}
        ).get("sha256")
        raw_family = (payload.get("anchor") or {}).get("family")
        family = str(raw_family).strip().casefold() if raw_family else None
        if not payload.get("measurement_valid", payload.get("passed", False)):
            rejected.append({"path": path, "reason": "measurement is not valid"})
            continue
        if (
            isinstance(estimate, bool)
            or isinstance(se, bool)
            or not isinstance(estimate, (int, float))
            or not isinstance(se, (int, float))
            or not math.isfinite(float(estimate))
            or not math.isfinite(float(se))
            or se <= 0
        ):
            rejected.append({"path": path, "reason": "missing estimate or positive Elo SE"})
            continue
        accepted.append({
            "path": str(Path(path).resolve()),
            "name": (payload.get("anchor") or {}).get("name"),
            "family": family,
            "estimate": float(estimate),
            "elo_se": float(se),
            "artifact_sha256": artifact_hash,
            "time_control": payload.get("tc"),
        })

    artifact_hashes = {item["artifact_sha256"] for item in accepted if item["artifact_sha256"]}
    families = {item["family"] for item in accepted if item["family"]}
    validation_errors = []
    if len(accepted) < minimum_anchors:
        validation_errors.append(
            f"{len(accepted)} valid anchors; require at least {minimum_anchors}"
        )
    if require_independent_artifacts and len(artifact_hashes) < minimum_anchors:
        validation_errors.append(
            f"{len(artifact_hashes)} unique anchor binaries; require at least {minimum_anchors}"
        )
    if require_independent_artifacts and len(artifact_hashes) != len(accepted):
        validation_errors.append(
            "duplicate or missing anchor artifact rows cannot receive independent weight"
        )
    if require_independent_families and len(families) < minimum_anchors:
        validation_errors.append(
            f"{len(families)} independent anchor families; require at least {minimum_anchors}"
        )
    if require_independent_families and len(families) != len(accepted):
        validation_errors.append(
            "duplicate or missing anchor family rows cannot receive independent weight"
        )
    if not accepted:
        return {
            "benchmark": "anchor_aggregate",
            "valid": False,
            "confidence": confidence,
            "anchors": accepted,
            "rejected": rejected,
            "validation_errors": validation_errors,
        }

    fixed_weights = [1.0 / (item["elo_se"] ** 2) for item in accepted]
    fixed_weight_total = sum(fixed_weights)
    fixed_estimate = sum(
        weight * item["estimate"] for weight, item in zip(fixed_weights, accepted)
    ) / fixed_weight_total
    q = sum(
        weight * (item["estimate"] - fixed_estimate) ** 2
        for weight, item in zip(fixed_weights, accepted)
    )
    degrees_freedom = max(0, len(accepted) - 1)
    denominator = fixed_weight_total - sum(weight * weight for weight in fixed_weights) / fixed_weight_total
    tau_squared = max(0.0, (q - degrees_freedom) / denominator) if denominator > 0 else 0.0
    random_weights = [1.0 / (item["elo_se"] ** 2 + tau_squared) for item in accepted]
    random_weight_total = sum(random_weights)
    estimate = sum(
        weight * item["estimate"] for weight, item in zip(random_weights, accepted)
    ) / random_weight_total
    standard_error = math.sqrt(1.0 / random_weight_total)
    critical = NormalDist().inv_cdf((1.0 + confidence) / 2.0)
    margin = critical * standard_error
    spread = max(item["estimate"] for item in accepted) - min(
        item["estimate"] for item in accepted
    )
    i_squared = max(0.0, 100.0 * (q - degrees_freedom) / q) if q > 0 else 0.0
    if spread > max_anchor_spread:
        validation_errors.append(
            f"anchor spread {spread:.1f} Elo exceeds {max_anchor_spread:.1f} Elo gate"
        )
    if i_squared > max_i_squared:
        validation_errors.append(
            f"anchor heterogeneity I^2 {i_squared:.1f}% exceeds {max_i_squared:.1f}% gate"
        )
    return {
        "benchmark": "anchor_aggregate",
        "valid": not validation_errors,
        "method": "dersimonian_laird_random_effects",
        "confidence": confidence,
        "estimate": round(estimate, 1),
        "elo_se": round(standard_error, 1),
        "elo_ci": [round(estimate - margin, 1), round(estimate + margin, 1)],
        "elo_margin": round(margin, 1),
        "anchor_spread": round(spread, 1),
        "max_anchor_spread": max_anchor_spread,
        "heterogeneity_q": round(q, 3),
        "heterogeneity_df": degrees_freedom,
        "i_squared_percent": round(i_squared, 1),
        "max_i_squared_percent": max_i_squared,
        "tau_squared": round(tau_squared, 3),
        "unique_anchor_artifacts": len(artifact_hashes),
        "independent_anchor_families": len(families),
        "anchors": accepted,
        "rejected": rejected,
        "validation_errors": validation_errors,
        "calibration_warning": (
            "Random-effects CI excludes shared anchor-rating calibration bias and is not "
            "FIDE Elo. Heterogeneity gates reject discordant pools."
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("results", nargs="+")
    parser.add_argument("--output", default="results/anchor-aggregate.json")
    parser.add_argument("--confidence", type=float, default=0.95)
    parser.add_argument("--minimum-anchors", type=int, default=3)
    parser.add_argument("--allow-correlated-anchors", action="store_true")
    parser.add_argument("--max-anchor-spread", type=float, default=100.0)
    parser.add_argument("--max-i-squared", type=float, default=50.0)
    args = parser.parse_args()
    result = aggregate_anchor_results(
        args.results,
        confidence=args.confidence,
        minimum_anchors=args.minimum_anchors,
        require_independent_artifacts=not args.allow_correlated_anchors,
        require_independent_families=not args.allow_correlated_anchors,
        max_anchor_spread=args.max_anchor_spread,
        max_i_squared=args.max_i_squared,
    )
    write_json(args.output, result)
    print(json.dumps(result))
    return 0 if result["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
