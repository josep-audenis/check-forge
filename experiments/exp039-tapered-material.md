# Experiment exp039 — Tapered material (PeSTO mg/eg piece values)

## Hypothesis

exp038 tapered the PST but material was still flat config values. Fold PeSTO midgame/endgame
piece values into the same phase blend so material, like position, shifts with the game
phase (e.g. rooks worth more in the endgame, minor pieces less).

## Change

`engine/src/eval.cpp`: added `kMgVal`/`kEgVal` (PeSTO material by type), and `evaluate_static`
now accumulates `mg += kMgVal[t] + kPstMg[t][idx]`, `eg += kEgVal[t] + kPstEg[t][idx]`
(white; mirrored for black) and interpolates by phase — the flat `evaluate_material` base is
no longer used inside `evaluate_static`. Config piece values still drive SEE / MVV-LVA
ordering / null-move material checks (unchanged).

## Files changed

- `engine/src/eval.cpp`

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8. Startpos eval = 0 (symmetric).
- Verification (400 games over two detached batches, varied openings, 8+0.08) vs v023:
  **113-74-213, +34.0 Elo ±17.5 (1σ), LOS ~97%, 0 illegal.** (Batch A +17.4, B stronger.)

## Results

```json
{"vs_v023": {"w": 113, "l": 74, "d": 213, "games": 400, "elo_diff": 34.0, "elo_err": 17.5, "illegal": 0}}
```

## Decision

**Accepted (strength).** New head `versions/v024-tapered-material`.

## Reason

+34 Elo over 400 games at LOS ~97%, both batches positive, correctness preserved. Tapered
material compounds the exp038 tapered-PST win: the PeSTO values (esp. rook/pawn gaining and
minors losing into the endgame) improve phase-appropriate trading and conversion. Batch A
alone (+17) was borderline — the 400-game confirm was necessary (per the exp030 lesson).

## Notes

- The eval material scale is now PeSTO (P82/N337/B365/R477/Q1025 mg), diverging from the
  config values (P100/N320/B330/R500/Q900) that still serve SEE/ordering. That split is
  intentional and worked; a future cleanup could unify them or SPSA-tune the eval values.

## Next experiment idea

- **SPSA on the tapered base** — mobility / pawn-structure / bishop-pair optima have likely
  shifted; re-run the harness now.
- **Tapered pawn-structure / bishop-pair**, or **SEE capture ordering** (reuse see_capture).
- **Re-anchor vs Stockfish** — two eval wins (exp038 +110, exp039 +34) since the last
  anchor; measure the absolute again.
