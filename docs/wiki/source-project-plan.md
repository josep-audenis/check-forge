# Source: PROJECT-PLA.md

Source file:

```text
PROJECT-PLA.md
```

## Summary

Original project plan defines CheckForge as an AutoResearch lab for deterministic chess engines.

Main idea:

```text
AI suggests. Benchmarks decide.
```

Key decisions:

```text
- C++17 engine
- Python research orchestration
- JSON configs
- Markdown experiment logs
- UCI support eventually
- cutechess-cli for automated games
- perft before search
- no neural networks
- no frontend before engine works
```

## Extracted Structure

Planned directories:

```text
engine/
research/
benchmarks/
matches/
experiments/
configs/
data/
docs/
dashboard/
```

This wiki normalizes that into [[system-architecture]].

## Extracted Roadmap

Roadmap from source:

```text
1. repository setup
2. board and move generation
3. basic engine
4. UCI protocol
5. search improvements
6. configurable parameters
7. benchmark harness
8. AutoResearch loop
9. dashboard later
```

See [[implementation-roadmap]].

## Extracted Rules

Important rules:

```text
- do not implement advanced search until perft is reliable
- propose exactly one experiment at a time
- prefer config changes before code changes
- never edit benchmarks to improve results
- never edit past experiment results
- never skip correctness tests
```

See [[research-loop]] and [[acceptance-rules]].

