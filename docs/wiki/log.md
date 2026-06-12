# CheckForge Wiki Log

Append-only record of wiki ingests, queries, lint passes, and major maintenance changes.

## [2026-06-12] ingest | PROJECT-PLA.md

Created initial project wiki from project plan. Extracted roadmap, architecture, acceptance rules, dashboard timing, and research loop.

Touched:

- [[overview]]
- [[implementation-roadmap]]
- [[system-architecture]]
- [[research-loop]]
- [[acceptance-rules]]
- [[dashboard-strategy]]
- [[data-contracts]]
- [[experiment-template]]
- [[source-project-plan]]

## [2026-06-12] ingest | llm-wiki.md

Reworked docs into Karpathy-style LLM wiki: indexed notes, source summaries, append-only log, schema/maintenance rules, and interlinked pages.

Touched:

- [[index]]
- [[agent-maintenance]]
- [[source-llm-wiki-pattern]]

## [2026-06-12] implementation | Phase 0 scaffold

Created initial scaffold: CMake C++17 placeholder engine, smoke test, PowerShell task runner, Makefile, benchmark placeholder scripts, default config, experiment template, and required project directories.

Verified:

```text
powershell -ExecutionPolicy Bypass -File task.ps1 build
powershell -ExecutionPolicy Bypass -File task.ps1 test
powershell -ExecutionPolicy Bypass -File task.ps1 benchmark
```

Touched:

- [[implementation-roadmap]]
- [[system-architecture]]
- [[data-contracts]]

## [2026-06-12] docs | Linux command documentation

Added Linux/macOS `make` command labels alongside Windows PowerShell commands.

Touched:

- [[implementation-roadmap]]

## [2026-06-12] implementation | Phase 1 board and FEN core

Implemented initial C++ board representation and FEN parser/serializer. Added tests for `startpos`, custom FEN round-trip, invalid FEN rejection, side to move, castling rights, en passant square, halfmove clock, and fullmove number. Added `checkforge --fen "<fen|startpos>"` CLI helper and FEN validation for placeholder `--perft`.

Verified:

```text
powershell -ExecutionPolicy Bypass -File task.ps1 test
powershell -ExecutionPolicy Bypass -File task.ps1 benchmark
build\engine\checkforge.exe --fen startpos
```

Touched:

- [[implementation-roadmap]]
- [[system-architecture]]

## [2026-06-12] implementation | Phase 2 legal movegen and perft

Implemented legal move generation and recursive perft. Added move representation, make-on-copy move application, king safety filtering, castling, en passant, promotions, `checkforge --moves`, and real `checkforge --perft` node counts. Upgraded `research/run_perft.py` from placeholder to correctness gate.

Verified:

```text
powershell -ExecutionPolicy Bypass -File task.ps1 test
powershell -ExecutionPolicy Bypass -File task.ps1 benchmark
build\engine\checkforge.exe --perft startpos 5
```

Results:

```text
startpos depth 1-5 passed
Kiwipete depth 1-2 passed
```

Touched:

- [[implementation-roadmap]]
- [[system-architecture]]
- [[data-contracts]]

## [2026-06-12] implementation | Phase 3 weak playable engine

Implemented material evaluation and fixed-depth negamax alpha-beta search. Added capture/promotion-first move ordering, terminal checkmate/stalemate scoring, `checkforge --eval`, and `checkforge --bestmove "<fen|startpos>" --depth <n>`.

Verified:

```text
powershell -ExecutionPolicy Bypass -File task.ps1 test
powershell -ExecutionPolicy Bypass -File task.ps1 benchmark
build\engine\checkforge.exe --eval "4k3/8/8/8/8/8/8/4KQ2 w - - 0 1"
build\engine\checkforge.exe --bestmove "4k3/8/8/8/4q3/8/4R3/4K3 w - - 0 1" --depth 1
```

Results:

```text
material eval returned 900 for white queen advantage
bestmove returned e2e4 to capture free queen
full-game smoke passed
perft benchmark remained green
```

