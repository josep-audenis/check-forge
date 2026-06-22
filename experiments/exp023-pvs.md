# Experiment exp023 — Principal variation search (PVS) — REJECTED

## Hypothesis

On top of LMR (v015), scout every non-first move with a null window and only re-search at
full window when it lands inside (alpha, beta). PVS is exact and usually faster, so it
should buy a little depth → Elo.

## Change (reverted)

`engine/src/search.cpp`, `negamax` loop: first move full window; every later move a
null-window scout (`-alpha-1, -alpha`), with LMR reduction for late quiet moves; re-search
at full depth/window when the scout beats alpha (and, for unreduced moves, lands below
beta).

## Files changed

- `engine/src/search.cpp` (added, then reverted)

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8.
- **Correctness confirmed**: PVS produced identical fixed-depth scores to v015 across 5
  varied positions (depth 6) — PVS is exact, not buggy.
- Speed (fixed depth-8, one position): 8.4s vs 8.8s — only ~5% faster.
- Verification (200 games, varied openings, 8+0.08), PVS vs v015:
  **37-62-101, −43.7 Elo ±24.8, 0 illegal.**

## Results

```json
{"vs_v015": {"w": 37, "l": 62, "d": 101, "games": 200, "elo_diff": -43.7, "elo_err": 24.8, "illegal": 0}}
```

## Decision

**Rejected.** Clear regression (−44 Elo). Reverted; head stays `versions/v015-lmr`
(confirmed: identical bestmove + score to v015).

## Reason

PVS is correct (exact scores) but **loses in timed play** because this engine's move
ordering is weak (only MVV-LVA + the TT move — no killer or history heuristics). At
non-PV nodes the best move is often not searched first, so null-window scouts fail high
frequently and trigger full re-searches; their cost outweighs the savings, so PVS reaches
*less* depth in the same time. LMR already captured the null-window benefit for the late
quiet moves where it reliably pays.

## Notes

- Order matters: PVS pays off only once move ordering is good enough that the first move
  is usually best. **Prerequisite: killer-move and history-heuristic ordering.** Re-try
  PVS after that.

## Next experiment idea

- **Killer moves + history heuristic** (better quiet-move ordering) — improves LMR/NMP
  cutoffs directly and unlocks PVS later.
- Or **make-unmake** to drop the per-move Board copy (raw nps → depth).
