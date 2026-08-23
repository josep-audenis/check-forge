"""Unit tests for robust PGN scoring and pair validation."""

from __future__ import annotations

import unittest
from pathlib import Path
from uuid import uuid4

from research.score_pgn import score_pgn


def game(round_id: int, white: str, black: str, result: str, fen: str, termination: str = "normal") -> str:
    return f'''[Event "test"]
[Round "{round_id}"]
[White "{white}"]
[Black "{black}"]
[Result "{result}"]
[FEN "{fen}"]
[Termination "{termination}"]

{result}

'''


class ScorePgnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path(__file__).parent / f"_score_{uuid4().hex}.pgn"
        self.addCleanup(self.path.unlink, missing_ok=True)

    def write(self, text: str) -> str:
        self.path.write_text(text, encoding="utf-8")
        return str(self.path)

    def test_scores_complete_colour_pairs_and_pentanomial(self) -> None:
        path = self.write(
            game(1, "CheckForge", "opponent", "1-0", "fen-a")
            + game(1, "opponent", "CheckForge", "0-1", "fen-a")
            + game(2, "CheckForge", "opponent", "0-1", "fen-b")
            + game(2, "opponent", "CheckForge", "1/2-1/2", "fen-b")
        )
        result = score_pgn(path, "checkforge", expected_games=4, require_pairs=True)
        self.assertTrue(result["valid"])
        self.assertEqual((result["wins"], result["losses"], result["draws"]), (2, 1, 1))
        self.assertEqual(result["pairing"]["pairs"], 2)
        self.assertEqual(result["pairing"]["pentanomial"]["counts"], [0, 1, 0, 0, 1])
        self.assertEqual(result["pairing"]["confidence_unit"], "opening_pair")
        self.assertEqual(result["elo_error_confidence"], 0.95)

    def test_rejects_pair_with_different_openings(self) -> None:
        path = self.write(
            game(1, "checkforge", "opponent", "1-0", "fen-a")
            + game(1, "opponent", "checkforge", "0-1", "fen-b")
        )
        result = score_pgn(path, require_pairs=True)
        self.assertFalse(result["valid"])
        self.assertFalse(result["pairing"]["complete"])
        self.assertIn("paired opening validation failed", result["validation_errors"][-1])

    def test_rejects_unfinished_and_unrelated_games(self) -> None:
        path = self.write(
            game(1, "checkforge", "opponent", "*", "fen-a")
            + game(2, "other", "opponent", "1-0", "fen-b")
        )
        result = score_pgn(path)
        self.assertFalse(result["valid"])
        self.assertEqual(result["games"], 0)
        self.assertEqual(len(result["rejected_games"]), 2)

    def test_engine_time_loss_is_validation_failure(self) -> None:
        path = self.write(game(1, "checkforge", "opponent", "0-1", "fen-a", "time forfeit"))
        result = score_pgn(path)
        self.assertFalse(result["valid"])
        self.assertEqual(result["time_forfeits"], 1)
        self.assertEqual(result["engine_time_losses"], 1)

    def test_opponent_time_loss_is_also_validation_failure(self) -> None:
        path = self.write(game(1, "checkforge", "opponent", "1-0", "fen-a", "time forfeit"))
        result = score_pgn(path)
        self.assertFalse(result["valid"])
        self.assertEqual(result["opponent_time_losses"], 1)

    def test_expected_game_count_is_enforced(self) -> None:
        path = self.write(game(1, "checkforge", "opponent", "1/2-1/2", "fen-a"))
        result = score_pgn(path, expected_games=2)
        self.assertFalse(result["valid"])
        self.assertIn("completed 1 games; expected 2", result["validation_errors"])

    def test_sequential_test_requires_complete_pairs(self) -> None:
        path = self.write(game(1, "checkforge", "opponent", "1-0", "fen-a"))
        result = score_pgn(path, sprt={"elo0": 0.0, "elo1": 20.0})
        self.assertFalse(result["valid"])
        self.assertNotIn("sprt", result)
        self.assertTrue(any("sequential test requires" in error for error in result["validation_errors"]))

    def test_preassigned_opening_schedule_must_match_pair_order(self) -> None:
        path = self.write(
            game(1, "checkforge", "opponent", "1-0", "fen-a")
            + game(1, "opponent", "checkforge", "0-1", "fen-a")
            + game(2, "checkforge", "opponent", "1/2-1/2", "fen-b")
            + game(2, "opponent", "checkforge", "1/2-1/2", "fen-b")
        )
        schedule = Path(__file__).parent / f"_schedule_{uuid4().hex}.epd"
        self.addCleanup(schedule.unlink, missing_ok=True)
        schedule.write_text("fen-b\nfen-a\n", encoding="utf-8")
        result = score_pgn(path, require_pairs=True, opening_schedule=str(schedule))
        self.assertFalse(result["valid"])
        self.assertEqual(len(result["pairing"]["schedule_validation"]["mismatches"]), 2)

    def test_sequential_test_rejects_unverified_pair_source(self) -> None:
        path = self.write(
            game(1, "checkforge", "opponent", "1-0", "fen-a")
            + game(1, "opponent", "checkforge", "0-1", "fen-a")
        )
        result = score_pgn(
            path,
            require_pairs=True,
            sprt={"elo0": 0.0, "elo1": 20.0},
        )
        self.assertFalse(result["valid"])
        self.assertNotIn("sprt", result)
        self.assertTrue(any("preassigned opening schedule" in error
                            for error in result["validation_errors"]))


if __name__ == "__main__":
    unittest.main()
