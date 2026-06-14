# Experiment exp017 — Movegen legality without per-move find_king

## Hypothesis

`generate_legal_moves` filtered each pseudo-move with `is_in_check(next, us)`, and
`is_in_check` calls `find_king`, a full 64-square scan, for every move. The friendly king
square only changes when the king itself moves, so it can be found once per call and
derived in O(1) per move. Removing the per-move scan should raise nodes/sec with
identical results.

## Change

`engine/src/movegen.cpp`, `generate_legal_moves`:
- `find_king` once before the loop; per move, post-move king square is `move.to` if the
  king moved else unchanged; check `is_square_attacked(next, king_sq, enemy)` directly.
- `reserve()` on the pseudo-move and legal-move vectors.

No change to move semantics — same definition of legality, same results.

## Files changed

- `engine/src/movegen.cpp`

## Expected effect

Faster move generation (fewer wasted board scans). Possibly a little Elo if it buys
depth; more likely strength-neutral at bullet (a fraction of a ply).

## Risks

Correctness of the derived king square (castling, en passant, king captures). Gated by
perft (must stay exact) and tactics.

## Tests run

- Unit (ctest): pass.
- Perft: exact at all cases (depths 1–5); perft(6) on a midgame FEN = 948,211,582 nodes,
  identical to v011.
- Tactical suite: 8/8.
- Speed: perft(6) **66.2s vs 88.8s for v011 → 1.34× faster**, identical nodes.
- Verification (200 games, varied openings, 8+0.08), exp017 vs v011:
  **46-46-108, +0.0 ±32.7 Elo, 0 flags/illegal.**

## Results

```json
{
  "speed": {"perft6_s": 66.2, "perft6_v011_s": 88.8, "speedup": 1.34},
  "internal_vs_v011": {"w": 46, "l": 46, "d": 108, "elo_diff": 0.0, "elo_err": 32.7},
  "absolute_elo": "unchanged ~1714 (strength-neutral)"
}
```

## Decision

**Accepted as INFRASTRUCTURE.** New head `versions/v012-king-cache`. No Elo gain claimed.

## Reason

1.34× faster move generation with perft exact and tactics 8/8 — a correct, zero-downside
speedup. Strength-neutral at bullet TC (34% nps is well under one extra ply at this
depth), consistent with the bullet-ceiling finding. Kept as infrastructure: the speed
will compound with future depth-buying work (make-unmake, pruning).

## Notes

- The remaining big movegen cost is the make-on-copy `make_move` (copies the whole Board
  per move) and the full-board FNV hash per search node. Those are the next targets.

## Next experiment idea

exp018: real evaluation (roadmap step 3) — king safety / pawn structure / mobility or
tuned PSTs — which gives a measurable Elo jump at the current depth, unlike search
micro-tweaks. Alternatively continue movegen: make-unmake to drop the per-move Board
copy. Either way, re-measure vs SF1700 with `run_anchor.py`.
