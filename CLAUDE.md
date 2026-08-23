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

Do **not** start from scratch. There is a working engine and 39 experiments of history.

## Current state (2026-07-09)

- **Head version: `versions/v024-tapered-material`** (latest accepted). Each
  `versions/vNNN-*/` holds the frozen `checkforge.exe`, `default.json`, and its match
  results. The live source builds the head.
- History: experiments `exp001`–`exp039` in `experiments/`; per-version match data in
  `versions/`, `results/`, `matches/`.
- Engine has: FEN/board, legal movegen + perft, material + crude piece-square eval,
  quiescence, negamax alpha-beta, MVV-LVA ordering, check extension, **iterative
  deepening + time management (v008)**, **transposition table (v009)**, **TT-move
  ordering (v010)**, **pawn-structure eval (doubled/isolated/passed, v013)**,
  **null-move pruning (v014)**, **late move reductions (v015)**,
  **killer + history move ordering (v016)**, **make/unmake search (v017, infra)**,
  **incremental Zobrist hashing (v018, infra)**, **aspiration windows (v019)**,
  **bitboard movegen + attack detection (v020, infra)**, **bitboard mobility eval (v021)**,
  **magic bitboards / O(1) sliders (v022)**, **tapered eval / mg-eg PST (v023, +110)**, **tapered material (v024, +34)**, minimal UCI.
