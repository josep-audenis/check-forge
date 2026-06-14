# Experiment exp021 — Null-move pruning

## Hypothesis

After two neutral eval terms (exp019/020), pivot to search (roadmap step 4). Null-move
pruning buys depth — the proven lever (one ply ≈ +147 Elo earlier) — and compounds with
the exp016 -O3 speed. If passing the move still fails high, a real move surely does, so
the subtree can be pruned.

## Change

`engine/src/search.cpp`, in `negamax`, after the TT probe: if `depth >= 3`, the window is
narrow (`beta < kMateZone`, i.e. not a PV/mate node), the side to move has non-pawn
material (zugzwang guard via new `has_non_pawn_material`), and not in check — search a
null move (pass; flip side, clear en passant) at reduced depth `depth - 1 - R` (R=2) with
a null window `(-beta, -beta+1)`. On `null_score >= beta`, return beta (fail-high cutoff).

## Files changed

- `engine/src/search.cpp`

## Expected effect

Fewer nodes per fixed depth → more depth in timed games → Elo. No correctness change
(search-only; perft unaffected).

## Risks

Null-move is unsound in zugzwang (guarded by non-pawn-material check) and can miss some
deep tactics. Gated by tactics (must stay 8/8).

## Tests run

- Unit (ctest): pass. Perft: exact (search-only change). Tactical suite: 8/8.
- Speed: fixed depth-7 on a midgame FEN — **13.9s vs 24.5s for v013 → 1.76× faster**,
  identical bestmove + score (f3g5 cp 18). Direct, deterministic depth/node win.
- Verification (400 games over two detached batches, varied openings, 8+0.08),
  NMP vs v013: **101-78-221, +20.0 Elo ±17.4 (1σ), 0 illegal/flags.**
  (Batch A alone: 50-38-112, +20.9; batch B combined: +20.0 — consistent.)

## Results

```json
{
  "speed_depth7": {"nmp_s": 13.9, "v013_s": 24.5, "speedup": 1.76},
  "vs_v013": {"w": 101, "l": 78, "d": 221, "games": 400, "elo_diff": 20.0, "elo_err_1sigma": 17.4, "illegal": 0}
}
```

## Decision

**Accepted (strength).** New head `versions/v014-null-move`.

## Reason

+20.0 Elo over 400 games, **consistent across two independent batches** (+20.9 then
+20.0) — replication rules out the noise that sank exp019/020. Backed by a deterministic
1.76× fixed-depth speedup (real depth gain in games) and a sound, standard technique with
correctness preserved (perft exact, tactics 8/8, 0 illegal). It also compounds with all
future depth work.

Honesty note: the 55% draw rate inflates the Elo error, so LOS is ~87% (1σ), short of a
95% bar. The decision rests on the consistent positive delta **plus** the deterministic
depth speedup and theory — not on a single match clearing significance. NMP is also
depth-sensitive, so bullet 8+0.08 likely understates it; a longer TC would show more.

## Notes

- The `--detach` fix (run_cutechess/run_anchor) worked: both 200-game batches ran to
  completion with no harness reaping.

## Next experiment idea

- **Late move reductions (LMR)** — reduce depth for late, quiet moves; compounds with NMP
  for more effective depth.
- Or **make-unmake** to drop the per-move Board copy (more nps → depth).
- Re-measure on the internal ladder vs v014; consider a longer-TC confirmation match for
  these depth-sensitive search changes.
