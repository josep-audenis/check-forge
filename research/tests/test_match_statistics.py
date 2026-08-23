"""Tests for :mod:`research.match_statistics`."""

from __future__ import annotations

import math
import unittest

from research.match_statistics import (
    elo_from_score,
    pentanomial_counts,
    score_from_elo,
    sprt_snapshot,
    summarize_samples,
)


class MatchStatisticsTests(unittest.TestCase):
    def test_elo_round_trip_and_boundaries(self) -> None:
        self.assertEqual(elo_from_score(0.5), 0.0)
        self.assertAlmostEqual(score_from_elo(100.0), 0.6400649998, places=9)
        self.assertAlmostEqual(elo_from_score(score_from_elo(-75.0)) or 0.0, -75.0, places=10)
        self.assertIsNone(elo_from_score(0.0))
        self.assertIsNone(elo_from_score(1.0))

    def test_balanced_summary_uses_conservative_fallback(self) -> None:
        summary = summarize_samples([0.5] * 100)
        self.assertEqual(summary["sample_count"], 100)
        self.assertEqual(summary["mean_score"], 0.5)
        self.assertEqual(summary["score_se"], 0.0)
        self.assertEqual(summary["confidence_method"], "hoeffding_conservative_fallback")
        self.assertLess(summary["score_ci"][0], 0.5)
        self.assertGreater(summary["score_ci"][1], 0.5)
        self.assertEqual(summary["elo"], 0.0)
        self.assertGreater(summary["elo_margin"] or 0.0, 0.0)
        self.assertIsNone(summary["elo_margin_95"])

    def test_winning_summary_uses_normal_approximation(self) -> None:
        summary = summarize_samples([1.0, 0.75, 0.5, 1.0])
        self.assertEqual(summary["confidence_method"], "normal_approximation")
        self.assertAlmostEqual(summary["mean_score"], 0.8125)
        self.assertGreater(summary["score_se"], 0.0)
        self.assertGreater(summary["elo"] or 0.0, 0.0)

    def test_boundary_summary_is_safe(self) -> None:
        summary = summarize_samples([1.0, 1.0])
        self.assertIsNone(summary["elo"])
        self.assertIsNone(summary["elo_se"])
        self.assertIsNone(summary["elo_ci"][1])
        self.assertIsNone(summary["elo_margin_95"])

    def test_pentanomial_counts(self) -> None:
        actual = pentanomial_counts([0, 0.5, 1, 1, 1.5, 2])
        self.assertEqual(actual["labels"], ["LL", "LD", "DD+WL", "WD", "WW"])
        self.assertEqual(actual["counts"], [1, 1, 2, 1, 1])
        self.assertEqual(actual["DD+WL"], 2)

    def test_invalid_inputs(self) -> None:
        with self.assertRaises(ValueError):
            summarize_samples([])
        with self.assertRaises(ValueError):
            summarize_samples([1.1])
        with self.assertRaises(ValueError):
            summarize_samples([0.5], confidence=1.0)
        with self.assertRaises(ValueError):
            pentanomial_counts([0.25])
        with self.assertRaises(ValueError):
            sprt_snapshot([0.5, 0.6], 0, 0)
        with self.assertRaises(ValueError):
            sprt_snapshot([0.5, 0.6], 10, 0)
        with self.assertRaises(ValueError):
            sprt_snapshot([0.5, 0.6], 0, 10, alpha=0.6, beta=0.4)
        with self.assertRaises(ValueError):
            elo_from_score(math.nan)

    def test_sprt_accepts_both_directions(self) -> None:
        wins = [0.8, 0.9] * 20
        losses = [0.1, 0.2] * 20
        accept_h1 = sprt_snapshot(wins, 0.0, 100.0)
        accept_h0 = sprt_snapshot(losses, 0.0, 100.0)
        self.assertEqual(accept_h1["method"], "paired_hoeffding_e_process")
        self.assertEqual(accept_h1["status"], "accept_h1")
        self.assertEqual(accept_h0["status"], "accept_h0")

    def test_sequential_test_handles_zero_variance(self) -> None:
        snapshot = sprt_snapshot([0.5, 0.5], 0.0, 50.0)
        self.assertEqual(snapshot["status"], "continue")
        self.assertEqual(snapshot["method"], "paired_hoeffding_e_process")
        self.assertIsNone(snapshot["decision_sample"])

    def test_sequential_test_retains_first_crossing(self) -> None:
        snapshot = sprt_snapshot([1.0] * 200 + [0.0] * 200, 0.0, 20.0)
        self.assertEqual(snapshot["status"], "accept_h1")
        self.assertLess(snapshot["decision_sample"], snapshot["available_samples"])


if __name__ == "__main__":
    unittest.main()
