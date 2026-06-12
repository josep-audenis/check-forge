# Implementation Roadmap

Build correctness first, research loop second, strength later, dashboard last.

## Phase 0: Repository Scaffold

Goal: project can build and run placeholder commands.

Create:

```text
README.md
AGENT_INSTRUCTIONS.md
Makefile
engine/CMakeLists.txt
engine/src/
engine/include/
engine/tests/
research/
benchmarks/
configs/default.json
experiments/TEMPLATE.md
docs/wiki/
```

Linux/macOS commands:

```bash
make build
make test
make perft
make tactics
make speed
make match
make benchmark
```

Windows commands:

```powershell
powershell -ExecutionPolicy Bypass -File task.ps1 build
powershell -ExecutionPolicy Bypass -File task.ps1 test
powershell -ExecutionPolicy Bypass -File task.ps1 benchmark
```

Acceptance:

```text
- repo builds
- test command exists
- benchmark command exists
- placeholder engine command runs
- README links to wiki index
```

Current status:

```text
Done. Phase 0 scaffold exists and placeholder commands pass.
```

## Phase 1: Board Core

Goal: trusted position representation.

Implement:

```text
- board representation
- FEN parser
- side to move
- castling rights
- en passant square
- halfmove clock
- fullmove number
```

Tests:

```text
- startpos parses
- custom FEN parses
- invalid FEN rejects
- board state round-trips
```

Do not implement search here.

Current status:

```text
Done. Board state stores pieces, side to move, castling rights, en passant square, halfmove clock, and fullmove number. FEN parser and serializer are covered by tests.
```

## Phase 2: Legal Move Generation And Perft

Goal: legal chess first.

Implement:

```text
- pseudo-legal move generation
- make move
- unmake move
- attack detection
- check detection
- legal move filtering
- castling
- en passant
- promotions
- perft command
```

CLI:

```bash
./engine --perft "startpos" 4
```

Acceptance:

```text
- start position perft passes depths 1-5
- tricky castling/en-passant/promotion positions pass
- search work waits until perft is reliable
```

Current status:

```text
Done for initial legal movegen. Start position perft passes depths 1-5. Kiwipete passes depths 1-2. Move generator covers quiet moves, captures, promotions, castling, en passant, check filtering, and recursive perft.
```

## Phase 3: Weak Playable Engine

Goal: legal move choice, not strength.

Implement:

```text
- material evaluation
- negamax
- alpha-beta pruning
- fixed-depth search
- simple move ordering
```

CLI:

```bash
./engine --eval "<fen>"
./engine --bestmove "<fen>" --depth 3
```

Acceptance:

```text
- engine returns legal bestmove
- engine prefers free material
- engine can play full game without crashing
```

Current status:

```text
Done. Engine has material evaluation, negamax alpha-beta search, capture/promotion-first move ordering, --eval, and --bestmove. Tests cover legal bestmove, free queen capture, and full-game smoke.
```

## Phase 4: UCI

Goal: connect to standard chess tools.

Minimum UCI:

```text
uci
isready
ucinewgame
position startpos
position fen ...
go depth N
go movetime X
stop
quit
```

Minimum output:

```text
id name CheckForge
id author Josep Audenis
uciok
readyok
bestmove <move>
```

Acceptance:

```text
- engine loads in UCI-compatible tools
- cutechess-cli can run games
- no illegal moves in automated games
```

Current status:

```text
Done for minimal UCI. Engine supports uci, isready, ucinewgame, position startpos, position fen, moves, go depth, go movetime, stop, and quit. Cutechess validation remains next external-tool check.
```

## Phase 5: Configurable Parameters

Goal: research agent can test many ideas without touching C++.

CLI:

```bash
./engine --config configs/default.json
```

Acceptance:

```text
- valid config changes engine behavior
- invalid config fails safely
- benchmark scripts record config used
```

Current status:

```text
Done for initial piece values and default depth. Engine accepts --config <path>; eval, search move ordering, CLI, and UCI use config. Invalid config fails safely.
```

## Phase 6: Benchmark Harness

Goal: one repeatable command evaluates engine changes.

Scripts:

```text
research/run_perft.py
research/run_tactics.py
research/run_speed.py
research/run_match.py
research/evaluate_result.py
```

Output:

```text
results/<experiment_id>.json
```

Acceptance:

```text
- one command runs full suite
- JSON result saved
- correctness failure rejects experiment automatically
```

Current status:

```text
Done for initial pre-autoresearch gate. run_benchmark.py writes aggregate JSON, perft/tactics/speed/match step JSON, and accepted/rejected decision. Internal UCI match runner supports engine-vs-engine and config-vs-config smoke games.
```

## Phase 7: Research Loop

Goal: controlled engine evolution.

Start semi-manual. Human approves proposals. Scripts run benchmarks. Human reviews decisions.

See [[research-loop]].

## Phase 8: Dashboard

Goal: visualize experiment history after real data exists.

See [[dashboard-strategy]].

## Current Milestones

```text
M1 Legal engine:
  board, FEN, legal movegen, perft

M2 Basic playable engine:
  material eval, alpha-beta, bestmove

M3 UCI + cutechess:
  UCI protocol, automated games

M4 Research loop:
  configs, benchmark JSON, experiment reports

M5 Stronger classical engine:
  quiescence, iterative deepening, transposition table, move ordering

M6 Dashboard:
  experiment history, charts, portfolio view
```
