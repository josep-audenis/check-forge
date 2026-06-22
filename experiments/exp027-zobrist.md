# Experiment exp027 — Incremental Zobrist hashing

## Hypothesis

The TT key was a full-board FNV hash recomputed at every node (a 64-byte loop). With
make/unmake (v017) the key can be maintained incrementally — a few XORs per move instead
of rescanning the board — which should raise nps → depth → Elo, and was the stated payoff
of make/unmake.

## Change

- `board.h`: `Board` gains `std::uint64_t zobrist`.
- `movegen.h/.cpp`: Zobrist tables (12×64 pieces, side, 16 castling masks, 8 e.p. files,
  splitmix64-seeded), `compute_zobrist` (from scratch, used to seed), incremental XOR
  updates in `make_move_inplace`, and `Undo.zobrist` restored in `unmake_move`.
  `make_move` (copy) and `Board::from_fen` set a valid key.
- `search.cpp`: TT key is now `board.zobrist` (seeded with `compute_zobrist` at the search
  root); null-move recomputes it (rare). The old per-node FNV `hash_board` was removed.

## Files changed

- `engine/include/checkforge/board.h`, `engine/include/checkforge/movegen.h`,
  `engine/src/board.cpp`, `engine/src/movegen.cpp`, `engine/src/search.cpp`

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8.
- **Incremental-hash correctness**: a temporary self-check (`board.zobrist ==
  compute_zobrist(board)` after every make) ran clean through perft on startpos, kiwipete
  (castling), an ep position, and a promotions+ep position — millions of makes, zero
  mismatch. (Self-check then removed.)
- Speed: fixed depth-9 — 18.99s vs 18.97s for v017 → identical; same bestmove + score.
- Verification (200 games, 8+0.08) vs v017: **50-51-99, −1.7 Elo ±24.6, 0 illegal.**

## Results

```json
{
  "depth9_s": {"zobrist": 18.99, "v017": 18.97},
  "vs_v017": {"w": 50, "l": 51, "d": 99, "games": 200, "elo_diff": -1.7, "elo_err": 24.6, "illegal": 0}
}
```

## Decision

**Accepted as INFRASTRUCTURE** (no Elo claimed). New head `versions/v018-zobrist`.

## Reason — second confirmation that per-node cost is elsewhere

Performance-neutral. Removing the per-node 64-byte FNV loop changed nothing measurable,
just as make/unmake (exp026) did. The per-node FNV was already cheap relative to the real
hot costs: **move generation, `is_square_attacked` ray scans (run for legality on every
pseudo-move), and the evaluation board scan.** Two experiments now agree the node-cost
bottleneck is movegen/attack-detection/eval, not move-making or hashing.

Kept as infrastructure because it is correct (verified by the perft self-check), the
standard O(1) hashing design, zero-downside, and strictly less per-node work — it will
matter if the dominant costs are later reduced.

## Notes

- To actually raise nps now would require attacking the real hot loops: bitboard move
  generation / attack detection (a large rewrite), or a cheaper eval. Otherwise gains
  should keep coming from tree-size reductions (ordering/pruning) and from real eval,
  which is where every measured win has come from (LMR +48, killers+history +110).

## Next experiment idea

- **Aspiration windows** around the previous iteration's score (cheap, narrows the root
  window, small depth win) — a tree-size lever, not a node-cost one.
- Or **mobility evaluation** (untried eval term that re-ranks moves).
- A bitboard movegen rewrite is the only big nps lever left, but it is a multi-experiment
  structural project.
