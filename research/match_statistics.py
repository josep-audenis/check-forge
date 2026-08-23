"""Deterministic, dependency-free statistics for paired engine matches.

Each sample is one independent unit in ``[0, 1]``.  For paired games, callers
must first average both game scores, so colour-paired games are not counted
twice.
"""

from __future__ import annotations

from collections.abc import Iterable
from math import exp, isfinite, log, log10, sqrt
from statistics import NormalDist, fmean, stdev
from typing import Any

_ELO_SCALE = 400.0
_LN10 = log(10.0)
_PENTANOMIAL_LABELS = ("LL", "LD", "DD+WL", "WD", "WW")
_PENTANOMIAL_TOTALS = (0.0, 0.5, 1.0, 1.5, 2.0)


def _finite_number(value: object, name: str) -> float:
    """Return finite numeric value or raise ``ValueError``."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name} must be a finite number")
    number = float(value)
    if not isfinite(number):
        raise ValueError(f"{name} must be a finite number")
    return number


def _samples(samples: Iterable[float]) -> list[float]:
    """Validate and materialize independent score samples."""
    values = [_finite_number(value, "sample") for value in samples]
    if not values:
        raise ValueError("samples must not be empty")
    if any(value < 0.0 or value > 1.0 for value in values):
        raise ValueError("samples must be in [0, 1]")
    return values


def _confidence(confidence: float) -> float:
    """Validate confidence strictly between zero and one."""
    value = _finite_number(confidence, "confidence")
    if not 0.0 < value < 1.0:
        raise ValueError("confidence must be in (0, 1)")
    return value


def elo_from_score(score: float) -> float | None:
    """Convert expected score to Elo difference; return ``None`` at 0 or 1."""
    value = _finite_number(score, "score")
    if value < 0.0 or value > 1.0:
        raise ValueError("score must be in [0, 1]")
    if value == 0.0 or value == 1.0:
        return None
    return _ELO_SCALE * log10(value / (1.0 - value))


def score_from_elo(elo: float) -> float:
    """Convert Elo difference to expected score using logistic Elo model."""
    value = _finite_number(elo, "elo")
    # Stable enough for finite floats; branch avoids overflow for extreme Elo.
    exponent = -value * _LN10 / _ELO_SCALE
    if exponent > 700.0:
        return 0.0
    if exponent < -700.0:
        return 1.0
    return 1.0 / (1.0 + exp(exponent))


def _elo_standard_error(score: float, score_se: float) -> float | None:
    """Delta-method Elo SE, undefined at score boundaries."""
    if score <= 0.0 or score >= 1.0:
        return None
    return _ELO_SCALE * score_se / (_LN10 * score * (1.0 - score))


def summarize_samples(samples: Iterable[float], confidence: float = 0.95) -> dict[str, Any]:
    """Summarize independent scores with explicitly labeled normal CI.

    Non-zero sample variance with at least two samples uses a normal
    approximation.  Single-sample and zero-variance cases use a conservative
    Hoeffding interval for bounded samples instead of claiming zero uncertainty.
    """
    values = _samples(samples)
    level = _confidence(confidence)
    count = len(values)
    mean = fmean(values)
    sample_se = stdev(values) / sqrt(count) if count > 1 else 0.0
    if count > 1 and sample_se > 0.0:
        method = "normal_approximation"
        critical = NormalDist().inv_cdf((1.0 + level) / 2.0)
        half_width = critical * sample_se
    else:
        method = "hoeffding_conservative_fallback"
        half_width = sqrt(log(2.0 / (1.0 - level)) / (2.0 * count))
    score_ci = (max(0.0, mean - half_width), min(1.0, mean + half_width))
    elo = elo_from_score(mean)
    elo_se = _elo_standard_error(mean, sample_se)
    elo_ci = (elo_from_score(score_ci[0]), elo_from_score(score_ci[1]))
    elo_margin = None
    if elo is not None and None not in elo_ci:
        elo_margin = max(abs(elo - elo_ci[0]), abs(elo_ci[1] - elo))
    elo_margin_95 = None if elo_se is None or method != "normal_approximation" else (
        NormalDist().inv_cdf(0.975) * elo_se
    )
    return {
        "sample_count": count,
        "mean_score": mean,
        "score_se": sample_se,
        "confidence_level": level,
        "confidence_method": method,
        "score_ci": score_ci,
        "elo": elo,
        "elo_se": elo_se,
        "elo_ci": elo_ci,
        "elo_margin": elo_margin,
        "elo_margin_95": elo_margin_95,
    }


def pentanomial_counts(pair_totals: Iterable[float]) -> dict[str, Any]:
    """Count paired-game totals in conventional pentanomial order.

    ``DD+WL`` combines either two draws or one win and one loss, both totaling
    one point from a two-game colour pair.
    """
    counts = [0, 0, 0, 0, 0]
    for total in pair_totals:
        value = _finite_number(total, "pair total")
        try:
            index = _PENTANOMIAL_TOTALS.index(value)
        except ValueError as exc:
            raise ValueError("pair totals must be one of 0, 0.5, 1, 1.5, 2") from exc
        counts[index] += 1
    return {"labels": list(_PENTANOMIAL_LABELS), "counts": counts,
            **dict(zip(_PENTANOMIAL_LABELS, counts, strict=True))}


def sprt_snapshot(
    samples: Iterable[float], elo0: float, elo1: float, alpha: float = 0.05, beta: float = 0.05
) -> dict[str, Any]:
    """Run an anytime-valid sequential test over independent paired scores.

    This is not Cute Chess's game-level trinomial SPRT. Each bounded sample is
    one colour-swapped opening-pair average. Hoeffding e-processes test the
    composite hypotheses ``mean <= score(elo0)`` and ``mean >= score(elo1)``.
    The first boundary crossing is retained, so optional stopping controls the
    wrong-decision probabilities at ``alpha`` and ``beta`` without estimating
    a variance or assuming a within-pair outcome distribution.
    """
    values = _samples(samples)
    null_elo = _finite_number(elo0, "elo0")
    alt_elo = _finite_number(elo1, "elo1")
    if null_elo >= alt_elo:
        raise ValueError("elo0 must be less than elo1")
    alpha_value = _confidence(alpha)
    beta_value = _confidence(beta)
    if alpha_value + beta_value >= 1.0:
        raise ValueError("alpha + beta must be less than 1")
    mean0 = score_from_elo(null_elo)
    mean1 = score_from_elo(alt_elo)
    gap = mean1 - mean0
    tuning = 4.0 * gap
    h0_threshold = log(1.0 / alpha_value)
    h1_threshold = log(1.0 / beta_value)
    running_sum = 0.0
    status = "continue"
    decision_sample = None
    log_e_against_h0 = 0.0
    log_e_against_h1 = 0.0
    for count, value in enumerate(values, start=1):
        running_sum += value
        penalty = count * tuning * tuning / 8.0
        log_e_against_h0 = tuning * (running_sum - count * mean0) - penalty
        log_e_against_h1 = tuning * (count * mean1 - running_sum) - penalty
        reject_h0 = log_e_against_h0 >= h0_threshold
        reject_h1 = log_e_against_h1 >= h1_threshold
        if reject_h0 or reject_h1:
            status = "accept_h1" if reject_h0 and not reject_h1 else (
                "accept_h0" if reject_h1 and not reject_h0 else "conflicting"
            )
            decision_sample = count
            break
    return {
        "method": "paired_hoeffding_e_process",
        "guarantee": "anytime-valid for independent bounded opening-pair scores",
        "available_samples": len(values),
        "sample_count": decision_sample or len(values),
        "decision_sample": decision_sample,
        "mean_score": fmean(values[:decision_sample] if decision_sample else values),
        "elo0": null_elo,
        "elo1": alt_elo,
        "score0": mean0,
        "score1": mean1,
        "alpha": alpha_value,
        "beta": beta_value,
        "log_e_against_h0": log_e_against_h0,
        "log_e_against_h1": log_e_against_h1,
        "h0_rejection_threshold": h0_threshold,
        "h1_rejection_threshold": h1_threshold,
        "status": status,
    }
