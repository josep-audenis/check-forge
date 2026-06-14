# Experiment exp019 — King-safety (pawn shield) — REJECTED

## Hypothesis

The eval had no king-safety term. A pawn-shield penalty (missing pawns in front of the
king), suppressed when the enemy has no queen so it doesn't punish correct endgame king
activity, should improve middlegame defence and gain Elo. Roadmap step 3 (real eval).

## Change (reverted)

`engine/src/eval.cpp`: added `evaluate_king_safety()` folded into `evaluate_static`:
- −14 per file (king ± adjacent) with no friendly pawn directly in front of the king.
- −7 per file with no friendly pawn two ranks in front.
- Applied only when the enemy still has a queen.

## Files changed

- `engine/src/eval.cpp` (added, then reverted after the match)

## Tests run

- Unit (ctest): pass. Tactical suite: 8/8. Perft: exact.
- Verification (200 games, varied openings, 8+0.08), candidate vs v013:
  **47-44-112, +5.1 Elo (~±24), 0 illegal/flags.**

## Results

```json
{"vs_v013": {"w": 47, "l": 44, "d": 112, "games": 203, "elo_diff": 5.1, "elo_err": 24.4, "illegal": 0}}
```

## Decision

**Rejected.** Strength-neutral (+5 Elo is well within noise). Reverted; head stays
`versions/v013-pawn-structure`.

## Reason

No measurable gain. A 54% draw rate and a +5 ±24 Elo result is indistinguishable from
zero, so there is no justification to keep the extra eval cost. Naive pawn-shield
king-safety commonly reads as neutral until paired with an attack-weight / king-zone
attacker-count model; the simple shield count alone does not change move choice at the
depth (~6) this engine reaches.

## Notes

- Infra incident: the cutechess run finished all 200 games (PGN complete) but the Python
  wrapper died before writing the result JSON (background task orphaned). The result was
  reconstructed from the PGN, which is ground truth. **Follow-up: make
  `run_cutechess.py` derive W-L-D from its own PGN and write the JSON robustly so a lost
  stdout / killed wrapper can't discard a completed match.**
- Consistent with the bullet-ceiling lesson: additive eval terms only help if they
  actually change the chosen move. Pawn structure (exp018) did (+51); a crude shield did
  not.

## Next experiment idea

- **Mobility** (count of legal/pseudo-legal moves, small per-move bonus) — a strong,
  distinct eval term, but watch the nodes/sec cost since it runs per leaf.
- Or **tuned piece-square tables** replacing the ad-hoc `positional_value`.
- Or revisit king safety with an attacker-count / king-zone model rather than a flat
  shield penalty.
