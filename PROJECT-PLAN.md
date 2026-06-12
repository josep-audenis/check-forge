# CheckForge — AutoResearch Lab for a Deterministic Chess Engine

## 1. Project vision

**CheckForge** is an AutoResearch-style system for building and improving a purely deterministic chess engine.

The goal is not to train a neural network. The goal is to create a research loop where an AI coding agent proposes small engine changes, runs experiments, measures results, and accepts/rejects changes based on objective benchmarks.

Core philosophy:

```text
AI suggests. Benchmarks decide.
```

The chess engine must remain:

```text
- deterministic
- classical/search-based
- no neural network
- no GPU dependency
- explainable
- measurable
```

The final project should demonstrate engine evolution over time through experiment logs, Elo estimates, tactical test results, speed benchmarks, and accepted/rejected research hypotheses.

---

## 2. External standards and tools

The engine should eventually support **UCI**, the Universal Chess Interface, because UCI is a standard protocol that lets chess engines communicate with GUIs and tournament tools. ([chessprogramming.org][1])

The evaluation system should use **cutechess-cli** for automated engine-vs-engine matches. Cutechess-cli supports UCI engines and is designed for command-line automated chess engine tournaments. ([chessprogramming.org][2])

Move generation must be verified using **perft tests**, which are a standard chess-programming method for debugging legal move generation by counting leaf nodes at fixed depths. ([chessprogramming.org][3])

---

## 3. High-level architecture

```text
CheckForge/
  engine/                 # deterministic chess engine
  research/               # AutoResearch orchestration
  benchmarks/             # perft, tactical suites, speed tests
  matches/                # cutechess match configs/results
  experiments/            # experiment reports
  configs/                # engine evaluation/search configs
  data/                   # openings, test positions, PGNs
  docs/                   # documentation
  dashboard/              # optional later UI
```

The system has four main parts:

```text
1. Chess Engine
   A deterministic classical engine written in C++.

2. Benchmark Harness
   Perft tests, tactical tests, speed tests, and match tests.

3. Research Agent Interface
   Instructions and scripts that allow Claude Code/Codex to propose and test changes.

4. Experiment Memory
   Logs of hypotheses, changes, results, and accept/reject decisions.
```

---

## 4. Recommended tech stack

Use:

```text
Engine:
C++17

Research orchestration:
Python

Testing:
pytest for Python scripts
native unit tests for engine
perft test suite
cutechess-cli for matches

Storage:
Markdown files first
SQLite later

Config:
JSON or TOML

Version control:
Git

Optional dashboard:
Streamlit first
React/Next.js later
```

Initial recommendation:

```text
C++17 engine
+ Python research scripts
+ JSON configs
+ Markdown experiment logs
```

Do not start with a complex frontend. The first goal is a working research loop.

---

## 5. Development phases

## Phase 0 — Repository setup

Create the base project structure:

```text
CheckForge/
  README.md
  PROJECT_PLAN.md
  AGENT_INSTRUCTIONS.md
  engine/
  research/
  benchmarks/
  configs/
  experiments/
  data/
  docs/
```

Add a simple build system:

```text
CMake for C++
```

For C++:

```text
engine/
  CMakeLists.txt
  src/
  include/
  tests/
```

Acceptance criteria:

```text
- repo builds
- test command exists
- benchmark command exists, even if placeholder
- README explains the project
```

---

## Phase 1 — Chess board and move generation

Implement the core chess representation.

Required features:

```text
- board representation
- FEN parser
- side to move
- castling rights
- en passant square
- halfmove/fullmove counters
- legal move generation
- make move
- unmake move
- check detection
```

Recommended board representation:

```text
Start simple.
Use mailbox/array board first if needed.
Move to bitboards later if performance becomes the bottleneck.
```

Required legal moves:

```text
- quiet moves
- captures
- promotions
- castling
- en passant
- checks
- pins
```

Add perft:

```text
engine --perft "<fen>" <depth>
```

Example:

```bash
./engine --perft "startpos" 4
```

Acceptance criteria:

```text
- starting position perft is correct for depths 1–5
- tricky positions with castling, en passant, promotions pass
- move generator is trusted before search is developed
```

Important rule:

```text
Do not implement advanced search until perft is reliable.
```

---

## Phase 2 — Basic engine

Implement the first playable engine.

Features:

```text
- material evaluation
- legal move search
- minimax or negamax
- alpha-beta pruning
- fixed-depth search
- simple move ordering
```

Evaluation v1:

```text
pawn = 100
knight = 320
bishop = 330
rook = 500
queen = 900
king = 0
```

CLI commands:

```bash
./engine --bestmove "<fen>" --depth 3
./engine --eval "<fen>"
```

Acceptance criteria:

```text
- engine can choose legal moves
- engine prefers winning material
- engine avoids obvious illegal/check-losing moves
- engine can play a full game without crashing
```

