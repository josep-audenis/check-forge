# Experiment exp031 — Bitboard move generation + attack detection

## Hypothesis

Roadmap step 2 (the big nps lever). Replace the mailbox ray/char scans with bitboards:
maintain piece bitboards on the Board, and use precomputed leaper tables + occupancy-based
slider attacks for `is_square_attacked` and for knight/slider/king move generation. Faster
movegen → more depth → Elo, and (more importantly) the foundation that makes cheap
bitboard eval (mobility, king safety) and PVS finally viable.

## Change

- New `bitboard.{h,cpp}`: `Bitboard` type, precomputed `g_knight_attacks`,
  `g_king_attacks`, `g_pawn_attacks`; `bishop_attacks`/`rook_attacks`/`queen_attacks` via
  occupancy ray loops; popcount/lsb helpers; `bb_piece_index`.
- `Board` gains `bb[12]` piece bitboards. `rebuild_bitboards` (used by `from_fen` and the
  copy `make_move`); incremental updates in `make_move_inplace` / `unmake_move` (validated
  against the mailbox by perft).
- `is_square_attacked` rewritten to bitboards. `generate_pseudo_legal_moves` emits
  knight/bishop/rook/queen/king targets from attack bitboards (pawns + castling unchanged).
- `engine/CMakeLists.txt`: add `bitboard.cpp`.

## Files changed

- `engine/include/checkforge/bitboard.h` (new), `engine/src/bitboard.cpp` (new),
  `engine/include/checkforge/board.h`, `engine/include/checkforge/movegen.h`,
  `engine/src/board.cpp`, `engine/src/movegen.cpp`, `engine/CMakeLists.txt`

## Tests run

- Unit: pass. **Perft: exact at all cases** (the gate — wrong bb maintenance or wrong
  bitboard attacks would corrupt legality/perft). Tactics: 8/8.
- Speed: perft6 **65.1s vs 81.5s for v019 → ~20% faster** movegen.
- Verification (200 games, 8+0.08) vs v019: **50-49-101, +1.7 Elo ±24.6, 0 illegal.**

## Results

```json
{
  "perft6_s": {"bitboards": 65.1, "v019": 81.5},
  "vs_v019": {"w": 50, "l": 49, "d": 101, "games": 200, "elo_diff": 1.7, "elo_err": 24.6, "illegal": 0}
}
```

## Decision

**Accepted as INFRASTRUCTURE** (no Elo claimed). New head `versions/v020-bitboards`.

## Reason — and what the bitboard payoff actually is

Strength-neutral despite ~20% faster movegen. In a real search the dominant per-leaf cost
is the **evaluation board scan (unchanged)**, and maintaining both `squares[]` and `bb[]`
in make/unmake dilutes the movegen win — so faster movegen alone doesn't move match Elo
(same lesson as make/unmake and Zobrist).

Kept because it is correct (perft exact) and is the **enabler** for the real wins:
- **Cheap bitboard eval** — mobility (rejected in exp029 only because mailbox ray scans
  made it 1.66× slower) and king safety become near-free with `bb`/attack tables.
- Faster sliders (magic bitboards) and piece-bitboard iteration (skip the 64-square scan).
- A PVS retry once nodes are genuinely cheaper.

## Next experiment idea

- **Bitboard mobility eval** (re-do exp029 using `bb` + attack tables) — the term was good
  (+8.7 even while 1.66× slower); near-free now, it should clear +15.
- Then **bitboard king safety**, **magic sliders**, and a **PVS retry**.

## Notes

- The bb/mailbox dual representation is redundant; a later cleanup could drop `squares[]`
  in hot paths (eval especially) to remove the double bookkeeping.
