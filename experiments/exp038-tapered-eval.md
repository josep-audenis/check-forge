# Experiment exp038 — Tapered evaluation (midgame/endgame PST)

## Hypothesis

The crude positional term (centrality/advance) is phase-blind, and the exp020 mg-only PST
swap was neutral because it just re-encoded centrality. Use PeSTO **midgame + endgame**
piece-square tables interpolated by game phase: the endgame tables (king to the centre,
pawns pushing, etc.) add real signal exactly where the old eval was weakest.

## Change

`engine/src/eval.cpp`: replaced `positional_value`/`central_bonus` with PeSTO `kPstMg[6][64]`
and `kPstEg[6][64]` (index 0 = a8; black mirrors via `sq^56`). `evaluate_static` accumulates
mg/eg sums and game phase (N=1,B=1,R=2,Q=4; max 24) and interpolates
`(mg*phase + eg*(24-phase))/24`. Material (config), bishop pair, pawn structure, and
mobility unchanged.

## Files changed

- `engine/src/eval.cpp`

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8. Startpos eval = 0 (symmetric → orientation ok).
- Verification (400 games over two detached batches, varied openings, 8+0.08) vs v022:
  **181-58-161, +110.4 Elo ±18.3 (1σ), LOS ~100%, 0 illegal.** (Batch A +113.3, B ~+108.)

## Results

```json
{"vs_v022": {"w": 181, "l": 58, "d": 161, "games": 400, "elo_diff": 110.4, "elo_err": 18.3, "illegal": 0}}
```

## Decision

**Accepted (strength).** New head `versions/v023-tapered-eval`. Biggest eval gain since
bitboard mobility — breaks the post-2000 plateau.

## Reason

+110 Elo over 400 games at LOS ~100%, both batches consistent, correctness preserved
(perft exact, tactics 8/8). The phase interpolation is the key: the same PeSTO mg tables
alone (exp020) were neutral, but blending toward endgame tables as material comes off fixes
the engine's weakest phase. Confirms the recurring lesson — a rejected idea (PST, exp020)
can become a big win once the missing ingredient (here, the endgame half + phase blend) is
added.

## Notes

- Material values are still the flat config values; PeSTO's tapered material could be a
  further small gain (future).
- This breaks the plateau that the last six experiments (king-safety ×3, scaled-LMR,
  mobility-SPSA, SEE) had hit.

## Next experiment idea

- **SPSA-tune** mobility/pawn-structure/bishop-pair on top of the new tapered base (the
  optimum may have shifted).
- **Tapered material** (PeSTO mg/eg piece values) and/or tapered pawn-structure.
- **SEE for capture ordering** (reuse `see_capture`), retry king safety with the stronger
  base, or re-anchor vs Stockfish to track the absolute.