- **Absolute Elo remains unverified.** v024 vs SF UCI_Elo=2000 scored 93-83-24,
  diagnostic estimate ≈2017 with paired 95% CI ≈1973–2062, but measurement v2 rejects
  that run because Stockfish had 5 time forfeits (up from v022's ≈1935 before the two tapered
  eval wins). The +144 internal since v022 (exp038 +110, exp039 +34) transferred to +82 on
  the anchor (~0.57×) — the self-play ladder overstates absolute Elo. The **self-play ladder overstates absolute Elo** (deltas
  compound; beating a weaker prior self by X doesn't fully transfer to the field), and SF
  `UCI_Elo` likely plays above nominal at bullet (deflating our reading). **Use the
  internal ladder for per-experiment DELTAS only; treat ~2000 as an unverified diagnostic.** Anchor =
  Stockfish 18 via `UCI_LimitStrength`/`UCI_Elo` (avx2, winget), `research/run_anchor.py`.
  Internal ladder (deltas, verified 200-400g each): v010 → v011 (+117, -O3) → v012 neutral
  → v013 (+51, pawn structure) → v014 (+20, null-move) → v015 (+48, LMR) →
  v016 (+110, killers+history) → v017/v018 neutral infra → v019 (+29, aspiration) →
  v020 neutral infra (bitboards) → v021 (+96, bitboard mobility) → v022 (+98, magic sliders) → v023 (+110, tapered eval) → v024 (+34, tapered material).
  **Anchor caveat**: old `±25` was one SE; paired 95% half-width is ≈45. At 200g/bullet,
  `UCI_Elo` is also miscalibrated (exp018: same
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

- **Strength claims require large samples or paired sequential evidence.** Small matches
  (≤ ~40 games) are **screening only** — they catch disasters (flags, crashes, illegal
  moves, large regressions) but have ±70–120 Elo error and **cannot** confirm a
  +15–30 Elo change. Never report a single-digit Elo delta from < 200 games as a gain.
- `research/run_cutechess.py` defaults to `--games 200` and uses varied openings.
  `--sprt-*` bounds invoke harness pair-level anytime-valid evidence; Cute Chess's
  game-level trinomial SPRT is intentionally not used with correlated colour pairs.
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
  --opponent-engine versions/v024-tapered-material/checkforge.exe `
  --opponent-config versions/v024-tapered-material/default.json `
  --experiment-id exp040-<slug> --output results/exp040-<slug>.json

# verification match (200 games, varied openings)
python research/run_cutechess.py --engine build/engine/checkforge.exe `
  --opponent-engine versions/v024-tapered-material/checkforge.exe `
  --opponent-config versions/v024-tapered-material/default.json `
  --tc 8+0.08 --output results/exp040-<slug>-cutechess.json `
  --pgn matches/exp040-<slug>.pgn

# absolute Elo vs the anchor (Stockfish auto-detected; set --anchor-elo near expected
# level so the match scores ~50% for tightest error bars)
python research/run_anchor.py --engine build/engine/checkforge.exe `
  --anchor-elo 1700 --games 200 --tc 8+0.08 `
  --output results/exp040-<slug>-anchor.json --pgn matches/exp040-<slug>-anchor.pgn
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

Next experiment id is **exp040**; next version is **v025**. (exp015 = Elo anchor, infra.
exp016 = Release build → v011, +117 Elo. exp017 = movegen king-cache → v012, infra/neutral.
exp018 = pawn-structure eval → v013, +51 Elo. exp019 = king-safety pawn-shield → REJECTED,
strength-neutral, head stays v013. exp020 = PST swap → REJECTED, neutral. exp021 = null-move pruning → v014, +20 Elo. exp022 = LMR → v015, +48 Elo. exp023 = PVS → REJECTED, -44 Elo (ordering too weak). exp024 = killers+history ordering → v016, +110 Elo. exp025 = PVS retry → REJECTED again, -44. exp026 = make/unmake → v017, infra/neutral. exp027 = incremental Zobrist → v018, infra/neutral (hashing also NOT the bottleneck; node cost = movegen + is_square_attacked ray scans + eval). nps lever left = bitboards; else gain via pruning/eval/ordering. exp028 = aspiration windows → v019, +29 Elo (400g). exp029 = mobility eval → REJECTED, neutral (1.66x slower, ate gain; needs bitboards). exp030 = scaled LMR → REJECTED (600g +10.4, variance; use 400-600g for tuning). exp031 = bitboard movegen+attacks → v020, infra/neutral (~20% faster movegen but eval scan dominates per-leaf; bb layer now enables CHEAP eval). exp032 = bitboard mobility eval → v021, +96 Elo (400g, LOS~100%) — biggest eval gain, ~cracks 2000 (est ~2050-2070); same term exp029 rejected at +8.7 on shallow v013 (re-test rejected eval terms after search deepens). exp033 = bitboard king-safety (attacker count) → REJECTED, -60 (slider ray-loops per leaf ON TOP of mobility = depth loss + crude signal). LESSON: magic bitboards (O(1) sliders) MUST precede more per-leaf eval. exp034 = magic bitboards (O(1) sliders) → v022, +98 Elo (400g, LOS~100%) — recovers mobility cost; bitboard arc compounding. Est ~2150-2170. exp035 = king-safety retry → REJECTED again, -56 (term itself harms play, NOT cost; failed 3x exp019/033/035 — stop hand-set king-safety). exp036 = SPSA harness + mobility tuning → no gain (weights already optimal {4,4,2,1}); harness shipped (research/run_spsa.py, config-only, checkpoint-resumable). Next SPSA targets: pawn-structure weights, piece values; or SEE quiescence pruning / tapered eval. exp037 = SEE quiescence pruning → REJECTED, neutral (-8.7; 36% faster q-search but static SEE prunes sound tactics; see_capture retained for ordering). exp038 = tapered eval (PeSTO mg/eg PST by phase) → v023, +110 Elo (400g, LOS~100%) — biggest eval gain since mobility, breaks the post-2000 plateau; vs exp020 mg-only neutral, the ENDGAME tables+phase blend are the signal. exp039 = tapered material (PeSTO mg/eg piece values folded into phase blend) → v024, +34 Elo (400g, LOS~97%; batch A +17 borderline, B confirmed). Next: SPSA on tapered base, tapered pawn-structure/bishop-pair, SEE-ordering, re-anchor vs SF (2 eval wins since last anchor).)

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).
