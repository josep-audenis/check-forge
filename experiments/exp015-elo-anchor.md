# Experiment exp015 — Elo anchor

## Hypothesis

CheckForge has never had an absolute Elo: every match was version-vs-version. With a
known-rated reference opponent, a verification match places CheckForge on a real Elo
scale, which is the prerequisite for measuring all later structural work (roadmap step 1).

Hypothesis: Stockfish 18 pinned via `UCI_LimitStrength` + `UCI_Elo` is a usable,
tunable anchor, and CheckForge v010's true strength is well above the earlier sub-1000
guess.

## Change

Infrastructure only — no engine change. CheckForge binary under test is the frozen
head `versions/v010-tt-move-ordering`.

- Installed Stockfish 18 (winget `Stockfish.Stockfish`, avx2 build) as the anchor.
- Added `research/run_anchor.py`: runs cutechess-cli with CheckForge vs Stockfish
  pinned to a chosen `UCI_Elo`, parses the final score and Elo difference, and computes
  the absolute rating `checkforge_elo = anchor_elo + elo_difference`. Auto-detects
  cutechess-cli and Stockfish under the winget package dir. Resolves the engine path to
  absolute (Python 3.14 on Windows no longer resolves relative exe paths via subprocess).

## Files changed

- `research/run_anchor.py` (new)

## Expected effect

A first absolute Elo for CheckForge, plus reusable tooling so future experiments report
real Elo, not just relative deltas.

## Risks

- Stockfish's `UCI_Elo` floor is 1320; anchors below that are unavailable via this knob.
- `UCI_Elo` is calibrated for slower TC; at bullet (8+0.08) Stockfish likely plays a bit
  above its nominal rating, so the absolute number carries a TC/calibration caveat. It
  is an anchored estimate, not a CCRL-exact rating.

## Tests run

- Perft / tactical / unit: N/A — engine binary unchanged from v010 (already gated).
- Anchor probes (small, noisy): vs SF1320 15-5 (~1510), vs SF1500 8-4 (~1620),
  vs SF1700 5-11 (~1563). Bracketed CheckForge ~1550-1600 → picked SF1600 for the
  verification run (near 50%, tightest error).
- Verification (200 games, varied openings, 8+0.08): see Results.

## Results

```json
{
  "anchor": "Stockfish 18, UCI_LimitStrength + UCI_Elo=1600",
  "tc": "8+0.08",
  "wins": 90, "losses": 101, "draws": 9, "games": 200,
  "elo_difference": -19.1,
  "checkforge_elo": 1580.9,
  "checkforge_elo_error": 47.3,
  "los_percent": 21.3,
  "flags_or_illegal": 0
}
```

**CheckForge v010 ≈ 1581 ±47 Elo** (anchor SF1600, 90-101-9, ~47% score).

## Decision

Accepted as INFRASTRUCTURE + measurement. No Elo gain is claimed for the engine (engine
unchanged). Head stays `v010`; no new version snapshot.

## Reason

Zero-downside tooling that satisfies roadmap step 1: every future experiment can now be
reported in absolute Elo via `research/run_anchor.py`. The 200-game verification run is
near 50%, giving a tight ±47 estimate. Clean run, 0 flags / illegal moves.

## Notes

- Big correction to prior belief: the engine is ~1580, not "well under 1500 / sub-1000".
  Material + crude PST + quiescence + check extension at depth 3-4 is more tactical than
  assumed.
- The anchor is tunable: set `--anchor-elo` near the expected level so the match scores
  ~50% for the tightest error bars.
- TC caveat stands — for a calibration-exact number, re-run the anchor at a longer TC
  later. The bullet number is consistent with the rest of the match history (all at
  8+0.08), so it is the right baseline for comparing future work tested the same way.

## Next experiment idea

Roadmap step 2: faster move generation (make-unmake / bitboards) to replace
make-on-copy. It is the depth limiter and the single biggest strength lever; one ply was
worth +147 Elo here. Gate hard with perft, then re-run `run_anchor.py` at SF1600 to
measure the absolute Elo gain.
