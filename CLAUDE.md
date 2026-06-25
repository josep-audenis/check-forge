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

Do **not** start from scratch. There is a working engine and 37 experiments of history.

## Current state (2026-06-25)

- **Head version: `versions/v022-magic-bitboards`** (latest accepted). Each
  `versions/vNNN-*/` holds the frozen `checkforge.exe`, `default.json`, and its match
  results. The live source builds the head.
- History: experiments `exp001`–`exp037` in `experiments/`; per-version match data in
  `versions/`, `results/`, `matches/`.
- Engine has: FEN/board, legal movegen + perft, material + crude piece-square eval,
  quiescence, negamax alpha-beta, MVV-LVA ordering, check extension, **iterative
  deepening + time management (v008)**, **transposition table (v009)**, **TT-move
  ordering (v010)**, **pawn-structure eval (doubled/isolated/passed, v013)**,
  **null-move pruning (v014)**, **late move reductions (v015)**,
  **killer + history move ordering (v016)**, **make/unmake search (v017, infra)**,
  **incremental Zobrist hashing (v018, infra)**, **aspiration windows (v019)**,
  **bitboard movegen + attack detection (v020, infra)**, **bitboard mobility eval (v021)**,
  **magic bitboards / O(1) sliders (v022)**, minimal UCI.
- **Absolute Elo ≈ 1950–2050 (best estimate, ~at 2000).** SF anchor re-measured v022 at
  **≈1935 ±25** (vs SF UCI_Elo=2000, 71-108-21, bullet 8+0.08) — ~200 below the raw
  internal-ladder sum (~2150). The **self-play ladder overstates absolute Elo** (deltas
  compound; beating a weaker prior self by X doesn't fully transfer to the field), and SF
  `UCI_Elo` likely plays above nominal at bullet (deflating our reading). **Use the
  internal ladder for per-experiment DELTAS only; treat absolute as ~2000.** Anchor =
  Stockfish 18 via `UCI_LimitStrength`/`UCI_Elo` (avx2, winget), `research/run_anchor.py`.
  Internal ladder (deltas, verified 200-400g each): v010 → v011 (+117, -O3) → v012 neutral
  → v013 (+51, pawn structure) → v014 (+20, null-move) → v015 (+48, LMR) →
  v016 (+110, killers+history) → v017/v018 neutral infra → v019 (+29, aspiration) →
  v020 neutral infra (bitboards) → v021 (+96, bitboard mobility) → v022 (+98, magic sliders).
  **Anchor caveat**: at 200g/bullet ±25-47 noise, `UCI_Elo` miscalibrated (exp018: same
  engine read 1684 vs SF1700 and 1937 vs SF1800). Coarse band only. See `docs/wiki/roadmap-to-2000.md`.
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
  --opponent-engine versions/v022-magic-bitboards/checkforge.exe `
  --opponent-config versions/v022-magic-bitboards/default.json `
  --experiment-id exp038-<slug> --output results/exp038-<slug>.json

# verification match (200 games, varied openings)
python research/run_cutechess.py --engine build/engine/checkforge.exe `
  --opponent-engine versions/v022-magic-bitboards/checkforge.exe `
  --opponent-config versions/v022-magic-bitboards/default.json `
  --tc 8+0.08 --output results/exp038-<slug>-cutechess.json `
  --pgn matches/exp038-<slug>.pgn

# absolute Elo vs the anchor (Stockfish auto-detected; set --anchor-elo near expected
# level so the match scores ~50% for tightest error bars)
python research/run_anchor.py --engine build/engine/checkforge.exe `
  --anchor-elo 1700 --games 200 --tc 8+0.08 `
  --output results/exp038-<slug>-anchor.json --pgn matches/exp038-<slug>-anchor.pgn
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

Next experiment id is **exp038**; next version is **v023**. (exp015 = Elo anchor, infra.
exp016 = Release build → v011, +117 Elo. exp017 = movegen king-cache → v012, infra/neutral.
exp018 = pawn-structure eval → v013, +51 Elo. exp019 = king-safety pawn-shield → REJECTED,
strength-neutral, head stays v013. exp020 = PST swap → REJECTED, neutral. exp021 = null-move pruning → v014, +20 Elo. exp022 = LMR → v015, +48 Elo. exp023 = PVS → REJECTED, -44 Elo (ordering too weak). exp024 = killers+history ordering → v016, +110 Elo. exp025 = PVS retry → REJECTED again, -44. exp026 = make/unmake → v017, infra/neutral. exp027 = incremental Zobrist → v018, infra/neutral (hashing also NOT the bottleneck; node cost = movegen + is_square_attacked ray scans + eval). nps lever left = bitboards; else gain via pruning/eval/ordering. exp028 = aspiration windows → v019, +29 Elo (400g). exp029 = mobility eval → REJECTED, neutral (1.66x slower, ate gain; needs bitboards). exp030 = scaled LMR → REJECTED (600g +10.4, variance; use 400-600g for tuning). exp031 = bitboard movegen+attacks → v020, infra/neutral (~20% faster movegen but eval scan dominates per-leaf; bb layer now enables CHEAP eval). exp032 = bitboard mobility eval → v021, +96 Elo (400g, LOS~100%) — biggest eval gain, ~cracks 2000 (est ~2050-2070); same term exp029 rejected at +8.7 on shallow v013 (re-test rejected eval terms after search deepens). exp033 = bitboard king-safety (attacker count) → REJECTED, -60 (slider ray-loops per leaf ON TOP of mobility = depth loss + crude signal). LESSON: magic bitboards (O(1) sliders) MUST precede more per-leaf eval. exp034 = magic bitboards (O(1) sliders) → v022, +98 Elo (400g, LOS~100%) — recovers mobility cost; bitboard arc compounding. Est ~2150-2170. exp035 = king-safety retry → REJECTED again, -56 (term itself harms play, NOT cost; failed 3x exp019/033/035 — stop hand-set king-safety). exp036 = SPSA harness + mobility tuning → no gain (weights already optimal {4,4,2,1}); harness shipped (research/run_spsa.py, config-only, checkpoint-resumable). Next SPSA targets: pawn-structure weights, piece values; or SEE quiescence pruning / tapered eval.)
