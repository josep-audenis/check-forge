# Benchmark Harness

This page describes the implemented gate before autoresearch starts changing chess strength.

## Commands

Windows:

```powershell
powershell -ExecutionPolicy Bypass -File task.ps1 test
powershell -ExecutionPolicy Bypass -File task.ps1 benchmark
powershell -ExecutionPolicy Bypass -File task.ps1 cutechess
```

Linux/macOS:

```bash
make test
make benchmark
make cutechess
```

`cutechess` requires `cutechess-cli` on `PATH`. If unavailable, `research/run_cutechess.py` writes a skipped JSON result.

## Implemented Benchmarks

```text
research/run_perft.py      rule correctness
research/run_tactics.py    fixed material bestmove checks
research/run_speed.py      perft nodes per second
research/run_match.py      internal UCI engine-vs-engine smoke games
research/run_cutechess.py  external cutechess validation
research/score_pgn.py      paired PGN statistics + validation
research/run_anchor.py     one externally rated anchor
research/aggregate_anchors.py  independent-anchor aggregation
research/run_measurement.py    screen/verify/claim profile runner
research/run_benchmark.py  aggregate suite runner
```

## Measurement v2

Every external match now records:

```text
- candidate, opponent, Cute Chess, config, and opening-file SHA-256
- engine/tool versions, git commit, CPU/OS/Python metadata
- time control, maximum games, RNG seed, concurrency, and command line
- W-L-D plus colour-paired pentanomial counts
- explicitly labeled confidence level and Elo confidence interval
- pair-level anytime-valid sequential evidence with predeclared Elo bounds
- completed-game count, pair validity, illegal moves, and engine time losses
```

`elo_err` is compatibility output but now means requested-confidence half-width
(95% by default), not one standard error. `elo_se` remains available separately.
When paired openings are complete, one colour-swapped opening pair is one independent
statistical sample.

Run Python measurement tests:

```powershell
powershell -ExecutionPolicy Bypass -File task.ps1 measurement-test
```

Score or recover an existing PGN strictly:

```powershell
python research/score_pgn.py matches/run.pgn `
  --engine checkforge --expected-games 1200 --require-pairs --strict
```

Run a reproducible relative sequential match:

```powershell
python research/run_cutechess.py `
  --engine build/engine/checkforge.exe `
  --opponent-engine versions/v024-tapered-material/checkforge.exe `
  --games 5000 --tc 8+0.08 --seed 1 --concurrency 1 `
  --sprt-elo0 0 --sprt-elo1 10 --sprt-alpha 0.05 --sprt-beta 0.05
```

Cute Chess runs the fixed maximum game count. Harness evaluates ordered opening pairs
with a paired Hoeffding e-process and retains first boundary crossing. This avoids
Cute Chess's game-level trinomial SPRT, whose alpha/beta guarantees do not cover
correlated colour-paired games. CLI keeps `--sprt-*` names for compatibility.

## Measurement Profiles

`run_measurement.py` defaults to plan-only. Add `--execute` after checking preflight.

```text
smoke   12+ unique positions, 24 games, integrity only; no strength inference
screen  12+ unique positions, 400 STC games, paired 0/20 Elo sequential test
verify  100+ unique positions, 5000 STC games + 1200 LTC games, 1+ anchor
claim   500+ unique positions, 4600 STC + 1200 LTC games, 3 anchor families
```

Show why current opening suite fails professional preflight:

```powershell
python research/run_measurement.py `
  --engine build/engine/checkforge.exe `
  --baseline-engine versions/v024-tapered-material/checkforge.exe `
  --profile screen
```

Verify/claim reject current 12-position file; smoke and screen accept it at their
stated evidence limits. Harness samples pair positions IID with replacement into a
seeded, hashed schedule, then gives Cute Chess sequential order. EPD operation text
after first four FEN fields does not inflate source diversity. Supply a larger curated
suite. Configure anchors using `configs/anchors.example.json`; claim mode requires
distinct binary hashes and distinct engine-family IDs. Several settings, builds, or
versions from one Stockfish family do not count as independent anchors. Anchor families
receive different deterministic schedule seeds to avoid reusing identical pair samples.
Scorer compares every PGN pair FEN against preassigned schedule order. Sequential
profiles require concurrency 1; reordered or reused positions invalidate measurement.

`measurement_valid` means match data passed integrity checks. `profile_passed` means
strength criterion passed. H0 and inconclusive sequential outcomes remain valid data
but fail profile. Fixed relative stages require point estimate at least +15 Elo and
confidence-interval lower bound above zero. Claim profile also requires each anchor
aggregate lower bound to clear target 2500 engine-pool Elo (override with
`--target-elo`). This scale is not FIDE Elo.

## Outputs

```text
results/latest.json
results/<experiment_id>/summary.json
results/<experiment_id>/perft.json
results/<experiment_id>/tactics.json
results/<experiment_id>/speed.json
results/<experiment_id>/match.json
matches/latest.pgn
```

## Engine Comparison

Use current engine against another binary:

```powershell
python research/run_benchmark.py --engine build/engine/checkforge.exe --opponent-engine old/checkforge.exe
```

Use different configs:

```powershell
python research/run_benchmark.py --engine build/engine/checkforge.exe --config configs/default.json --opponent-config configs/other.json
```

## Readiness Rule

Autoresearch can start when:

```text
- task.ps1 test passes
- task.ps1 benchmark passes
- results/latest.json has accepted=true
- cutechess either passes or is explicitly skipped because cutechess-cli is unavailable
```
