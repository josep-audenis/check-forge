# Experiment exp003-avoid-reversal

## Hypothesis

Avoiding immediate reversal of the previous own move in UCI root selection will reduce threefold repetition loops.

## Change

Added UCI move-history tracking and root search fallback that excludes the direct reverse of the previous own move when an alternative legal move exists.

## Files changed

- `engine/include/checkforge/config.h`
- `engine/src/config.cpp`
- `engine/include/checkforge/search.h`
- `engine/src/search.cpp`
- `engine/include/checkforge/uci.h`
- `engine/src/uci.cpp`
- `engine/tests/smoke_tests.cpp`
- `configs/default.json`

## Expected effect

Engine should play longer non-repeating games against v002.

## Risks

If games no longer end by repetition, current UCI time handling may be exposed as too slow.

## Tests run

- Perft: passed
- Tactical suite: 2/2 passed
- Speed: 1,915,493 nodes/sec in perft speed test
- Self-play: passed
- Fixed opponent: v002 positional eval via cutechess, 40 games at `1+0.05`

## Results

```json
{
  "benchmark": "results/exp003-avoid-reversal.json",
  "cutechess": "results/exp003-avoid-reversal-cutechess.json",
  "score_vs_v002": "20 - 20 - 0 [0.500]",
  "draw_ratio": "0.0%",
  "failure_mode": "all games lost by White on time",
  "accepted": false
}
```

## Decision

Needs more testing

## Reason

Correctness gates passed and repetition was reduced, but cutechess exposed clock losses. Need UCI time management before judging strength.

## Notes

The change likely fixes repetition pressure, but current default depth under time controls is too slow once games continue.

## Next experiment idea

Add basic UCI time-control depth cap for `go wtime/btime/movetime`.
