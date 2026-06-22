# Experiment exp024 — Killer moves + history heuristic

## Hypothesis

exp023 showed move ordering is the bottleneck (PVS lost because scouts failed high too
often). Add the two standard quiet-move ordering heuristics — killer moves (two per ply,
the quiet moves that last caused a beta cutoff) and a from→to history table credited on
quiet cutoffs — so good quiet moves are tried earlier. Better ordering → more/earlier
cutoffs → smaller tree → more depth, and it sharpens NMP/LMR too.

## Change

`engine/src/search.cpp`:
- `SearchContext` gains `killers[kMaxPly][2]` and `history[64][64]`.
- New `search_move_score` / `order_moves_search`: captures/promotions first (MVV-LVA),
  then killers, then quiet moves by history (tiers separated by large constants; history
  clamped). Used in `negamax` and at the root (the TT move is still promoted to front).
- On a quiet beta-cutoff, `record_quiet_cutoff` updates killers (shift) and
  `history[from][to] += depth*depth`.

## Files changed

- `engine/src/search.cpp`

## Expected effect

Large node reduction at fixed depth → much greater depth in games → big Elo.

## Risks

None to correctness (ordering only changes search order, not results). Gated by perft
(exact) and tactics (8/8).

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8.
- Speed: fixed depth-9 on a midgame FEN — **31s vs 3m43s for v015 → 7.2× faster**, same
  bestmove + score (b2b4 cp 6).
- Verification (200 games, varied openings, 8+0.08), vs v015:
  **76-15-109, +109.5 Elo ±25.8, LOS ~100%, 0 illegal.**

## Results

```json
{
  "speed_depth9": {"new_s": 31, "v015_s": 223, "speedup": 7.2},
  "vs_v015": {"w": 76, "l": 15, "d": 109, "games": 200, "elo_diff": 109.5, "elo_err": 25.8, "illegal": 0}
}
```

## Decision

**Accepted (strength).** New head `versions/v016-killers-history`.

## Reason

+109.5 Elo over 200 games at LOS ~100% — the biggest gain since the -O3 build, and the
largest search improvement. Backed by a deterministic 7.2× fixed-depth speedup, with
correctness preserved (perft exact, tactics 8/8, 0 illegal). Move ordering was the
limiting factor (exp023); fixing it pays off enormously and also makes NMP/LMR cutoffs
land sooner.

## Notes

- This unblocks PVS (exp023, rejected): with the first move now usually best, scout
  re-searches should be rare. PVS is the natural retry next.

## Next experiment idea

- **Retry PVS** on top of killers+history (should now pay off).
- Or **make-unmake** to drop the per-move Board copy (raw nps → depth).
- Re-measure on the internal ladder vs v016; consider a longer-TC confirmation for the
  accumulated depth-sensitive search stack.
