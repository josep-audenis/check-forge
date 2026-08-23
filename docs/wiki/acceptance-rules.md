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
- Smoke: small (<= ~40 games). Cheap. Only catches DISASTERS:
  flags/time losses, crashes, illegal moves, large (>100 Elo) regressions.
  Error is +-70..120 Elo, so it CANNOT confirm a small improvement.
  Use it to kill obviously-bad ideas fast.
- Screening: 100-400 paired games. Useful for large effects, still too noisy for
  precise low-double-digit Elo claims.
- Verification: pair-level anytime-valid sequential test with predeclared bounds, or
  enough fixed games for desired 95% interval. Required before strength accept/reject.
```

Never report a single-digit / low Elo delta from a screening match as a gain.

## Strength Accept Rule

Accept on strength only if a VERIFICATION match shows:

```text
- at least +15 Elo over baseline
- paired sequential H1 decision (e.g. elo0=0 elo1=10 alpha=0.05 beta=0.05), or
  fixed-game 95% confidence interval wholly above 0 Elo
- tactical accuracy does not drop more than 2%
- zero time losses / illegal moves
```

`research/run_cutechess.py` exposes pair-level sequential bounds through legacy-named
`--sprt-elo0`, `--sprt-elo1`, `--sprt-alpha`, and `--sprt-beta`. Cute Chess itself
does not decide: harness applies anytime-valid bounded-score evidence to ordered
opening-pair averages. Harness writes a seeded IID-with-replacement schedule from
semantically unique source positions and records its hash.
Sequential evidence requires concurrency 1 and exact PGN-to-schedule pair order.

## Infrastructure Accept (no measured Elo)

A correct, zero-downside change with no measurable Elo (e.g. a search technique that
only pays off at greater depth) may be accepted as INFRASTRUCTURE, but the report must
say so explicitly and must NOT claim an Elo gain. Examples in history: quiescence
(exp001), check extension (exp005), transposition table (exp013).

Caveat from exp011-exp014: at the current shallow depth (~3-4), search micro-changes
read as noise at bullet TC. Do not accept them as strength gains; prefer the structural
work in [[roadmap-to-2000]].

## Absolute Elo (anchor)

`research/run_anchor.py` measures against one declared external rating.
`research/aggregate_anchors.py` combines distinct engine families with random effects,
reports spread/I-squared/tau-squared, and rejects heterogeneous pools. One Stockfish
`UCI_Elo` setting remains coarse calibration, not FIDE Elo. Precise public claims need
multiple families and both STC/LTC measurements.
Duplicate family or binary rows invalidate aggregate; they never receive extra weight.

## Confidence Targets

Near 50% score, rough independent-game requirements for a two-sided 95% interval are:

```text
+-20 Elo: ~1,200 games
+-10 Elo: ~4,600 games
+-5 Elo:  ~18,500 games
```

Paired pentanomial variance determines exact requirements. Never describe one standard
error as a 95% uncertainty interval.

## Links

- [[research-loop]]
- [[data-contracts]]
