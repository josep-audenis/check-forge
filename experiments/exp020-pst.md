# Experiment exp020 — PeSTO midgame piece-square tables — REJECTED

## Hypothesis

Replace the ad-hoc `positional_value` (centrality/advance heuristic) with proper PeSTO
midgame piece-square tables — a classic, cheap (table-lookup), well-tuned positional
term that should change move choice and gain Elo. Roadmap step 3 (real eval).

## Change (reverted)

`engine/src/eval.cpp`: `positional_value` rewritten to index per-piece PeSTO midgame
tables (White: `table[s]`; Black: `-table[s ^ 56]`, vertical mirror). Added a king PST
(the crude version had none). Removed `central_bonus`.

## Files changed

- `engine/src/eval.cpp` (added, then reverted after the match)

## Tests run

- Unit (ctest): pass. Tactical: 8/8. Perft: exact.
- Orientation verified via `--bestmove --depth`: WN-e4 (373) ≈ mirror BN-e5 (376),
  startpos = 0, WN-e4 (373) > WN-a1 (323). Tables correct, not buggy.
- Verification (201 games over two batches, varied openings, 8+0.08), PST vs v013:
  **45-44-112, +1.7 Elo (~±24), 0 illegal/flags.**

## Results

```json
{"vs_v013": {"w": 45, "l": 44, "d": 112, "games": 201, "elo_diff": 1.7, "elo_err": 24.5, "illegal": 0}}
```

## Decision

**Rejected.** Strength-neutral (+1.7 ±24 is indistinguishable from zero). Reverted; head
stays `versions/v013-pawn-structure`. Confirmed revert reproduces v013 (identical
bestmove + score).

## Reason

No measurable gain. Generic PeSTO midgame tables do not beat the engine's existing crude
centrality/advance eval (hand-iterated across exp002–exp008) at the depth (~5-6) this
engine reaches: the PST mostly re-encodes centrality the crude eval already captures, so
move ranking barely changes. This is the second neutral eval term (after exp019 king
safety) — confirming that an eval term only helps if it adds information that re-ranks
moves. Pawn structure (exp018, +51) did; PST and shield did not.

## Notes

- Both verification batches were killed mid-run by the harness reaping the background
  process tree (~78 and ~123 games). Aggregated to a full 201-game sample via the PGN
  (ground truth) with `research/score_pgn.py`. Future long matches should use the new
  `--detach` flag (breaks away from the harness job). See `docs/wiki/log.md`.
- A *tapered* PST (midgame↔endgame interpolation by game phase) or *tuning* the existing
  weights against the engine could still help; a flat midgame-only table swap does not.

## Next experiment idea

- **Mobility** (per-side move counts → bonus), the remaining untried classic eval term —
  but measure the nodes/sec cost since it runs per leaf.
- Or pivot to roadmap step 4 (search): **null-move pruning** or **late move reductions**,
  which buy depth (the proven lever) and compound with the -O3 speed.
- Or **make-unmake** to drop the per-move Board copy (more nodes/sec → depth).