---

## Phase 3 — UCI protocol

Implement basic UCI support.

Minimum required commands:

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

Acceptance criteria:

```text
- engine can be loaded by a UCI-compatible GUI/tool
- engine can be run by cutechess-cli
- engine can complete automated games
```

---

## Phase 4 — Search improvements

Add classical search features incrementally.

Priority order:

```text
1. iterative deepening
2. quiescence search
3. better move ordering
4. transposition table
5. check extensions, if useful
6. null-move pruning
7. late move reductions
8. aspiration windows
9. futility pruning
10. time management
```

Do not add everything at once. Each feature should be introduced as an experiment.

Acceptance criteria:

```text
- each search feature has before/after benchmark data
- no feature is accepted without tests
- speed and tactical accuracy are tracked
```

---

## Phase 5 — Configurable engine parameters

Expose evaluation and search parameters through config files.

Example:

```json
{
  "piece_values": {
    "pawn": 100,
    "knight": 320,
    "bishop": 330,
    "rook": 500,
    "queen": 900
  },
  "eval_weights": {
    "mobility": 10,
    "king_safety": 20,
    "passed_pawn": 25,
    "isolated_pawn_penalty": -12,
    "bishop_pair": 35,
    "rook_open_file": 20
  },
  "search_params": {
    "null_move_reduction": 2,
    "lmr_base": 1,
    "futility_margin": 120,
    "aspiration_window": 50
  }
}
```

The engine should load:

```bash
./engine --config configs/default.json
```

Acceptance criteria:

```text
- config changes affect engine behavior
- config values are validated
- invalid config fails safely
- research agent can modify configs without touching engine code
```

---

## Phase 6 — Benchmark harness

Create Python scripts for evaluating engine versions.

Scripts:

```text
research/run_perft.py
research/run_tactics.py
research/run_speed.py
research/run_match.py
research/evaluate_result.py
```

Benchmark types:

```text
1. Perft correctness
2. Tactical suite accuracy
3. Speed benchmark
4. Self-play match
5. Fixed-opponent match
```

Metrics:

```text
- perft pass/fail
- tactical accuracy
- average time per position
- nodes per second
- win/draw/loss
- estimated Elo difference
- crashes/timeouts
```

Acceptance criteria:

```text
- one command can run the full benchmark suite
- results are saved in machine-readable JSON
- failed correctness tests automatically reject the experiment
```

Example result:

```json
{
  "experiment_id": "exp_0007",
  "engine_version": "v0.3.1",
  "perft_passed": true,
  "tactical_accuracy": 0.62,
  "nodes_per_second": 450000,
  "match": {
    "games": 200,
    "wins": 72,
    "draws": 61,
    "losses": 67,
    "elo_diff": 8.7
  },
  "accepted": false,
  "reason": "Elo gain too small and tactical accuracy decreased"
}
```

---

## Phase 7 — AutoResearch loop

Create the actual research loop.

File:

```text
research/research_loop.py
```

The loop:

```text
1. Load current engine state.
2. Read previous experiments.
3. Ask AI agent for one experiment proposal.
4. Apply change.
5. Build engine.
6. Run correctness tests.
7. Run benchmarks.
8. Evaluate result.
9. Accept or reject.
10. Write experiment report.
```

At first, the loop can be semi-manual:

```text
Claude Code/Codex proposes the experiment.
Human approves.
Script runs benchmark.
Human reviews result.
```

Later, automate more.

---

## 6. Agent instructions

Create `AGENT_INSTRUCTIONS.md` with this content:

```text
You are the CheckForge research agent.

Your job is to improve a deterministic classical chess engine through small, measurable experiments.

Rules:
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

Allowed initial edit scope:
- configs/*.json
- engine/src/eval/*
- engine/src/search/*

Forbidden initial edit scope:
- research/evaluate_result.py
- benchmark expected outputs
- previous experiment reports

Experiment report format:
- Experiment ID
- Date
- Hypothesis
- Change made
- Files changed
- Expected effect
- Tests run
- Results
- Decision: accepted/rejected
- Notes
- Next suggested experiment
```

---

## 7. Experiment report template

Create:

```text
experiments/TEMPLATE.md
```

Template:

````markdown
# Experiment EXP_ID

## Hypothesis

Explain the idea being tested.

## Change

Describe exactly what changed.

## Files changed

- file 1
- file 2

## Expected effect

What should improve?

## Risks

What could get worse?

## Tests run

- Perft:
- Tactical suite:
- Speed:
- Self-play:
- Fixed opponent:

## Results