Touched:

- [[implementation-roadmap]]
- [[system-architecture]]

## [2026-06-12] implementation | Phase 4 minimal UCI

Implemented minimal UCI protocol loop with `checkforge uci`. Added UCI session parser for `uci`, `isready`, `ucinewgame`, `position startpos`, `position fen`, move-list application, `go depth`, `go movetime`, `stop`, and `quit`.

Verified:

```text
powershell -ExecutionPolicy Bypass -File task.ps1 test
powershell -ExecutionPolicy Bypass -File task.ps1 benchmark
uci/isready/position/go/quit subprocess smoke
position fen free-queen bestmove subprocess smoke
```

Results:

```text
UCI handshake returns id name, id author, uciok, readyok
go depth returns bestmove
perft benchmark remains green
```

Touched:

- [[implementation-roadmap]]
- [[system-architecture]]

## [2026-06-12] autoresearch | exp001 quiescence

Implemented bounded capture/promotion quiescence at search leaves with configurable `quiescence_depth`.

Verified:

```text
powershell -ExecutionPolicy Bypass -File task.ps1 test
python research/run_benchmark.py --engine build/engine/checkforge.exe --opponent-engine versions/v000-phase4-baseline/checkforge.exe --opponent-config versions/v000-phase4-baseline/default.json --experiment-id exp001-quiescence --output results/exp001-quiescence.json
python research/run_cutechess.py --engine build/engine/checkforge.exe --opponent-engine versions/v000-phase4-baseline/checkforge.exe --opponent-config versions/v000-phase4-baseline/default.json --games 40 --tc 2+0.1 --output results/exp001-quiescence-cutechess.json --pgn matches/exp001-quiescence-vs-v000.pgn
```

Results:

```text
benchmark accepted=true
cutechess passed=true
score vs v000: 0 - 0 - 40 [0.500]
decision: accepted as infrastructure; no Elo gain detected
```

## [2026-06-12] autoresearch | exp002 positional eval

Added static search eval with piece-square and development bonuses.

Verified:

```text
powershell -ExecutionPolicy Bypass -File task.ps1 test
python research/run_benchmark.py --engine build/engine/checkforge.exe --opponent-engine versions/v001-quiescence/checkforge.exe --opponent-config versions/v001-quiescence/default.json --experiment-id exp002-positional-eval --output results/exp002-positional-eval.json
python research/run_cutechess.py --engine build/engine/checkforge.exe --opponent-engine versions/v001-quiescence/checkforge.exe --opponent-config versions/v001-quiescence/default.json --games 60 --tc 2+0.1 --output results/exp002-positional-eval-cutechess.json --pgn matches/exp002-positional-eval-vs-v001.pgn
```

Results:

```text
benchmark accepted=true
cutechess passed=true
score vs v001: 0 - 0 - 60 [0.500]
decision: accepted; improves opening choices but still repeats
weak point: immediate move reversal / threefold repetition
```

## [2026-06-12] autoresearch | exp003 avoid reversal

Added UCI history-aware root fallback to avoid immediate reversal of previous own move.

Results:

```text
benchmark accepted=true
fast cutechess exposed time-control weakness
score vs v002 at 1+0.05: 20 - 20 - 0, all games lost by White on time
decision: needs follow-up, kept as current candidate after exp004 rejected
```

## [2026-06-12] autoresearch | exp004 time management

Tested shallow depth cap for UCI time controls.

Results:

```text
benchmark accepted=true
cutechess score vs v002: 0 - 60 - 0
failure: lost every game by mate
decision: rejected and reverted
saved rejected binary: versions/v004-rejected-time-management
```

## [2026-06-12] autoresearch | exp005 check extension

Added one-ply extension when a leaf node is in check.

Results:

```text
benchmark accepted=true
cutechess score vs v002: 0 - 0 - 20 [0.500]
decision: accepted as safe search infrastructure; no Elo gain detected
saved version: versions/v005-check-extension
```
