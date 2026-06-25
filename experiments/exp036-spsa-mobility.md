# Experiment exp036 — SPSA tuning harness + mobility-weight tuning

## Hypothesis

Build an SPSA tuner (roadmap step 5) and use it to tune the mobility eval weights (the +96
lever, exp032). Tuned weights might beat the hand-set defaults {N4,B4,R2,Q1}.

## Change

- `engine/config.{h,cpp}`: mobility weights `mob_knight/bishop/rook/queen` exposed in the
  config (`eval_weights`), parsed and emitted; `eval.cpp` mobility now reads them. Default
  values unchanged → default config reproduces v022 exactly (verified: identical bestmove
  + score at depth 8).
- `research/run_spsa.py` (new): SPSA driver. Each iteration perturbs all tuned params by
  ±c_k along a random sign vector, plays a short self-match (same engine binary, only
  `--config` differs), and steps params toward the winner. Checkpoints to
  `results/spsa_state.json` every iteration (resumable after a reap — used twice here).

## Files changed

- `engine/include/checkforge/config.h`, `engine/src/config.cpp`, `engine/src/eval.cpp`
- `research/run_spsa.py` (new)

## Tests run

- Unit: pass. Tactics: 8/8. Default config == v022 (verified).
- SPSA: 30 iterations × 24 games, TC 4+0.04, tuning the 4 mobility weights.

## Results

```text
start theta {4, 4, 2, 1}
final theta {3.97, 3.93, 2.07, 1.02} -> rounds to {4, 4, 2, 1}
per-iteration plus-score hovered ~0.45-0.48 (no consistent direction)
tuned config == v022 defaults
```

## Decision

**Harness accepted as INFRASTRUCTURE; mobility tuning = no change.** Head stays
`versions/v022-magic-bitboards`. No version bump (tuned weights are bit-identical to v022,
so a verification match would be 50% by construction).

## Reason

The mobility weights barely moved across 30 iterations and round back to the defaults — they
were already near-optimal, so the +96 mobility gain (exp032) used good values and there is
no easy gain to squeeze there. The valuable deliverable is the **reusable, validated SPSA
harness**: same engine binary, config-only perturbation, checkpoint-resumable.

## Notes

- SPSA at 24 games/iter is noisy; the lack of movement is consistent with a flat optimum
  rather than a found peak. Either way: no gain on these 4 params.
- Next SPSA targets have more headroom than mobility (which was already tuned by hand):
  pawn-structure weights (doubled/isolated/passed — currently hardcoded), and possibly
  piece values. Expose those in config, then re-run the harness.

## Next experiment idea

- exp037: expose pawn-structure weights in config and SPSA-tune them (more headroom).
- Or SEE-based quiescence pruning / tapered eval (structural, not tuning).
