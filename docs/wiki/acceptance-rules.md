# Acceptance Rules

Benchmarks decide whether changes stay.

## Automatic Reject

Reject automatically if:

```text
- engine fails to build
- any perft test fails
- engine crashes during match
- illegal move occurs
- tactical accuracy drops more than 3%
- nodes/sec drops more than 15% without clear Elo gain
```

## Accept Conditions

Accept only if:

```text
- correctness tests pass
- no crashes
- performance does not regress badly
- match result justifies keeping change
```

## Screening vs Verification

Two kinds of match run, do not confuse them:

```text
- Screening: small (<= ~40 games). Cheap. Only catches DISASTERS:
  flags/time losses, crashes, illegal moves, large (>100 Elo) regressions.
  Error is +-70..120 Elo, so it CANNOT confirm a small improvement.
  Use it to kill obviously-bad ideas fast.
- Verification: 200+ games, or SPRT. Required before any strength-based
  accept/reject. This is the only evidence that justifies an Elo claim.
```

Never report a single-digit / low Elo delta from a screening match as a gain.

## Strength Accept Rule

Accept on strength only if a VERIFICATION match shows:

```text
- at least +15 Elo over baseline
- at least 200 games (or an SPRT pass, e.g. elo0=0 elo1=10 alpha=0.05 beta=0.05)
- tactical accuracy does not drop more than 2%
- zero time losses / illegal moves
```

`research/run_cutechess.py` defaults to `--games 200` with varied openings. Add
cutechess `-sprt elo0=0 elo1=10 alpha=0.05 beta=0.05` for sequential testing.

## Infrastructure Accept (no measured Elo)

A correct, zero-downside change with no measurable Elo (e.g. a search technique that
only pays off at greater depth) may be accepted as INFRASTRUCTURE, but the report must
say so explicitly and must NOT claim an Elo gain. Examples in history: quiescence
(exp001), check extension (exp005), transposition table (exp013).

Caveat from exp011-exp014: at the current shallow depth (~3-4), search micro-changes
read as noise at bullet TC. Do not accept them as strength gains; prefer the structural
work in [[roadmap-to-2000]].

## Absolute Elo (anchor)

An Elo anchor now exists (exp015): `research/run_anchor.py` plays CheckForge vs
Stockfish pinned to a known `UCI_Elo` and reports `checkforge_elo = anchor_elo +
cutechess Elo diff`. Use it to state results in absolute Elo, not only relative deltas.
Pin `--anchor-elo` near the expected level so the match scores ~50% (tightest error).
Caveat: `UCI_Elo` is calibrated for slower TC, so the bullet number is an anchored
estimate. v010 baseline ≈ 1581 ±47.

## Future Improvement

Wire SPRT directly into `run_cutechess.py` / `run_anchor.py`. Add a longer-TC anchor run
for a calibration-exact number.

## Links

- [[research-loop]]
- [[data-contracts]]

