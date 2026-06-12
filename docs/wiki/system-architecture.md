# System Architecture

CheckForge has four core parts:

```text
1. Chess Engine
2. Benchmark Harness
3. Research Agent Interface
4. Experiment Memory
```

Dashboard is optional and should read experiment memory after data exists.

## Repository Shape

```text
CheckForge/
  engine/                 C++17 deterministic chess engine
  research/               Python orchestration and benchmark scripts
  benchmarks/             perft, tactics, speed, match suites
  matches/                cutechess configs and match outputs
  configs/                JSON engine/search/eval parameters
  experiments/            Markdown experiment reports
  results/                machine-readable benchmark output
  data/                   openings, FENs, PGNs, tactical positions
  docs/wiki/              LLM-maintained project wiki
  dashboard/              optional UI, added after data exists
```

Current Phase 0 command runner:

```text
task.ps1                  PowerShell build/test/benchmark runner
Makefile                  Make runner for environments with make installed
```

## Engine

C++17 deterministic classical engine.

Early board representation should be simple. Mailbox or array board is acceptable. Bitboards can come later if performance data proves need.

Do not add neural network, GPU dependency, or non-deterministic search behavior.

Current board core:

```text
- 64-square array indexed from a8 to h1
- FEN parser accepts "startpos" alias
- FEN serializer round-trips normalized FEN
- stores side to move, castling rights, en passant square, halfmove clock, fullmove number
```

Current CLI:

```bash
checkforge --version
checkforge --fen "<fen|startpos>"
checkforge --moves "<fen|startpos>"
checkforge --perft "<fen|startpos>" <depth>
checkforge --eval "<fen|startpos>"
checkforge --bestmove "<fen|startpos>" --depth <n>
checkforge uci
```

Current move generation:

```text
- pseudo-legal generation by piece
- legal filtering by make-on-copy and king safety
- castling legality checks
- en passant capture handling
- promotion moves to queen, rook, bishop, knight
- recursive perft
```

Current search:

```text
- material-only evaluation
- negamax
- alpha-beta pruning
- fixed-depth search
- simple capture/promotion-first move ordering
- checkmate and stalemate terminal handling
```

Current UCI:

```text
- uci
- isready
- ucinewgame
- position startpos [moves ...]
- position fen <six FEN fields> [moves ...]
- go depth N
- go movetime X
- stop
- quit
```

## Benchmarks

Benchmark harness should include:

```text
- perft correctness
- tactical suite accuracy
- speed benchmark
- self-play match
- fixed-opponent match
```

Correctness gates strength experiments. If perft fails, experiment fails.

## Research Agent Interface

Agent proposes exactly one experiment at a time. Prefer config change before C++ code change.

Initial allowed edit scope:

```text
- configs/*.json
- engine/src/eval/*
- engine/src/search/*
```

Initial forbidden edit scope:

```text
- research/evaluate_result.py
- benchmark expected outputs
- previous experiment reports
```

## Experiment Memory

Experiment memory has two forms:

```text
- experiments/*.md for human-readable reports
- results/*.json for machine-readable metrics
```

Wiki pages summarize current state. Experiment reports remain historical record.

## Links

- [[data-contracts]]
- [[research-loop]]
- [[dashboard-strategy]]
