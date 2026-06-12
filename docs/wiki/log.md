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
