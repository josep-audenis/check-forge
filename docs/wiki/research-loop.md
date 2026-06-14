# Research Loop

Research loop turns engine development into controlled experiments.

## Loop

```text
1. Load current engine state.
2. Read previous experiments.
3. Propose one experiment.
4. Apply change.
5. Build engine.
6. Run correctness tests.
7. Run benchmarks.
8. Evaluate result.
9. Accept or reject.
10. Write experiment report.
11. Update wiki if behavior, workflow, schema, or roadmap changed.
```

## First Mode

Start semi-manual:

```text
- agent proposes experiment
- human approves
- scripts run benchmark
- human reviews result
- agent records report
```

Automate only after commands, schemas, and acceptance rules stabilize.

## Current State And Commands

Head version is the highest-numbered `versions/vNNN-*/` (v010-tt-move-ordering as of
2026-06-13). The live tree builds the head; accepted experiments freeze a new snapshot.

Build and gate (call tools directly; `task.ps1 -ExecutionPolicy Bypass` is blocked by
the sandbox):

```text
cmake -S . -B build; cmake --build build
ctest --test-dir build --output-on-failure
python research/run_tactics.py --engine build/engine/checkforge.exe   # 8/8
python research/run_perft.py   --engine build/engine/checkforge.exe
python research/run_benchmark.py --engine build/engine/checkforge.exe \
  --opponent-engine versions/<head>/checkforge.exe \
  --opponent-config versions/<head>/default.json \
  --experiment-id expNNN-<slug> --output results/expNNN-<slug>.json
python research/run_cutechess.py --engine build/engine/checkforge.exe \
  --opponent-engine versions/<head>/checkforge.exe \
  --opponent-config versions/<head>/default.json \
  --tc 8+0.08 --output results/expNNN-<slug>-cutechess.json \
  --pgn matches/expNNN-<slug>.pgn
```

## Screening vs Verification

```text
- Screening (<= ~40 games): kill disasters fast; cannot confirm small gains.
- Verification (200+ games or SPRT): required before any strength accept/reject.
```

See [[acceptance-rules]]. Strategy and priority order: [[roadmap-to-2000]].

## Experiment Discipline

Rules:

```text
- one hypothesis per experiment
- one main change per experiment
- no benchmark script edits to improve result
- no past result edits
- no skipped perft/correctness tests
- no acceptance based only on theory
- every accepted change needs benchmark support
```

## Example First Experiment

Hypothesis:

```text
Engine undervalues bishops compared with knights.
```

Change:

```text
bishop value 330 -> 340
```

Test:

```text
200 games against previous version using fixed openings.
```

Decision:

```text
Accept or reject based on benchmark result and acceptance rules.
```

## Links

- [[acceptance-rules]]
- [[experiment-template]]
- [[data-contracts]]

