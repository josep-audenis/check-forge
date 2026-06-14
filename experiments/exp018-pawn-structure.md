# Experiment exp018 — Pawn-structure evaluation

## Hypothesis

The eval was material + crude positional + bishop pair, with **no pawn-structure
understanding** at all. Adding doubled / isolated / passed-pawn terms is a purely additive
signal (new information, low regression risk) and, unlike search micro-tweaks, an eval
term is measurable at the current depth. Roadmap step 3 (real evaluation).

## Change

`engine/src/eval.cpp`: new `evaluate_pawn_structure()` (White-perspective), folded into
`evaluate_static`:
- **Doubled**: −15 per extra pawn on a file.
- **Isolated**: −12 for a pawn with no friendly pawn on adjacent files.
- **Passed**: bonus by rank advanced `{10,17,25,40,65,100}` (no enemy pawn on the same or
  adjacent files ahead).

Weights hardcoded (like the existing `kBishopPairBonus`); config exposure deferred.

## Files changed

- `engine/src/eval.cpp`

## Expected effect

Better pawn play and endgame conversion (the engine drew/repeated a lot); a measurable
Elo gain over v012.

## Risks

A bad sign or rank-orientation bug could weaken play. Gated by perft (unaffected) and
tactics (must stay 8/8).

## Tests run

- Unit (ctest): pass.
- Perft: exact (eval does not touch movegen).
- Tactical suite: 8/8.
- Verification (200 games, varied openings, 8+0.08), exp018 vs v012:
  **77-48-75, +50.7 ±38.3 Elo, LOS 99.5%, 0 illegal/flags.**
- Anchor (200 games, 8+0.08): vs SF1700 90-99-11 → 1684 ±47; vs SF1800 136-61-3 → 1937 ±52.

## Results

```json
{
  "internal_vs_v012": {"w": 77, "l": 48, "d": 75, "elo_diff": 50.7, "elo_err": 38.3, "los": 99.5},
  "anchor_vs_SF1700": {"w": 90, "l": 99, "d": 11, "checkforge_elo": 1684.4, "elo_err": 47.1},
  "anchor_vs_SF1800": {"w": 136, "l": 61, "d": 3, "checkforge_elo": 1937.0, "elo_err": 52.0},
  "absolute_elo_estimate": "~1765 (internal ladder: v011/v012 ~1714 + 51)"
}
```

## Decision

**Accepted (strength).** New head `versions/v013-pawn-structure`.

## Reason

+50.7 Elo internal over v012 with LOS 99.5% clears the +15 threshold; correctness
preserved (perft exact, tactics 8/8, 0 illegal). The internal head-to-head is the
controlled, trustworthy measure of the gain.

## Notes — anchor is too noisy to pin absolute Elo here

The Stockfish anchor gave **contradictory** absolutes for the same engine: SF1700 → 1684,
SF1800 → 1937, while internally v013 is clearly +51 over v012 (≈ v011's 1714 tier, which
itself anchored ~50% vs SF1700). Causes: (a) ±47 anchor error at 200 games can't resolve
a ~50-Elo change; (b) `UCI_Elo` is miscalibrated at bullet TC and compresses/saturates
(SF1800 score was 68% → inflated). **Use the internal version-vs-version ladder for
deltas; treat the SF anchor as a coarse band only.** Best current estimate ≈ 1750–1765.

## Next experiment idea

Continue real eval (roadmap step 3): **king safety** (pawn-shield / open-file-near-king
penalty) or **mobility**, each a distinct additive term. For a tighter absolute number,
either raise game counts or anchor at a single fixed SF level and only compare deltas
there. Re-measure on the internal ladder vs v013.
