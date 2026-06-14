# Experiment exp009-varied-openings

## Hypothesis

Every version-vs-version match (exp001-008) ended 0-0-N, all draws by 3-fold
repetition. Two deterministic engines from the same startpos play the same game, so
no change can ever be decisive. Starting each game from a varied opening should make
near-identical engines diverge and let real strength differences surface as wins.

## Change

- Added `data/openings.epd` (12 common opening positions, 1-2 plies in).
- `research/run_cutechess.py`: new `--openings` arg (default `data/openings.epd`).
  When the file exists, passes `-openings file=... format=epd order=random -repeat`
  to cutechess so each opening is played by both engines with colors reversed.

No engine code changed. This is a measurement-protocol fix, not a result edit.

## Files changed

- `data/openings.epd`
- `research/run_cutechess.py`

## Expected effect

Decisive games appear; cutechess Elo becomes a usable signal instead of a flat 0.5.

## Risks

A bad opening FEN would crash games. All 12 are legal early positions and were
exercised in the baseline matrix below without errors.

## Tests run

Baseline matrix, 20 games each, tc=4+0.1, varied openings:

- v007 vs v000 (positional eval vs material-only): **15 - 0 - 5**
- v007 vs v005: 4 - 6 - 10, Elo -34.9 +/- 111
- v006 vs v005: 6 - 6 - 8, Elo 0.0 +/- 122.6

## Results

```json
{
  "v007_vs_v000": "15 - 0 - 5",
  "v007_vs_v005": "4 - 6 - 10",
  "v006_vs_v005": "6 - 6 - 8",
  "decisive_games_now_possible": true
}
```

## Decision

Accepted

## Reason

The metric works: with varied openings, games are decisive. v007 dominates the
material-only v000 15-0-5 — the **first clear wins in the project**. The previous
"no Elo gain" across exp001-008 was a measurement artifact (fixed-start repetition
draws), not a property of the engine changes.

## Notes

The adjacent-version results (v007 vs v005, v006 vs v005) are statistical noise at
20 games: the small eval/ordering tweaks (positional v2, MVV-LVA, bishop-pair) are
roughly strength-neutral. Only the large accumulated difference (eval vs no eval) is
clearly decisive. Big honest lesson: prior accept-as-infrastructure calls were
correct to claim "no measurable Elo" — they just couldn't measure it at all.

## Next experiment idea

With a working metric, the dominant strength lever is search depth, but the engine
ignores the clock and searches a fixed depth, flagging when that depth is too slow
(exp004). Implement iterative deepening + time management so the engine searches as
deep as time allows without losing on time.
