# Experiment exp029 — Mobility evaluation — REJECTED

## Hypothesis

Add a mobility term (pseudo-mobility of knights/bishops/rooks/queens, small per-square
bonus) — a classic eval feature that re-ranks moves, like pawn structure (+51). Should
gain Elo.

## Change (reverted)

`engine/src/eval.cpp`: `evaluate_mobility` (white-perspective) counting reachable squares
per minor/major piece (own pieces block; empty/enemy count), weights N=4/B=4/R=2/Q=1 per
square, folded into `evaluate_static`.

## Files changed

- `engine/src/eval.cpp` (added, then reverted)

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8.
- Speed: fixed depth-9 **128s vs 77s for v019 → 1.66× slower** (slider ray scans run at
  every eval leaf). Different move/score (eval changed, as intended).
- Verification (200 games, 8+0.08) vs v019: **52-47-101, +8.7 Elo ±24.6, 0 illegal.**

## Results

```json
{"vs_v019": {"w": 52, "l": 47, "d": 101, "games": 200, "elo_diff": 8.7, "elo_err": 24.6, "illegal": 0}}
```

## Decision

**Rejected.** Does not clear the +15 strength bar (+8.7 ±24.6 is within noise). Reverted;
head stays `versions/v019-aspiration` (confirmed identical bestmove + score).

## Reason

The eval term is genuinely helpful (the score stayed positive across the run, never
behind), but mobility requires a slider ray scan for every minor/major piece at **every
eval leaf**, which made the engine **1.66× slower** → it lost roughly half a ply of depth.
The eval gain and the depth loss almost exactly cancelled → net ≈ 0. Same structural
pattern as PVS (exp025): a sound technique that cannot pay until the underlying operation
(here, attack generation) is cheap. Mobility wants **bitboards**.

## Notes

- A cheaper variant (knights-only mobility — no ray scans — or mobility cached/incremental)
  might net positive, but full slider mobility on the mailbox board is too costly.
- Reinforces the standing finding: at this engine's nps, per-leaf scanning eval terms are
  on the edge of paying; tree-size levers (ordering/pruning) and *cheap* eval terms (pawn
  structure) are the reliable wins until bitboards land.

## Next experiment idea

- **Weight tuning** (roadmap step 5): tune existing cheap terms (pawn-structure penalties,
  bishop-pair, null-move R, LMR threshold/reduction) now that the structure is in place —
  cheap, no per-node cost.
- **Bitboards** (roadmap step 2): the big rewrite that makes mobility, PVS, and deeper
  search all pay — the route to push well past 2000.
