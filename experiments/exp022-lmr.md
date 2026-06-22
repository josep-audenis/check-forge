# Experiment exp022 — Late move reductions (LMR)

## Hypothesis

Continue search work (roadmap step 4). Late, quiet moves rarely beat the best move
already found, so search them shallower first and only re-search at full depth if they
surprise us. This buys effective depth — the proven lever — and compounds with null-move
pruning (v014) and -O3 (v011).

## Change

`engine/src/search.cpp`, `negamax` move loop: track `move_count`. For a move that is
`depth >= 3`, `move_count >= 4`, the node is not in check, and the move is not a
capture/promotion — search at `depth - 2` with a null window `(-alpha-1, -alpha)`; if that
beats alpha, re-search at full `depth - 1` and full window. First moves,
captures/promotions, and in-check nodes are always searched in full. Hoisted
`node_in_check` (shared with null-move pruning).

## Files changed

- `engine/src/search.cpp`

## Expected effect

Large node reduction at fixed depth → much greater depth in timed games → Elo.

## Risks

LMR can under-search a good quiet move; the null-window re-search is the safety net.
Gated by tactics (8/8) and perft (search-only, unaffected).

## Tests run

- Unit (ctest): pass. Perft: exact. Tactical suite: 8/8.
- Speed: fixed depth-8 on a midgame FEN — **9.1s vs 51.8s for v014 → 5.7× faster**, same
  score (cp 2; a different equal-valued move chosen, expected with eval ties).
- Verification (400 games over two detached batches, varied openings, 8+0.08),
  LMR vs v014: **117-62-221, +48.1 Elo ±17.5 (1σ), LOS ~99.7%, 0 illegal.**
  (Batch A: 55-32-113, +40.1; combined +48.1 — strongly, consistently positive.)

## Results

```json
{
  "speed_depth8": {"lmr_s": 9.1, "v014_s": 51.8, "speedup": 5.7},
  "vs_v014": {"w": 117, "l": 62, "d": 221, "games": 400, "elo_diff": 48.1, "elo_err_1sigma": 17.5, "illegal": 0}
}
```

## Decision

**Accepted (strength).** New head `versions/v015-lmr`.

## Reason

+48.1 Elo over 400 games at LOS ~99.7% — conclusive, the strongest gain since the -O3
build. Backed by a deterministic 5.7× fixed-depth speedup, correctness preserved (perft
exact, tactics 8/8, 0 illegal). Compounds with NMP and all future depth work.

## Notes

- The 5.7× depth-8 speedup is much larger than NMP's 1.76× because reductions apply to the
  majority (late, quiet) of moves at every interior node, shrinking the tree super-linearly
  with depth.
- Both batches ran to completion via `--detach` (no harness reaping).

## Next experiment idea

- **Principal variation search (PVS)** — null-window non-PV moves at full depth; pairs
  naturally with LMR.
- Or **make-unmake** to drop the per-move Board copy (more nps → depth).
- Or a longer-TC confirmation, since these depth-sensitive changes are understated at
  bullet. Re-measure on the internal ladder vs v015.
