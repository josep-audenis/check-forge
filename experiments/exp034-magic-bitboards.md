# Experiment exp034 — Magic bitboards (O(1) slider attacks)

## Hypothesis

Slider attacks were O(ray) loops, called heavily per node (movegen, `is_square_attacked`,
and especially mobility eval — 4 slider lookups per slider piece per leaf). exp033 showed
the per-leaf slider budget was exhausted. Replace ray loops with magic bitboards (O(1)
multiply+shift table lookups). Should recover the depth that mobility spent → Elo, and
re-open room for more eval.

## Change

`engine/src/bitboard.cpp`: `bishop_attacks` / `rook_attacks` now index magic tables
(unchanged signatures). Init-time generation: relevant-occupancy masks, deterministic
random sparse magic search (fixed seed → reproducible), attack tables built from the ray
truth. Knight/king/pawn tables unchanged.

## Files changed

- `engine/src/bitboard.cpp`

## Tests run

- Unit: pass. **Perft: exact at all cases** (the gate — magic attacks must equal the ray
  truth). Tactics: 8/8.
- Speed: fixed depth-9 **24.3s vs 29.4s for v021 → ~18% faster** at one position; the
  in-game gain is larger because slider attacks are called far more often there.
- Verification (400 games over two detached batches, varied openings, 8+0.08) vs v021:
  **151-41-208, +98.1 Elo ±18.1 (1σ), LOS ~100%, 0 illegal.** Both batches +98.

## Results

```json
{
  "depth9_s": {"magic": 24.3, "v021": 29.4},
  "vs_v021": {"w": 151, "l": 41, "d": 208, "games": 400, "elo_diff": 98.1, "elo_err": 18.1, "illegal": 0}
}
```

## Decision

**Accepted (strength).** New head `versions/v022-magic-bitboards`.

## Reason

+98.1 Elo over 400 games, LOS ~100%, both batches identical, correctness preserved (perft
exact, tactics 8/8). A pure speed change worth +98 because v021's mobility eval makes the
slider-attack path extremely hot (per leaf); O(1) magic recovers almost all of mobility's
1.55× cost → large effective depth gain. The single-position 18% understates it.

## Notes — the bitboard investment compounding

The bitboard arc: exp031 movegen (neutral alone) → exp032 mobility (+96, the eval the
bitboards enabled) → exp034 magic (+98, recovering the eval's cost). Pure-speed changes are
neutral when the hot path is light (exp026/027/031) and large when it is heavy (here, after
mobility). The lesson: re-measure "infrastructure" speedups after the workload that stresses
them lands.

## Next experiment idea

- **Retry king safety (exp033)** — it failed mostly on cost; slider attacks are now O(1),
  so an attacker-count term should be affordable. Use a tuned non-linear attack table.
- **PVS retry** — nodes are meaningfully cheaper now.
- **Re-anchor vs Stockfish** at a higher `--anchor-elo` (≈2100) to confirm the absolute.
- Tune mobility weights; tapered eval.
