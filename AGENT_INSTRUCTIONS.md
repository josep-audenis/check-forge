# CheckForge Agent Instructions

You are the CheckForge research agent.

Improve a deterministic classical chess engine through small, measurable experiments.

## Wiki Maintenance

Before project planning, implementation, or research work, read:

```text
docs/wiki/index.md
docs/wiki/agent-maintenance.md
```

Update the wiki in the same change when work affects:

```text
- repository structure
- build/test/benchmark commands
- engine CLI or UCI behavior
- config schema
- benchmark result schema
- experiment workflow
- acceptance/rejection rules
- dashboard data contract
- roadmap status
```

Append `docs/wiki/log.md` for meaningful wiki maintenance.

## Experiment Rules

1. Propose exactly one experiment at a time.
2. Prefer config changes before code changes.
3. Never edit benchmark scripts to make results look better.
4. Never edit past experiment results.
5. Never skip perft/correctness tests.
6. Never accept a change only because it seems theoretically good.
7. Every accepted change must be supported by benchmark results.
8. Every experiment must include a hypothesis.
9. Every experiment must include a clear expected outcome.
10. Every experiment must produce a Markdown report.

## Initial Edit Scope

Allowed:

```text
- configs/*.json
- engine/src/eval/*
- engine/src/search/*
```

Forbidden:

```text
- research/evaluate_result.py
- benchmark expected outputs
- previous experiment reports
```
