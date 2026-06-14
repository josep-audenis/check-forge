# Experiment exp007-mvv-lva

## Hypothesis

Capture ordering currently ranks moves by victim value only. Adding least-valuable-
attacker tie-breaking (MVV-LVA) should improve alpha-beta cut efficiency without
changing the moves chosen at a fixed depth, and must hold the expanded tactical
suite at 8/8.

## Change

`engine/src/search.cpp`: replaced the victim-only sort comparator with a
`move_order_key` helper implementing MVV-LVA. Captures/promotions are keyed by
`(victim + promotion) * 100 - attacker`; quiet moves key to 0 and sort last. The
`* 100` factor keeps victim value dominant so a low-value attacker only breaks ties
between equal victims.

## Files changed

- `engine/src/search.cpp`

## Expected effect

Fewer nodes searched in capture-heavy positions; identical best moves at fixed
depth; no tactical regression.

## Risks

A wrong key sign could reorder captures badly and slow search or change results.
Mitigated by the correctness gate (perft, 8-case tactics, match) and cutechess.

## Tests run

- Unit tests: 1/1 passed
- Perft: passed
- Tactical suite: 8/8 (expanded exp006 suite)
- Speed: passed
- Internal match vs v005: passed
- Cutechess vs v005: 20 games at `2+0.1`

## Results

```json
{
  "benchmark": "results/exp007-mvv-lva.json",
  "cutechess": "results/exp007-mvv-lva-cutechess.json",
  "tactics": "8/8",
  "score_vs_v005": "0 - 0 - 20 [0.500]",
  "draw_ratio": "100.0%",
  "elo_diff": 0.0,
  "accepted": true
}
```

## Decision

Accepted

## Reason

All correctness gates pass, tactical suite holds 8/8, and cutechess shows no
regression versus v005. MVV-LVA is a correct, standard ordering refinement. No Elo
gain — and none was reachable here (see Notes).

## Notes

Every cutechess game ended 1/2-1/2 by 3-fold repetition, exactly as in exp001/002/005.
Both engines are deterministic and play the same opening into the same shuffle, so
no ordering or eval change can produce a decisive result at fixed depth — the
**3-fold repetition draw is now the binding constraint on any Elo signal**, not the
search ordering. There is no node-count instrumentation, so the ordering speedup is
asserted by construction, not measured. Logged as a follow-up need.

## Next experiment idea

Two independent threads worth pursuing:
1. Add search-node instrumentation so ordering changes like this one can be measured.
2. Address the repetition draw (e.g. light contempt / avoid repeating a position when
   ahead) so version-vs-version matches can ever be decisive. exp003 showed a naive
   anti-reversal hack is dangerous, so this needs care.
Next concrete step (exp008): bishop-pair eval term — a safe, isolated eval change to
keep exercising the loop while the harder repetition problem is scoped.