```json
{}
````

## Decision

Accepted / Rejected / Needs more testing

## Reason

Explain the decision.

## Notes

What did we learn?

## Next experiment idea

Suggest one follow-up.

````

---

## 8. Acceptance/rejection rules

Initial acceptance rules:

```text
Reject automatically if:
- engine fails to build
- any perft test fails
- engine crashes during match
- illegal move occurs
- tactical accuracy drops more than 3%
- nodes/sec drops more than 15% without clear Elo gain
````

Accept only if:

```text
- correctness tests pass
- no crashes
- performance does not regress badly
- match results are positive enough to justify keeping
```

Initial simple match rule:

```text
Accept if:
- at least +15 estimated Elo over baseline
- at least 200 games played
- tactical accuracy does not drop more than 2%
```

Later improvement:

```text
Use SPRT-style testing or stronger confidence intervals.
```

---

## 9. First concrete MVP milestone

The first MVP is **not** a strong chess engine.

The first MVP is:

```text
A weak but legal chess engine that can be automatically tested.
```

MVP requirements:

```text
- parses FEN
- generates legal moves
- passes basic perft tests
- searches with alpha-beta
- evaluates material
- speaks minimal UCI
- can play cutechess-cli games
- has one configurable JSON parameter file
- has one experiment report
```

Example first AutoResearch experiment:

```text
Hypothesis:
The engine undervalues bishops compared to knights.

Change:
bishop value 330 → 340

Test:
200 games against previous version using fixed openings.

Decision:
Accept/reject based on result.
```

---

## 10. Suggested repository commands

Use these commands eventually:

```bash
# Build engine
make build

# Run unit tests
make test

# Run perft tests
make perft

# Run tactical benchmark
make tactics

# Run speed benchmark
make speed

# Run match against previous version
make match

# Run full benchmark suite
make benchmark

# Create new experiment
python research/new_experiment.py

# Evaluate experiment
python research/evaluate_result.py results/latest.json
```

---

## 11. Project roadmap

## Milestone 1 — Legal engine

```text
- board representation
- FEN parser
- legal move generation
- perft
```

Target:

```text
Correctness, not strength.
```

## Milestone 2 — Basic playable engine

```text
- material eval
- alpha-beta
- bestmove command
```

Target:

```text
Can play legal games.
```

## Milestone 3 — UCI + cutechess

```text
- UCI support
- automated matches
```

Target:

```text
Can be evaluated automatically.
```

## Milestone 4 — First research loop

```text
- config file
- experiment template
- benchmark scripts
- first accepted/rejected experiment
```

Target:

```text
AutoResearch loop exists.
```

## Milestone 5 — Stronger classical engine

```text
- quiescence
- iterative deepening
- transposition table
- move ordering
```

Target:

```text
Reach competent hobby-engine strength.
```

## Milestone 6 — Research dashboard

```text
- experiment history
- Elo graph
- tactical accuracy graph
- speed graph
```

Target:

```text
Project becomes visually impressive.
```

---

## 12. What not to do

Avoid:

```text
- adding neural networks
- adding GPU dependencies
- rewriting everything every experiment
- accepting changes without matches
- optimizing only for one test suite
- letting the agent modify benchmark expected outputs
- building a frontend before the engine works
- chasing Stockfish-level strength early
```

The goal is disciplined research, not chaos.

---

## 13. Definition of success

This project succeeds if it shows:

```text
- a deterministic chess engine improving over time
- reproducible experiments
- objective benchmarks
- AI-generated hypotheses
- accepted and rejected changes
- clear engineering documentation
```

The final portfolio description:

```text
CheckForge is an AutoResearch lab for deterministic chess engines.
An AI coding agent proposes engine changes, runs controlled experiments,
and accepts or rejects modifications using perft correctness tests,
tactical benchmarks, speed metrics, and engine-vs-engine matches.
```

---

## 14. First task for Claude Code/Codex

Start with this:

```text
Task:
Create the initial repository structure for CheckForge.

Requirements:
1. Create README.md explaining the project.
2. Create AGENT_INSTRUCTIONS.md.
3. Create engine/ with a minimal C++ or skeleton.
4. Create research/ with placeholder benchmark scripts.
5. Create experiments/TEMPLATE.md.
6. Create configs/default.json.
7. Add a Makefile or equivalent command runner.
8. Do not implement full chess yet.
9. Make sure the project builds/runs a placeholder command.
10. Keep the architecture simple and extensible.
```

Then next task:

```text
Implement FEN parsing and board representation.
Add tests.
Do not implement search yet.
```

Then:

```text
Implement legal move generation and perft.
Do not proceed to engine search until perft passes.
```

That’s the right order.

[1]: https://www.chessprogramming.org/UCI?utm_source=chatgpt.com "UCI"
[2]: https://www.chessprogramming.org/Cutechess-cli?utm_source=chatgpt.com "Cutechess-cli"
[3]: https://www.chessprogramming.org/Perft?utm_source=chatgpt.com "Perft"
