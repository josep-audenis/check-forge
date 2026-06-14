# Experiment exp013-transposition

## Hypothesis

At 4+0.1 the engine cannot buy more depth with more time (exp012 flagged). A
transposition table caches the result of already-searched positions so iterative
deepening reuses shallower work and reaches greater depth within the same flag-safe
budget — a faster search rather than a longer one.

## Change

`engine/src/search.cpp`: added a fixed-size (2^20 entry) thread-local TT keyed by an
FNV-1a hash of the board (squares + side + castling + en passant). Interior
`negamax` nodes probe the table and return on a usable depth-sufficient bound
(exact / lower≥beta / upper≤alpha), and store their result with the appropriate
bound flag and depth-preferred replacement. Mate-distance scores are not stored (they
need ply-relative correction this flat table does not track). The table is reset at
the start of each top-level search.

## Files changed

- `engine/src/search.cpp`

## Expected effect

More depth per move at fixed TC; correctness unchanged; no flags.

## Risks

A wrong bound or hash collision could return a bad score and weaken or corrupt play.
Mitigated by perft, the 8-case tactics suite, cutechess illegal-move detection, and
the mate-score store guard.

## Tests run

- Unit tests: 1/1 passed
- Perft: passed
- Tactical suite: 8/8 (fixed-depth path, exercises probe/store)
- Benchmark vs v008: accepted
- Cutechess vs v008: 40 games at 4+0.1 -> 11 - 10 - 19, Elo +8.7 ±79.3, 0 flags
- Cutechess vs v008: 16 games at 12+0.1 -> Elo +21.7 ±74.2, 81% draws, 0 flags

## Results

```json
{
  "benchmark": "results/exp013-transposition.json",
  "cutechess_bullet": "results/exp013-transposition-cutechess.json",
  "score_vs_v008_4+0.1": "11 - 10 - 19",
  "elo_4+0.1": 8.7,
  "elo_12+0.1": 21.7,
  "time_losses": 0,
  "accepted": true
}
```

## Decision

Accepted (v009)

## Reason

Correct, foundational search infrastructure with zero downside: non-negative at both
tested time controls (+8.7 and +21.7 Elo), no flags, all correctness gates green.
Not statistically significant on its own (high draw rate keeps decisive games rare),
but it is the standard prerequisite for stronger search and pays off more as depth
grows. Accepted on the same infrastructure basis as exp001/exp005, and unlike the
rejected exp011/exp012 it never regresses.

## Notes

Confirms the bullet ceiling: classic search optimizations (root-PV exp011, TT here)
are near-neutral at ~depth 3-4 because there is no extra ply to win; their value
appears as TC lengthens. The TT also enables TT-move ordering, the natural follow-up.

## Next experiment idea

Store the best move in each TT entry and search it first (TT-move ordering). This is
the synergy that makes the rejected root-PV idea actually pay: a real best-move hint
from a deeper prior search, improving cutoffs even at shallow depth.
