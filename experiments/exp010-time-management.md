# Experiment exp010-time-management

## Hypothesis

The engine searches a fixed `default_depth` on every move and ignores the clock
(`uci.cpp` returned `default_depth` for any `go` without explicit `depth`). So a
deeper, stronger search flags on time (exp004; confirmed here: a depth-4 config lost
all 20 games on time at 4+0.1, yet won +147 Elo at 30+0.3). Iterative deepening
bounded by a per-move time budget should let the engine search as deep as time
allows, beating fixed-depth-3 v007 without ever losing on time.

## Change

- `engine/src/search.cpp`: introduced `SearchContext` (config + deadline + sticky
  abort + node counter) threaded through `negamax`/`quiescence`/`search_root`. Added
  `search_bestmove_timed()`: iterative deepening from depth 1 to a cap, keeping the
  best move from the last fully completed depth and discarding any aborted iteration.
  Time is read via `GetTickCount64` (the toolchain's `<chrono>` backend fails to
  compile here — pulls a missing `features.h`).
- `engine/include/checkforge/search.h`: declared `search_bestmove_timed`.
- `engine/src/uci.cpp`: `go` now parses `wtime/btime/winc/binc/movetime/depth`.
  Explicit `depth` keeps the old fixed-depth path (tests, tooling). `movetime` and
  clock (`wtime/btime`) use the timed search with budget
  `remaining/30 + 3*inc/4`, capped at 80% of remaining, floor 5 ms.

## Files changed

- `engine/src/search.cpp`
- `engine/include/checkforge/search.h`
- `engine/src/uci.cpp`

## Expected effect

No time losses; net-positive score vs v007; correctness unchanged (fixed-depth path
identical).

## Risks

A search that overshoots its budget would flag. The first build did exactly that
(see Notes) due to a non-sticky abort. Fixed and re-measured before accepting.

## Tests run

- Unit tests: 1/1 passed
- Perft: passed
- Tactical suite: 8/8 (fixed-depth path unchanged)
- `movetime` adherence: 200->214 ms, 1000->1017 ms, 3000->3022 ms (tight)
- Benchmark vs v007: accepted
- Cutechess vs v007: 30 games, tc=4+0.1, varied openings

## Results

```json
{
  "benchmark": "results/exp010-time-management.json",
  "cutechess": "results/exp010-time-management-cutechess.json",
  "score_vs_v007": "8 - 6 - 16",
  "elo_diff": 23.2,
  "elo_err": 86.6,
  "los": "70.4%",
  "time_losses": 0,
  "accepted": true
}
```

## Decision

Accepted (v008)

## Reason

Core architectural fix: the engine now respects the clock and never flagged across
30 games (vs the fixed-depth path that loses every game when depth is too slow).
Score vs v007 is net-positive (+23 Elo) though not significant at 30 games. Accepted
primarily as the infrastructure that removes the time-loss failure mode and unlocks
depth scaling, which is the project's main remaining strength lever.

## Notes

First build flagged all 30 games: `out_of_time` only reported the abort on its
1-in-2048 poll tick, so the signal never propagated and each iteration ran to full
completion (measured 3.8x budget overshoot). Made the abort sticky (return true once
aborted); overshoot dropped to a few ms. Lesson logged. The Elo edge is small at
4+0.1 because a ~200 ms budget only reaches ~depth 3-4; the advantage grows with TC
(depth-4 vs depth-3 was +147 Elo at 30+0.3).

## Next experiment idea

Tune the time budget to convert the measured headroom (zero flags) into deeper
search and a clearer Elo edge — e.g. spend `remaining/20` — measured vs v008.
