# Experiment exp008-bishop-pair

## Hypothesis

Static eval currently values both bishops identically to any minor piece. Adding a
small bishop-pair bonus should nudge the engine toward keeping both bishops, a
well-established positional heuristic, without harming tactics or correctness.

## Change

`engine/src/eval.cpp`: in `evaluate_static`, count bishops per side during the
positional sweep and add `kBishopPairBonus = 30` for a side holding two or more
bishops (subtracted for Black). Symmetric, so quiescence stand-pat stays balanced.

## Files changed

- `engine/src/eval.cpp`

## Expected effect

Engine retains bishop pairs more often. No tactical regression; correctness gates
unchanged.

## Risks

A bishop-pair term that is too large could distort material trades. Kept small (30,
under a third of a minor piece) to stay safe.

## Tests run

- Unit tests: 1/1 passed
- Perft: passed
- Tactical suite: 8/8
- Speed: passed
- Internal match vs v006: passed
- Cutechess vs v006: 20 games at `2+0.1`

## Results

```json
{
  "benchmark": "results/exp008-bishop-pair.json",
  "cutechess": "results/exp008-bishop-pair-cutechess.json",
  "tactics": "8/8",
  "score_vs_v006": "0 - 0 - 20 [0.500]",
  "draw_ratio": "100.0%",
  "elo_diff": 0.0,
  "accepted": true
}
```

## Decision

Accepted

## Reason

Correctness gates pass and cutechess shows no regression versus v006. Bishop-pair is
a sound, isolated eval term. No Elo gain — blocked by the same 3-fold repetition
draw documented in exp007, not by the eval term itself.

## Notes

This is the third consecutive accept-as-infrastructure result. The pattern is now
unambiguous: with two deterministic clones drawing the same opening by 3-fold
repetition every game, *no* eval or ordering change can move the cutechess Elo. The
loop is producing correct, well-tested versions but the strength metric is saturated
at 0.5 until the repetition problem is addressed.

## Next experiment idea

Stop adding eval/search polish against a flat metric. Next high-value work is
infrastructure to unblock measurement:
1. Search-node instrumentation (quantify ordering/pruning changes).
2. Repetition handling so version-vs-version games can be decisive — or change the
   match protocol to use varied opening books so identical engines diverge and Elo
   becomes observable. exp003 warns that naive anti-repetition hacks regress badly.
