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
research/run_benchmark.py  aggregate suite runner
```

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
