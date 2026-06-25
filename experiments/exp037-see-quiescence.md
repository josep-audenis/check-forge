# Experiment exp037 — SEE-based quiescence pruning — REJECTED

## Hypothesis

Add static exchange evaluation (SEE) and skip losing captures (SEE < 0) in quiescence.
Should shrink the q-search (faster → deeper) and improve quality.

## Change

- `movegen.{h,cpp}`: `see_capture()` — bitboard SEE (recompute attackers per swap for
  x-rays; least-valuable-attacker order; config piece values). **Kept** (correct, reusable).
- `search.cpp`: quiescence skipped captures with SEE < 0 — **reverted** after the match.

## Files changed

- `engine/include/checkforge/movegen.h`, `engine/src/movegen.cpp` (see_capture, kept)
- `engine/src/search.cpp` (quiescence pruning, reverted)

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8 (with pruning on).
- Speed: fixed depth-10 **30.3s vs 47.1s for v022 → ~36% faster** q-search.
- Verification (200 games, 8+0.08) vs v022: **37-42-121, −8.7 Elo ±24.6, 0 illegal.**

## Results

```json
{"vs_v022": {"w": 37, "l": 42, "d": 121, "games": 200, "elo_diff": -8.7, "elo_err": 24.6, "illegal": 0}}
```

## Decision

**Rejected.** Strength-neutral/slightly negative despite a 36% faster q-search. Pruning
reverted; head stays `versions/v022-magic-bitboards` (confirmed identical to v022). The
`see_capture` function is retained for possible future move-ordering use.

## Reason

The depth gained from a smaller q-search is offset by occasionally pruning a capture that
is part of a sound tactic (SEE is static — it misses follow-ups, pins, and check-based
resources), so the net is ~0/−. Q-search was not a strength bottleneck here. This mirrors
the per-node speedups (make-unmake, zobrist, bitboard movegen) that were neutral: faster
isn't stronger unless it buys decisions that matter.

## Notes

- A softer variant (prune only SEE below a margin, or use SEE just to *order* captures
  rather than prune) might be neutral-to-slightly-positive; not pursued now.
- `see_capture` is verified correct (perft/tactics unaffected, no illegal moves across the
  match) and available for move ordering experiments.

## Next experiment idea

- **SEE for capture ordering** (order good captures before bad, don't prune) — uses the
  retained `see_capture`, lower risk than pruning.
- **Tapered eval** (midgame↔endgame PST by phase) — a structural eval change with headroom.
- **SPSA on pawn-structure / piece values** — expose those and reuse the harness.
