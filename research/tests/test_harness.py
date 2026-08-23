"""Tests for reproducibility metadata helpers."""

from __future__ import annotations

import hashlib
import unittest
from pathlib import Path
from uuid import uuid4

from research.harness import base_metadata, file_metadata, prepare_opening_schedule


class HarnessMetadataTests(unittest.TestCase):
    def path(self, suffix: str) -> Path:
        path = Path(__file__).parent / f"_harness_{uuid4().hex}{suffix}"
        self.addCleanup(path.unlink, missing_ok=True)
        return path

    def test_file_metadata_hashes_and_counts_nonempty_lines(self) -> None:
        path = self.path(".epd")
        content = (
            "board-a w - - id one;\n\n"
            "board-b b KQ - id two;\n"
            "board-a w - - id duplicate-operation;\n"
        )
        path.write_text(content, encoding="utf-8")
        metadata = file_metadata(str(path), count_nonempty_lines=True)
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata["sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(metadata["nonempty_lines"], 3)
        self.assertEqual(metadata["unique_nonempty_lines"], 3)
        self.assertEqual(metadata["duplicate_nonempty_lines"], 0)
        self.assertEqual(metadata["unique_positions"], 2)
        self.assertEqual(metadata["duplicate_positions"], 1)
        self.assertTrue(metadata["exists"])

    def test_base_metadata_records_artifact_and_environment(self) -> None:
        engine = self.path(".bin")
        config = self.path(".json")
        engine.write_bytes(b"deterministic-engine")
        config.write_text("{}", encoding="utf-8")
        metadata = base_metadata(str(engine), str(config))
        self.assertEqual(metadata["schema_version"], 2)
        self.assertIsNotNone(metadata["engine_artifact"]["sha256"])
        self.assertIsNotNone(metadata["config"]["sha256"])
        self.assertIn("logical_cpus", metadata["environment"])
        self.assertIn("python", metadata["environment"])

    def test_opening_schedule_is_seeded_iid_and_recorded(self) -> None:
        source = self.path(".epd")
        first = self.path(".schedule.epd")
        second = self.path(".schedule.epd")
        source.write_text("a w - -\nb b - -\nc w - -\n", encoding="utf-8")
        first_meta = prepare_opening_schedule(str(source), str(first), pairs=20, seed=7)
        second_meta = prepare_opening_schedule(str(source), str(second), pairs=20, seed=7)
        self.assertEqual(first.read_bytes(), second.read_bytes())
        self.assertEqual(first_meta["sampling"], "iid_with_replacement_from_unique_epd_positions")
        self.assertEqual(first_meta["pairs"], 20)
        self.assertEqual(first_meta["schedule"]["nonempty_lines"], 20)


if __name__ == "__main__":
    unittest.main()
