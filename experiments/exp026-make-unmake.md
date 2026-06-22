# Experiment exp026 — Make/unmake move (in-place search)

## Hypothesis

exp025 concluded PVS failed because per-node cost is dominated by make-on-copy (a full
Board copy per move). Replacing it with in-place make/unmake should cut that cost → more
nps → depth → Elo, and unlock PVS.

## Change

- `movegen.h/.cpp`: added `Undo`, `make_move_inplace(Board&, Move)`, and
  `unmake_move(Board&, Move, Undo)`. Refactored `generate_legal_moves` to one mutable
  board copy + make/unmake per pseudo-move (was a copy per move), and `perft` to
  make/unmake.
- `search.cpp`: `negamax`, `quiescence`, `search_root` now operate on a mutable `Board&`
  with make/unmake around each recursive call; null-move flips side/ep in place and
  restores. `make_move` (copy) kept for external callers.

## Files changed

- `engine/include/checkforge/movegen.h`, `engine/src/movegen.cpp`, `engine/src/search.cpp`

## Tests run

- Unit: pass. **Perft: exact at all depths** (make/unmake correctness — millions of
  make/undo cycles). Tactics: 8/8.
- **Search parity**: identical bestmove + score to v016 across 4 positions at depth 8
  (same algorithm, no copies) — confirms behaviour unchanged.
- Speed: **perft6 206.2s vs 207.6s for v016 — identical**; depth-9 search likewise within
  noise. (Both ~3× slower than earlier sessions = machine thermal throttling after hours
  of matches, affecting both equally.)
- Verification (200 games, 8+0.08) vs v016: **51-46-103, +8.7 Elo ±24.6, 0 illegal.**

## Results

```json
{
  "perft6": {"new_s": 206.2, "v016_s": 207.6},
  "vs_v016": {"w": 51, "l": 46, "d": 103, "games": 200, "elo_diff": 8.7, "elo_err": 24.6, "illegal": 0}
}
```

## Decision

**Accepted as INFRASTRUCTURE** (no Elo claimed). New head `versions/v017-make-unmake`.

## Reason — and a corrected hypothesis

Make/unmake is **performance-neutral** here, which **refutes exp025's hypothesis**: the
~80-byte Board copy is *not* the bottleneck — the compiler turns it into a cheap memcpy,
about the same cost as make/unmake + an `Undo`. The real per-node costs are move
generation, the **full-board FNV hash computed at every node**, and the evaluation scan.

Kept as infrastructure because it is correct, zero-downside, the standard search
architecture, and — crucially — the enabler for the actual win: **incremental Zobrist
hashing** (update the key in make/unmake instead of rescanning 64 squares per node) and
incremental evaluation. Those need make/unmake to exist.

## Notes

- Two structural hypotheses about node cost have now been corrected by measurement
  (PVS-needs-ordering → PVS-needs-cheap-nodes → copy-isn't-the-cost). The data now points
  at hashing/eval per node, not move-making.

## Next experiment idea

- **Incremental Zobrist hashing**: replace the per-node full-board FNV with a Zobrist key
  updated incrementally in make/unmake. Removes a 64-iteration loop from every node →
  real nps → depth. Then retry PVS.
- Or cheaper/incremental evaluation.
