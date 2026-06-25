# Experiment exp030 — Scaled late move reductions — REJECTED

## Hypothesis

LMR (v015) reduced late quiet moves by a flat 1 ply. With strong killer/history ordering
(v016), reducing *deeper* for moves later in the list and at greater depth should prune
more safely → more depth → Elo. (Roadmap step 5, fine-tuning.)

## Change (reverted)

`engine/src/search.cpp`, LMR reduction made variable: `r = 1`, `+1` if `move_count >= 6`,
`+1` if `depth >= 6 && move_count >= 10` (clamped to `depth-1`), instead of the flat
`depth-2`.

## Files changed

- `engine/src/search.cpp` (added, then reverted)

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8.
- Speed: searches noticeably deeper per unit time (fixed depth-10 ~22s).
- Verification (600 games over three detached batches, varied openings, 8+0.08) vs v019:
  **161-143-296, +10.4 Elo ±14.2, LOS ~77%, 0 illegal.**
  Per batch: A +41.9, B +0.0, C ≈ −10 — large disagreement.

## Results

```json
{"vs_v019": {"w": 161, "l": 143, "d": 296, "games": 600, "elo_diff": 10.4, "elo_err": 14.2, "los": 77}}
```

## Decision

**Rejected.** Over 600 games the gain is +10.4 ±14.2 — below the +15 bar and not
significant (LOS ~77%). Reverted; head stays `versions/v019-aspiration`.

## Reason

The first 200-game batch flashed +41.9, but batches B and C regressed to ~0 and ~−10; the
600-game estimate is ~+10 within noise. The deeper reductions trade a little extra depth
for a little extra tactical/positional miss, netting roughly even. Not worth keeping.

## Notes — process lesson

This is a textbook case for **large samples**: batch A (+42, LOS ~95%) alone would have
been a false accept. Three batches revealed the true ~+10. Single 200-game matches near
the +15 threshold are not trustworthy for fine-tuning deltas — use 400–600 games (or SPRT)
when the first result is in the noisy +15..+40 band.

## Next experiment idea

- **Tune the LMR trigger instead of the reduction** (e.g. start reducing at move_count ≥ 3,
  keeping a flat 1-ply reduction) — a different, possibly safer knob.
- **Tune cheap eval weights** (pawn-structure penalties, bishop pair) against the ladder.
- **Bitboards** (roadmap step 2) remain the big structural lever that unlocks PVS, mobility,
  and more depth — the route well past 2000.
