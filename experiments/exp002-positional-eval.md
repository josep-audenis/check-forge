# Experiment exp002-positional-eval

## Hypothesis

Small positional terms will stop equal-material opening moves from degenerating into edge-pawn pushes.

## Change

Added static search evaluation with simple piece-square and development bonuses. Material-only `--eval` remains unchanged.

## Files changed

- `engine/include/checkforge/eval.h`
- `engine/src/eval.cpp`
- `engine/src/search.cpp`
- `engine/tests/smoke_tests.cpp`

## Expected effect

Engine should prefer developing knights and bishops over random edge-pawn moves.

## Risks

Naive piece-square scoring can create new loops if one or two squares dominate quiet evaluation.

## Tests run

- Perft: passed
- Tactical suite: 2/2 passed
- Speed: 1,918,532 nodes/sec in perft speed test
- Self-play: passed
- Fixed opponent: v001 quiescence via cutechess, 60 games

## Results

```json
{
  "benchmark": "results/exp002-positional-eval.json",
  "cutechess": "results/exp002-positional-eval-cutechess.json",
  "score_vs_v001": "0 - 0 - 60 [0.500]",
  "draw_ratio": "100.0%",
  "accepted": true
}
```

## Decision

Accepted

## Reason

Correctness gates passed and opening play changed from edge-pawn pushes to development. No Elo gain yet because both engines still repeat positions.

## Notes

Main weak point is immediate piece reversal and threefold repetition. Need anti-repetition behavior or search history before more eval tuning.

## Next experiment idea

Avoid immediate reversal of previous own move in UCI root move selection.
