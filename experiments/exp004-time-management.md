# Experiment exp004-time-management

## Hypothesis

Using shallower search under UCI time controls will avoid clock losses after exp003 reduces repetitions.

## Change

Temporarily changed `go wtime/btime/movetime` handling to cap search at depth 1 or 2.

## Files changed

- `engine/src/uci.cpp`
- `engine/tests/smoke_tests.cpp`

## Expected effect

Engine should stop losing on time in fast cutechess games.

## Risks

Depth reduction can make the engine tactically helpless.

## Tests run

- Perft: passed
- Tactical suite: 2/2 passed
- Speed: 1,892,886 nodes/sec in perft speed test
- Self-play: passed
- Fixed opponent: v002 positional eval via cutechess, 60 games at `1+0.05`

## Results

```json
{
  "benchmark": "results/exp004-time-management.json",
  "cutechess": "results/exp004-time-management-cutechess.json",
  "score_vs_v002": "0 - 60 - 0 [0.000]",
  "failure_mode": "lost every game by mate",
  "accepted": false
}
```

## Decision

Rejected

## Reason

Clock losses disappeared, but playing strength collapsed. Change was reverted after saving `versions/v004-rejected-time-management`.

## Notes

Naive depth cap is too crude. Future time management needs iterative deepening or a smaller search improvement, not hard depth reduction.

## Next experiment idea

Improve tactical strength with check extension or mate detection before retrying time management.
