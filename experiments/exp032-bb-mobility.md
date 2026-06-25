# Experiment exp032 — Bitboard mobility evaluation

## Hypothesis

Re-do the exp029 mobility term using the v020 bitboard layer. Mobility was rejected in
exp029 only because mailbox ray scans made it 1.66× slower (it still scored +8.7). On
bitboards it should be cheap enough to net a clear gain — and at v020's deeper search the
term should also guide play better than it did on shallow v013.

## Change

`engine/src/eval.cpp`: `evaluate_mobility` rebuilt on bitboards — per minor/major piece,
count reachable squares (`g_knight_attacks` / `bishop_attacks` / `rook_attacks` /
`queen_attacks` against occupancy, minus own pieces) via popcount. Weights N=4/B=4/R=2/Q=1.
Folded into `evaluate_static`.

## Files changed

- `engine/src/eval.cpp`

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8.
- Speed: fixed depth-9 29.8s vs 19.2s for v020 → ~1.55× slower (sliders are still ray
  loops, not magic — eval cost remains, but less than exp029's 1.66×).
- Verification (400 games over two detached batches, varied openings, 8+0.08) vs v020:
  **158-50-192, +96.2 Elo ±18.0 (1σ), LOS ~100%, 0 illegal.** (Batch A +79.5, B even
  stronger.)

## Results

```json
{
  "depth9_s": {"bb_mobility": 29.8, "v020": 19.2},
  "vs_v020": {"w": 158, "l": 50, "d": 192, "games": 400, "elo_diff": 96.2, "elo_err": 18.0, "illegal": 0}
}
```

## Decision

**Accepted (strength).** New head `versions/v021-bb-mobility`. **Biggest eval gain of the
project.**

## Reason

+96.2 Elo over 400 games at LOS ~100%, both batches strongly positive, correctness
preserved (perft exact, tactics 8/8, 0 illegal). Despite still being ~1.55× slower at
fixed depth, the mobility signal is so valuable at this (deeper) search that it dominates
the depth cost — the opposite outcome to exp029 (+8.7 on shallow v013). This is the
payoff the bitboard foundation (exp031) was built for.

## Notes — why exp029 failed and this didn't

Same eval term, opposite verdict. Two things changed: (1) the engine is ~200 Elo stronger
and searches deeper, so mobility's positional guidance converts to results; (2) the
bitboard version is somewhat cheaper (1.55× vs 1.66×). Lesson: an eval term's value is
relative to search depth — re-test rejected eval terms after the search gets stronger.

## Next experiment idea

- **Magic bitboards** for O(1) slider attacks — removes the remaining slider ray-loop cost
  that still makes mobility/attack-detection ~1.5× heavy; would let mobility + king safety
  run nearly free and unlock deeper search.
- **Bitboard king safety** (king-zone attacker count using attack tables) — now cheap and,
  given mobility's success, likely another real gain.
- **PVS retry** (rejected twice for node cost) — re-test now nodes are cheaper.
- Re-measure absolute Elo vs the Stockfish anchor (likely > 2000 now).
