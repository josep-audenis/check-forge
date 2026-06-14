# CheckForge — Agent Entry Point

CheckForge is an **AutoResearch lab for a deterministic, classical (non-NN) chess
engine**: an AI agent proposes one small engine change at a time, measures it with
objective benchmarks, and accepts or rejects it. `AI suggests. Benchmarks decide.`

If you are an agent continuing this project, **read in this order before doing anything**:

1. This file (current state + the rules that changed).
2. `AGENT_INSTRUCTIONS.md` — the operating manual for the research loop.
3. `docs/wiki/index.md` → then `docs/wiki/roadmap-to-2000.md`, `docs/wiki/acceptance-rules.md`,
   `docs/wiki/research-loop.md`, `docs/wiki/agent-maintenance.md`.
4. `docs/wiki/log.md` (tail) — what the last sessions did.

Do **not** start from scratch. There is a working engine and 21 experiments of history.

## Current state (2026-06-15)

- **Head version: `versions/v014-null-move`** (latest accepted). Each
  `versions/vNNN-*/` holds the frozen `checkforge.exe`, `default.json`, and its match
  results. The live source builds the head.
- History: experiments `exp001`–`exp021` in `experiments/`; per-version match data in
  `versions/`, `results/`, `matches/`.
- Engine has: FEN/board, legal movegen + perft, material + crude piece-square eval,
  quiescence, negamax alpha-beta, MVV-LVA ordering, check extension, **iterative
  deepening + time management (v008)**, **transposition table (v009)**, **TT-move
  ordering (v010)**, **pawn-structure eval (doubled/isolated/passed, v013)**,
  **null-move pruning (v014)**, minimal UCI.
- **Absolute Elo ≈ 1770–1785 (estimate).** Anchor = Stockfish 18 pinned via
  `UCI_LimitStrength`/`UCI_Elo` (avx2, winget); measure with `research/run_anchor.py`.
  Internal ladder: v010 ≈1581 → v011 (+117, -O3) ≈1714 → v012 neutral → v013 (+51, pawn
  structure) → v014 (+20, null-move, 400 games). **Trust the internal version-vs-version ladder for deltas, NOT the SF
  anchor**: at 200 games / bullet TC the anchor has ±47 noise and `UCI_Elo` is
  miscalibrated/saturates (exp018: same engine gave 1684 vs SF1700 and 1937 vs SF1800).
  Treat the anchor as a coarse band only. See `docs/wiki/roadmap-to-2000.md`.
- **The build defaults to Release (-O3) since exp016.** It had been compiling at -O0;
  fixing that alone was +117 Elo. Always build optimized.

## The approach changed — read this

Earlier sessions tried many small eval/search tweaks. With the metric finally working
(varied openings), the lesson was: **at the shallow depth (~3-4) this engine reaches,
micro-tweaks are statistical noise.** The path to real strength (~2000 Elo target) is
**big structural work FIRST, fine-tuning LAST**, in this order:

1. **Elo anchor** — add a known-rated reference opponent (e.g. Stockfish with
   `UCI_LimitStrength`/skill/depth pinned, or a CCRL-rated weak engine) so every result
   is in real Elo. Prerequisite for measuring all later work. **Do this first.**
2. **Faster move generation** — replace make-on-copy with bitboards / make-unmake.
   Nodes/sec → depth → the single biggest strength lever.
3. **Real evaluation** — king safety, pawn structure, mobility, tuned piece-square
   tables.
4. **Search pruning** — null-move, late move reductions, aspiration windows, PVS.
5. **Only then: parameter fine-tuning** (config/SPSA-style) on top of real structure.

Full rationale and the bullet-ceiling evidence: `docs/wiki/roadmap-to-2000.md`.

## Testing discipline (this changed too)

- **Strength claims require large samples: 200+ games, or SPRT.** Small matches
  (≤ ~40 games) are **screening only** — they catch disasters (flags, crashes, illegal
  moves, large regressions) but have ±70–120 Elo error and **cannot** confirm a
  +15–30 Elo change. Never report a single-digit Elo delta from < 200 games as a gain.
- `research/run_cutechess.py` now defaults to `--games 200` and uses varied openings
  (`data/openings.epd`). For sequential testing add cutechess
  `-sprt elo0=0 elo1=10 alpha=0.05 beta=0.05` (not yet wired into the script).
- Correctness gates (perft, tactics 8/8, no illegal moves, no flags) are mandatory and
  unchanged.

## Build & run (commands that actually work here)

This is Windows + msys2/ucrt (ninja, g++). **Do not rely on
`powershell -ExecutionPolicy Bypass -File task.ps1 ...`** — the sandbox classifier
blocks `-ExecutionPolicy Bypass`. Call the tools directly:

```powershell
cmake -S . -B build            # configure
cmake --build build            # build -> build/engine/checkforge.exe
ctest --test-dir build --output-on-failure   # unit tests

# correctness gates
python research/run_perft.py   --engine build/engine/checkforge.exe
python research/run_tactics.py --engine build/engine/checkforge.exe   # expect 8/8

# full benchmark vs current head (correctness + internal match)
python research/run_benchmark.py --engine build/engine/checkforge.exe `
  --opponent-engine versions/v014-null-move/checkforge.exe `
  --opponent-config versions/v014-null-move/default.json `
  --experiment-id exp022-<slug> --output results/exp022-<slug>.json

# verification match (200 games, varied openings)
python research/run_cutechess.py --engine build/engine/checkforge.exe `
  --opponent-engine versions/v014-null-move/checkforge.exe `
  --opponent-config versions/v014-null-move/default.json `
  --tc 8+0.08 --output results/exp022-<slug>-cutechess.json `
  --pgn matches/exp022-<slug>.pgn

# absolute Elo vs the anchor (Stockfish auto-detected; set --anchor-elo near expected
# level so the match scores ~50% for tightest error bars)
python research/run_anchor.py --engine build/engine/checkforge.exe `
  --anchor-elo 1700 --games 200 --tc 8+0.08 `
  --output results/exp022-<slug>-anchor.json --pgn matches/exp022-<slug>-anchor.pgn
```

Notes: the engine ignores the clock only for `go depth N` (fixed depth, used by
tests); real games send `wtime/btime` and use iterative deepening. `<chrono>` does not
compile on this toolchain (missing `features.h`) — timing uses `GetTickCount64`.

## When you finish an accepted experiment

1. Write `experiments/expNNN-<slug>.md` (see `experiments/TEMPLATE.md`).
2. Snapshot `versions/vNNN-<slug>/` = `checkforge.exe` + `default.json` +
   `benchmark-result.json` + `cutechess-result.json` + the `.pgn`.
3. Append `docs/wiki/log.md` (`## [YYYY-MM-DD] autoresearch | expNNN <title>`).
4. Update any wiki page whose subject changed (commands, schema, roadmap, rules).

Next experiment id is **exp022**; next version is **v015**. (exp015 = Elo anchor, infra.
exp016 = Release build → v011, +117 Elo. exp017 = movegen king-cache → v012, infra/neutral.
exp018 = pawn-structure eval → v013, +51 Elo. exp019 = king-safety pawn-shield → REJECTED,
strength-neutral, head stays v013. exp020 = PST swap → REJECTED, neutral. exp021 = null-move pruning → v014, +20 Elo.)
