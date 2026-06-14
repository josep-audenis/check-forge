# Experiment exp006-tactical-suite

## Hypothesis

The two-case tactical suite (`free-queen`, `free-rook`) is too shallow to measure
search strength, so every recent experiment reports "no Elo gain detected" with no
way to see tactical regressions. A broader suite of verified positions will give a
real accuracy metric for future search/eval changes.

This is the explicit "next experiment idea" recorded in exp005.

## Change

Expanded `research/run_tactics.py` CASES from 2 to 8. Added six positions with
independently verified unique best moves:

- `mate-back-rank` (Ra8#, depth 3)
- `mate-scholars-qf7` (Qxf7#, depth 3)
- `win-bishop-rxd3` (Rxd3, depth 2)
- `win-rook-fork-nxe6` (Nxe6 winning the rook, depth 3)
- `win-knight-rxd5` (Rxd5, depth 2)
- `royal-fork-nc7` (Nc7+ forking king and rook, depth 3)

No engine code changed. This raises the measurement bar; it does not alter expected
outputs to make existing results look better.

## Files changed

- `research/run_tactics.py`

## Expected effect

Future experiments get a sensitive tactical-accuracy signal instead of a binary
2/2. Baseline v005 should pass all 8 (the cases were chosen from positions v005
already solves), establishing 8/8 as the reference.

## Risks

If any added position were ambiguous (multiple best moves) it could flag a false
regression. Ambiguous multi-mate positions encountered during selection were
discarded; only forced/unique solutions were kept.

## Tests run

- Tactical suite (v005): 8/8 solved
- Perft / speed / match: unaffected (no engine change)

## Results

```json
{
  "tactics": "results/exp006-tactical-suite-tactics.json",
  "baseline": "v005-check-extension",
  "solved": 8,
  "total": 8,
  "passed": true
}
```

## Decision

Accepted

## Reason

Establishes a richer correctness/tactics gate. v005 passes 8/8, confirming no
regression and giving later experiments a meaningful metric. Infrastructure only —
no new engine binary version produced.

## Notes

The earlier attempts at mate-in-2 ground truth were dropped: the engine reached
them by simple material gain rather than a forced mate line, so they were not
reliable forced-mate tests. Kept only positions with a single verifiable best move.

## Next experiment idea

With a real tactical gate in place, make a search-efficiency change (MVV-LVA capture
ordering) and confirm it holds 8/8 while improving node counts.
