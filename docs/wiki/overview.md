# Overview

CheckForge is an AutoResearch lab for deterministic classical chess engines.

Core rule:

```text
AI suggests. Benchmarks decide.
```

Goal is not a neural engine. Goal is a reproducible loop where an AI coding agent proposes small engine changes, runs experiments, measures results, and accepts or rejects changes using objective benchmarks.

## Constraints

Engine must stay:

```text
- deterministic
- classical/search-based
- no neural network
- no GPU dependency
- explainable
- measurable
```

## First MVP

MVP is not a strong chess engine. MVP is a weak but legal chess engine that can be automatically tested.

Required:

```text
- FEN parser
- board representation
- legal move generation
- basic perft suite
- material evaluation
- alpha-beta search
- minimal UCI
- one JSON config file
- one benchmark result
- one experiment report
```

## Definition Of Success

Project succeeds if it shows:

```text
- deterministic chess engine improving over time
- reproducible experiments
- objective benchmarks
- AI-generated hypotheses
- accepted and rejected changes
- clear engineering documentation
```

## Links

- [[implementation-roadmap]]
- [[system-architecture]]
- [[research-loop]]
- [[acceptance-rules]]

