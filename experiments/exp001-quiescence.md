# Experiment exp001-quiescence

## Hypothesis

Bounded quiescence search will reduce horizon mistakes in capture sequences without changing legal move generation.

## Change

Added configurable `quiescence_depth` and capture/promotion-only quiescence at leaf nodes. Default depth is 4.

## Files changed

- `engine/include/checkforge/config.h`
- `engine/src/config.cpp`
- `engine/src/search.cpp`
- `engine/tests/smoke_tests.cpp`
- `configs/default.json`

## Expected effect

Engine should avoid at least simple poisoned captures and keep perft unchanged.

## Risks

Search can slow down. Since engine has weak move ordering and no time management, deeper capture search may not improve match score yet.

## Tests run

- Perft: passed
- Tactical suite: 2/2 passed
- Speed: 1,939,553 nodes/sec in perft speed test
- Internal self-play: passed
- Fixed opponent: v000 baseline via cutechess, 40 games

## Results

```json
{
  "benchmark": "results/exp001-quiescence.json",
  "cutechess": "results/exp001-quiescence-cutechess.json",
  "score_vs_v000": "0 - 0 - 40 [0.500]",
  "draw_ratio": "100.0%",
  "accepted": true
}
```

## Decision

Accepted

## Reason

Correctness gates passed and explicit poisoned-pawn smoke test passed. Match score did not improve because both engines repeat heavily from weak opening/search behavior.

## Notes

Quiescence is useful infrastructure, but current match weakness is repeated rook/edge shuffling and no positional preference. Next experiments should target move choice in quiet positions.

## Next experiment idea

Add simple piece-square tables or mobility/development scoring to break sterile repetition and prefer normal development.
