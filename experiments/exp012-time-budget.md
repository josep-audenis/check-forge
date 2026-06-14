# Experiment exp012-time-budget

## Hypothesis

v008 never flagged in 30 games, suggesting spare time. Spending a larger share of
the clock (`remaining/20 + full increment` instead of `remaining/30 + 3/4·inc`)
should reach more depth and gain Elo without flagging.

## Change

`engine/src/uci.cpp` `time_budget_ms`: budget raised to `remaining/20 + increment`.

## Files changed

- `engine/src/uci.cpp` (reverted after rejection)

## Tests run

- Unit tests: 1/1 passed
- Benchmark vs v008: accepted
- Cutechess vs v008: 40 games, tc=4+0.1, varied openings

## Results

```json
{
  "cutechess": "results/exp012-time-budget-cutechess.json",
  "score_vs_v008": "7 - 18 - 15",
  "elo_diff": -98.1,
  "elo_err": 88.5,
  "los": "1.4%",
  "time_losses": 11,
  "accepted": false
}
```

## Decision

Rejected

## Reason

The more aggressive budget **flagged 11 of 40 games** and lost significantly
(-98 Elo, LOS 1.4%). The earlier "geometric, never exhausts" reasoning ignored
move overhead and the fact that the increment at bullet TC (0.1 s) is tiny relative
to the extra spend. v008's `remaining/30 + 3/4·inc` is the flag-safe operating point
for this TC. Reverted.

## Notes

Second consecutive rejection (with exp011). Conclusion: at 4+0.1, v008 is near the
time-management optimum — additional depth cannot be bought with more clock without
flagging. Real strength gains now require a **faster search** (same depth, fewer
nodes) rather than more time. The canonical tool is a transposition table.

## Next experiment idea

Add a transposition table so previously searched positions are reused, letting
iterative deepening reach greater depth within the same flag-safe budget. Gate with
perft, the 8-case tactics suite, and cutechess illegal-move detection.
