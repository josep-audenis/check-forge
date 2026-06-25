# Experiment exp033 — Bitboard king safety (attacker count) — REJECTED

## Hypothesis

After mobility (+96, exp032) showed eval terms pay at v021's depth, add a king-safety
term: count enemy pieces attacking the king ring ("attack units"), weighted by piece type,
and penalise. Should be another cheap bitboard eval win.

## Change (reverted)

`engine/src/eval.cpp`: `king_danger` (knights +2 / bishops +2 / rooks +3 / queens +5 per
piece whose attack set hits the king zone = `g_king_attacks[k] | k`), `evaluate_king_safety_bb`
(white-perspective, scale 5 cp/unit), folded into `evaluate_static`.

## Files changed

- `engine/src/eval.cpp` (added, then reverted)

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8.
- Verification (200 games, 8+0.08) vs v021: **32-66-102, −59.6 Elo ±24.9, 0 illegal.**

## Results

```json
{"vs_v021": {"w": 32, "l": 66, "d": 102, "games": 200, "elo_diff": -59.6, "elo_err": 24.9, "illegal": 0}}
```

## Decision

**Rejected.** Large regression (−60 Elo). Reverted; head stays `versions/v021-bb-mobility`
(confirmed identical bestmove + score).

## Reason

Two compounding problems:
1. **Cost:** the term runs bishop/rook/queen attack ray-loops at every eval leaf — on top
   of mobility, which already does the same. Eval became heavy enough to lose meaningful
   depth (the slider attacks are still O(ray), not magic).
2. **Quality:** a flat linear attacker-count at scale 5 is crude — it penalises normal
   middlegame king exposure too bluntly, distorting move choice.

Cost + crude signal → −60. This is the clear signal that **magic bitboards (O(1) slider
attacks) must come before stacking more per-leaf eval terms** — mobility already spent the
per-leaf budget; king safety on ray-loop sliders overspends it.

## Notes

- Not a verdict on king safety as a concept — it's a verdict on doing it with O(ray)
  sliders on top of mobility. Re-try after magic bitboards, with a tuned non-linear
  attack-weight table and a lower scale.

## Next experiment idea

- **Magic bitboards** (roadmap): O(1) bishop/rook attacks via magic multiply+shift tables.
  Makes mobility cheaper (recovers depth) and makes king safety / further eval affordable.
  Perft-gate hard. This is the enabling step for the next eval wins.
- Then retry king safety (tuned) and PVS.
