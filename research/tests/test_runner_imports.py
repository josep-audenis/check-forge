"""Package-mode imports must resolve scorer before any long match starts."""

from __future__ import annotations

import unittest

from research import run_anchor, run_cutechess, score_pgn


class RunnerImportTests(unittest.TestCase):
    def test_cutechess_runner_uses_package_scorer(self) -> None:
        self.assertIs(run_cutechess.score_pgn, score_pgn.score_pgn)

    def test_anchor_runner_uses_package_scorer(self) -> None:
        self.assertIs(run_anchor.score_pgn, score_pgn.score_pgn)


if __name__ == "__main__":
    unittest.main()
