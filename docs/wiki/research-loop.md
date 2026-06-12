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

