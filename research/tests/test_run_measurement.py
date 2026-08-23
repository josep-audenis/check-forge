"""Tests for measurement profile preflight and anchor configuration."""

from __future__ import annotations

import json
import unittest
from pathlib import Path
from uuid import uuid4

from research.run_measurement import (
    PROFILES,
    absolute_decision,
    load_anchors,
    preflight,
    relative_decision,
)


class RunMeasurementTests(unittest.TestCase):
    def path(self, suffix: str) -> Path:
        path = Path(__file__).parent / f"_measurement_{uuid4().hex}{suffix}"
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def test_screen_profile_accepts_current_scale_suite_and_baseline(self) -> None:
        engine = self.path(".exe")
        baseline = self.path(".exe")
        openings = self.path(".epd")
        engine.write_bytes(b"candidate")
        baseline.write_bytes(b"baseline")
        openings.write_text("\n".join(f"fen-{index}" for index in range(12)), encoding="utf-8")
        errors, metadata = preflight(
            PROFILES["screen"], str(openings), str(engine), str(baseline), []
        )
        self.assertEqual(errors, [])
        self.assertEqual(metadata["openings"]["nonempty_lines"], 12)
        self.assertEqual(metadata["openings"]["unique_positions"], 12)

    def test_profile_rejects_duplicated_openings(self) -> None:
        engine = self.path(".exe")
        baseline = self.path(".exe")
        openings = self.path(".epd")
        engine.write_bytes(b"candidate")
        baseline.write_bytes(b"baseline")
        openings.write_text("\n".join(["fen-a"] * 12), encoding="utf-8")
        errors, metadata = preflight(
            PROFILES["screen"], str(openings), str(engine), str(baseline), []
        )
        self.assertTrue(any("1 unique positions" in error for error in errors))
        self.assertEqual(metadata["openings"]["duplicate_positions"], 11)

    def test_claim_profile_requires_large_suite_and_three_independent_anchors(self) -> None:
        engine = self.path(".exe")
        anchor = self.path(".exe")
        openings = self.path(".epd")
        engine.write_bytes(b"candidate")
        anchor.write_bytes(b"same-anchor")
        openings.write_text("fen\n", encoding="utf-8")
        anchors = [
            {
                "name": f"anchor-{index}",
                "family": "same-family",
                "engine": str(anchor),
                "rating": 2500,
            }
            for index in range(3)
        ]
        errors, _ = preflight(
            PROFILES["claim"], str(openings), str(engine), None, anchors
        )
        self.assertTrue(any("profile requires 500" in error for error in errors))
        self.assertTrue(any("unique anchor binaries" in error for error in errors))
        self.assertTrue(any("independent anchor families" in error for error in errors))

    def test_load_anchors_validates_schema(self) -> None:
        path = self.path(".json")
        path.write_text(json.dumps({"anchors": [{"name": "x"}]}), encoding="utf-8")
        with self.assertRaises(ValueError):
            load_anchors(str(path))

    def test_relative_decision_rejects_valid_h0_and_inconclusive_runs(self) -> None:
        stage = PROFILES["screen"]["stages"][0]
        for status in ("accept_h0", "continue"):
            run = {
                "measurement_valid": True,
                "result": {"results": {"sprt": {
                    "status": status,
                    "method": "paired_hoeffding_e_process",
                }}},
            }
            self.assertFalse(relative_decision(run, stage)["passed"])
        run["result"]["results"]["sprt"]["status"] = "accept_h1"
        self.assertTrue(relative_decision(run, stage)["passed"])

    def test_absolute_decision_requires_lower_bound_to_clear_target(self) -> None:
        self.assertFalse(absolute_decision({"valid": True, "elo_ci": [2499, 2600]}, 2500)["passed"])
        self.assertTrue(absolute_decision({"valid": True, "elo_ci": [2500, 2600]}, 2500)["passed"])


if __name__ == "__main__":
    unittest.main()
