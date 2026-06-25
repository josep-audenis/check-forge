# Experiment exp035 — King safety retry (cheap, tuned) — REJECTED

## Hypothesis

exp033 king safety lost −60; I attributed it mainly to per-leaf slider cost. Magic
bitboards (v022) removed that cost, so a king-zone attacker-count term with a gentler
bounded non-linear danger table should now pay.

## Change (reverted)

`engine/src/eval.cpp`: `evaluate_king_safety_bb` — attacker units into the king zone
(knight+2/bishop+2/rook+3/queen+5), mapped through a bounded non-linear `kKingDanger[]`
table (0 for a lone attacker, ramping to ~270). Magic-backed (cheap). Folded into
`evaluate_static`.

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8.
- Verification (200 games, 8+0.08) vs v022: **32-64-104, −56.1 Elo ±24.9, 0 illegal.**

## Results

```json
{"vs_v022": {"w": 32, "l": 64, "d": 104, "games": 200, "elo_diff": -56.1, "elo_err": 24.9, "illegal": 0}}
```

## Decision

**Rejected.** −56 Elo, almost identical to exp033's −60 — despite the cost now being cheap
(magic) and the weighting gentler. Reverted; head stays `versions/v022-magic-bitboards`.

## Reason — corrects the exp033 diagnosis

The cost theory was wrong: making it cheap did **not** help. The king-safety *term itself*
hurts this engine's play — an attacker-count penalty distorts the otherwise strong
material + PST + pawn-structure + mobility eval, biasing move choice badly. King safety has
now failed three times (exp019 pawn-shield neutral; exp033 −60; exp035 −56). **Stop trying
king-safety variants** until there's a fundamentally different, tuned model (and ideally
SPSA-tuned weights), not another hand-set attacker table.

## Notes

- General lesson: a hand-tuned eval term with a large dynamic range (here up to ~270 cp)
  can easily do net harm; bounded/SPSA-tuned weights are needed. Mobility worked because
  its per-square weights are small and uniformly positive-sum.

## Next experiment idea

- **PVS retry** — rejected twice (exp023/025) for node cost; magic bitboards made nodes
  materially cheaper, so re-test.
- **Re-anchor vs Stockfish** at `--anchor-elo ~2100` to confirm the absolute rating.
- **Tune mobility weights** (small, proven-positive term) — low-risk fine-tuning.
