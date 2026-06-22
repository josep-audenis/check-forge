# Experiment exp028 — Aspiration windows

## Hypothesis

Iterative deepening searched every depth with a full window. Searching instead within a
narrow band around the previous iteration's score lets most nodes run with a tighter
window → more cutoffs → a little more depth in the same time → Elo. A tree-size lever
(unlike the neutral per-node changes exp026/027).

## Change

`engine/src/search.cpp`:
- `search_root` takes an optional `[alpha, beta]` window (defaults full → fixed-depth
  callers unchanged) and now beta-cuts on fail-high.
- `search_root_aspiration`: for depth ≥ 4, search `[prev−35, prev+35]`; on fail-low/high
  widen that side and double delta; full window past delta 2000. Shallow depths use a full
  window.
- The timed iterative-deepening loop calls `search_root_aspiration(depth, best.score)`.
  Fixed-depth `search_bestmove` (tactics/tooling) is untouched.

## Files changed

- `engine/src/search.cpp`

## Tests run

- Unit: pass. Perft: exact. Tactics: 8/8 (fixed-depth path unchanged). Timed-search
  sanity: legal moves on startpos + kiwipete.
- Verification (400 games over two detached batches, varied openings, 8+0.08) vs v018:
  **111-78-211, +28.7 Elo ±17.4 (1σ), LOS ~95%, 0 illegal.** (Batch A +41.9, batch B
  +15.6 — both positive.)

## Results

```json
{"vs_v018": {"w": 111, "l": 78, "d": 211, "games": 400, "elo_diff": 28.7, "elo_err": 17.4, "illegal": 0}}
```

## Decision

**Accepted (strength).** New head `versions/v019-aspiration`.

## Reason

+28.7 Elo over 400 games at LOS ~95%, both batches positive, correctness preserved (perft
exact, tactics 8/8, 0 illegal). A standard, low-risk tree-size lever that compounds with
NMP/LMR. Confirms the post-exp027 read: with per-node micro-opts exhausted, gains come
from tree-size (search) and eval, not node cost.

## Notes

- Estimate after v019 ≈ 1955–1975 — essentially at the 2000 target band.
- Aspiration interacts with move-ordering quality; the strong v016 ordering is part of why
  it pays here (few costly re-searches).

## Next experiment idea

- **Mobility evaluation** (untried eval term that re-ranks moves) — likely the next clean
  Elo source, like pawn structure (+51).
- Or **tune existing weights** (pawn-structure / null-move R / LMR threshold) now that the
  structure is in place (roadmap step 5).
- Bitboard movegen remains the only big nps lever (multi-experiment rewrite) for pushing
  well past 2000.
