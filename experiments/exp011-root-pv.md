# Experiment exp011-root-pv

## Hypothesis

Searching the previous iteration's best move first at the root (PV-first ordering)
should sharpen alpha-beta cutoffs, let iterative deepening reach one more ply inside
the same time budget, and thus gain Elo at fixed TC.

## Change

`engine/src/search.cpp`: `search_root` takes an optional `pv_first` move and rotates
it to the front after MVV-LVA ordering. `search_bestmove_timed` passes the last
completed depth's best move into the next iteration. Fixed-depth search passes
`nullptr`, so its behavior is unchanged.

## Files changed

- `engine/src/search.cpp` (reverted after rejection)

## Expected effect

Faster cutoffs -> occasionally one extra ply -> small positive Elo vs v008.

## Tests run

- Unit tests: 1/1 passed
- Tactical suite: 8/8 (fixed-depth path unchanged)
- Benchmark vs v008: accepted
- Cutechess vs v008: 40 games, tc=4+0.1, varied openings

## Results

```json
{
  "cutechess": "results/exp011-root-pv-cutechess.json",
  "score_vs_v008": "10 - 15 - 15",
  "elo_diff": -43.7,
  "elo_err": 87.1,
  "los": "15.9%",
  "time_losses": 0,
  "accepted": false
}
```

## Decision

Rejected

## Reason

No evidence of gain: point estimate is negative (-43.7 Elo) and not significant
(±87, LOS 15.9%). PV-first ordering is a pure speed optimization, but at the shallow
depths reachable in a ~200 ms bullet budget the cutoff savings rarely buy a full
extra ply, so move choice is essentially unchanged and the result is noise. Per the
acceptance rules, a change is not kept without positive benchmark support. Reverted;
v008 remains head.

## Notes

Correct behavior of the loop: not every plausible idea survives measurement. The
speedup would likely matter at longer TC / deeper search, where an extra ply is
actually unlocked — worth revisiting once base depth is higher.

## Next experiment idea

Use the proven lever directly: spend a larger fraction of the clock per move so the
search reaches greater depth (depth itself was worth +147 Elo at 30+0.3). Tune the
time budget and measure vs v008.
