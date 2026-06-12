# Experiment exp005-check-extension

## Hypothesis

Searching one extra ply when the side to move is in check at a leaf will improve mate defense without changing quiet move behavior.

## Change

At `depth == 0`, `negamax` now extends by one ply if the side to move is in check. Otherwise it uses quiescence as before.

## Files changed

- `engine/src/search.cpp`

## Expected effect

Engine should avoid shallow tactical blind spots around checks.

## Risks

Extra nodes in checking lines can slow search.

## Tests run

- Perft: passed
- Tactical suite: 2/2 passed
- Speed: 2,002,644 nodes/sec in perft speed test
- Self-play: passed
- Fixed opponent: v002 positional eval via cutechess, 20 games at `2+0.1`

## Results

```json
{
  "benchmark": "results/exp005-check-extension.json",
  "cutechess": "results/exp005-check-extension-cutechess.json",
  "score_vs_v002": "0 - 0 - 20 [0.500]",
  "draw_ratio": "100.0%",
  "accepted": true
}
```

## Decision

Accepted

## Reason

Correctness gates passed and cutechess showed no regression versus v002. No Elo gain yet.

## Notes

Main remaining weakness is still repetition and lack of decisive conversion. Rejected reversal hack showed breaking repetition without stronger tactics can be bad.

## Next experiment idea

Add a real tactical benchmark set with mate-in-one and mate-in-two positions before further search changes.
