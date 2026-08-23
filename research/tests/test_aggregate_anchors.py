"""Tests for multi-family random-effects anchor aggregation."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from uuid import uuid4

from research.aggregate_anchors import aggregate_anchor_results


class AggregateAnchorTests(unittest.TestCase):
    def path(self, suffix: str = ".json") -> Path:
        path = Path(__file__).parent / f"_anchor_{uuid4().hex}{suffix}"
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def test_combines_independent_anchor_results(self) -> None:
        paths = []
        for index, estimate in enumerate((2490.0, 2500.0, 2510.0)):
            path = self.path()
            path.write_text(json.dumps({
                "measurement_valid": True,
                "checkforge_elo": estimate,
                "results": {"elo_se": 10.0},
                "anchor": {"name": f"anchor-{index}", "family": f"family-{index}"},
                "reproducibility": {"anchor_artifact": {"sha256": f"hash-{index}"}},
                "tc": "60+0.6",
            }), encoding="utf-8")
            paths.append(str(path))
        result = aggregate_anchor_results(paths)
        self.assertTrue(result["valid"])
        self.assertEqual(result["estimate"], 2500.0)
        self.assertEqual(result["unique_anchor_artifacts"], 3)
        self.assertEqual(result["independent_anchor_families"], 3)
        self.assertLess(result["elo_margin"], 20.0)

    def test_rejects_correlated_or_invalid_anchors(self) -> None:
        paths = []
        for index in range(3):
            path = self.path()
            path.write_text(json.dumps({
                "measurement_valid": index != 2,
                "checkforge_elo": 2500.0,
                "results": {"elo_se": 10.0},
                "anchor": {"family": "same-family"},
                "reproducibility": {"anchor_artifact": {"sha256": "same"}},
            }), encoding="utf-8")
            paths.append(str(path))
        result = aggregate_anchor_results(paths, minimum_anchors=2)
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["anchors"]), 2)
        self.assertEqual(result["unique_anchor_artifacts"], 1)
        self.assertEqual(len(result["rejected"]), 1)

    def test_rejects_discordant_anchor_pool(self) -> None:
        paths = []
        for index, estimate in enumerate((1500.0, 2500.0, 3500.0)):
            path = self.path()
            path.write_text(json.dumps({
                "measurement_valid": True,
                "checkforge_elo": estimate,
                "results": {"elo_se": 1.0},
                "anchor": {"name": f"anchor-{index}", "family": f"family-{index}"},
                "reproducibility": {"anchor_artifact": {"sha256": f"hash-{index}"}},
            }), encoding="utf-8")
            paths.append(str(path))
        result = aggregate_anchor_results(paths)
        self.assertFalse(result["valid"])
        self.assertGreater(result["tau_squared"], 0.0)
        self.assertTrue(any("spread" in error for error in result["validation_errors"]))
        self.assertTrue(any("heterogeneity" in error for error in result["validation_errors"]))

    def test_duplicate_family_cannot_gain_extra_weight(self) -> None:
        paths = []
        for index, family in enumerate(("family-a", "family-a", "family-b", "family-c")):
            path = self.path()
            path.write_text(json.dumps({
                "measurement_valid": True,
                "checkforge_elo": 2500.0,
                "results": {"elo_se": 10.0},
                "anchor": {"name": f"anchor-{index}", "family": family},
                "reproducibility": {"anchor_artifact": {"sha256": f"hash-{index}"}},
            }), encoding="utf-8")
            paths.append(str(path))
        result = aggregate_anchor_results(paths, minimum_anchors=3)
        self.assertFalse(result["valid"])
        self.assertTrue(any("duplicate or missing anchor family" in error
                            for error in result["validation_errors"]))


if __name__ == "__main__":
    unittest.main()
