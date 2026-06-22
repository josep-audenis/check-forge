# Experiment exp025 — Principal variation search, retry on v016 ordering — REJECTED

## Hypothesis

exp023 rejected PVS (−44 Elo) blaming weak move ordering. Now that v016 has killer +
history ordering (the first move is usually best), scout re-searches should be rare, so
PVS should finally pay off.

## Change (reverted)

`engine/src/search.cpp`, `negamax` loop: first move full window; every later move a
null-window scout (with LMR reduction for late quiet moves), re-search at full
depth/window when it beats alpha. Same change as exp023, on top of v016.

## Files changed

- `engine/src/search.cpp` (added, then reverted)

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8. (PVS is exact — same scores.)
- Speed: fixed depth-9 on a midgame FEN — 23.8s vs **21.8s for v016** → ~9% *slower*.
- Verification (200 games, varied openings, 8+0.08), vs v016:
  **34-59-107, −43.7 Elo ±24.8, 0 illegal.**

## Results

```json
{"vs_v016": {"w": 34, "l": 59, "d": 107, "games": 200, "elo_diff": -43.7, "elo_err": 24.8, "illegal": 0}}
```

## Decision

**Rejected** (again). −44 Elo, identical to exp023. Reverted; head stays
`versions/v016-killers-history` (confirmed: identical bestmove + score).

## Reason — the hypothesis was wrong about the cause

Better ordering did **not** rescue PVS: still −44. The real reason PVS loses here is node
cost, not ordering. This engine's per-node work is dominated by **make-on-copy (a full
Board copy per move) + a full-board FNV hash + vector movegen** — not by the alpha-beta
window. So a null-window scout is barely cheaper than a full-window search (same make/
hash/movegen), while every scout that beats alpha triggers a re-search that pays the full
node cost again. Net: ~9% more work at fixed depth → less depth in timed games → −44.

PVS only pays off when narrowing the window meaningfully cheapens a node, i.e. when nodes
are cheap. **Prerequisite: make-unmake (cheap nodes), not move ordering.**

## Notes

- Two rejections of the same idea for two different stated reasons — the second corrected
  the first. The corrected lesson (node cost, not ordering) points squarely at make-unmake
  as the next structural lever.

## Next experiment idea

- **make-unmake**: replace `make_move` (copies the whole Board) with in-place make/undo
  in the search recursion. Big nps win on its own (the per-move copy is the dominant node
  cost), and it finally makes PVS / further pruning worthwhile. Gate hard with perft.
- Cheaper incremental Zobrist hashing (instead of full-board FNV per node) is a related
  node-cost win.
