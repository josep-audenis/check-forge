# Experiment exp014-tt-move-ordering

## Hypothesis

The TT (v009) stores a score but discards the best move. Storing that move and
searching it first should improve alpha-beta cutoffs — the synergy that makes the
rejected standalone root-PV (exp011) actually pay, because the hint now comes from a
deeper prior search.

## Change

`engine/src/search.cpp`: `TTEntry` gains a `best` move. `negamax` records the best
move and stores it; on probe it pulls the TT move as an ordering hint (even when the
bound is unusable) and promotes it to the front after MVV-LVA. `search_root` does the
same at the root. Added `same_move` / `promote_move_to_front` helpers.

## Files changed

- `engine/src/search.cpp`

## Expected effect

Better ordering -> earlier cutoffs -> occasionally more depth; correctness unchanged.

## Tests run

- Unit tests: 1/1 passed
- Tactical suite: 8/8 (fixed-depth path)
- Benchmark vs v009: accepted
- Cutechess vs v009: 40 games at 4+0.1 -> 7 - 8 - 25, Elo -8.7 ±66.6, 0 flags, 62.5% draws

## Results

```json
{
  "benchmark": "results/exp014-tt-move-ordering.json",
  "cutechess": "results/exp014-tt-move-ordering-cutechess.json",
  "score_vs_v009": "7 - 8 - 25",
  "elo_diff": -8.7,
  "elo_err": 66.6,
  "time_losses": 0,
  "accepted": true
}
```

## Decision

Accepted (v010) — as infrastructure, NOT as a proven strength gain.

## Reason

Strength-neutral at bullet (-8.7 ±66.6 is indistinguishable from zero), zero flags,
all correctness gates green. Kept on the same basis as quiescence/check-extension/TT:
it is a correct, standard search technique with no downside whose benefit appears as
depth grows. This is explicitly **not** a measured Elo improvement at this TC.

## Notes

Confirms the recurring ceiling once more: at the ~depth-3-4 reachable in a 200 ms
bullet budget, ordering/caching changes cannot manufacture a new ply, so they read as
noise. The draw rate rising to 62.5% suggests slightly more solid play. Honest
caveat: with no node-count instrumentation, the cutoff improvement is asserted from
theory, not measured.

## Next experiment idea

Stop chasing search micro-optimizations at bullet. Two productive directions:
1. Node-count instrumentation, so ordering/TT changes can be measured directly
   instead of inferred from noisy bullet Elo.
2. A faster move generator (the current make-on-copy path is the real depth limiter);
   more nodes/sec converts directly into depth and measurable Elo.
