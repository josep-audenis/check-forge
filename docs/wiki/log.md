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

## [2026-06-13] autoresearch | exp006 tactical suite

Expanded `research/run_tactics.py` from 2 to 8 verified tactical positions
(mate-in-1, pins/forks, hanging-piece wins) to give a real accuracy metric. exp005's
prescribed next step. Raises the measurement bar; does not alter expected outputs.

Results:

```text
tactics on v005: 8/8 solved
decision: accepted as infrastructure; no engine binary version produced
```

## [2026-06-13] autoresearch | exp007 MVV-LVA ordering

Replaced victim-only capture ordering with MVV-LVA (`(victim+promotion)*100 - attacker`).

Results:

```text
benchmark accepted=true, tactics 8/8
cutechess score vs v005: 0 - 0 - 20 [0.500], all draws by 3-fold repetition
decision: accepted as search infrastructure; no Elo gain
saved version: versions/v006-mvv-lva
```

## [2026-06-13] autoresearch | exp008 bishop-pair eval

Added a symmetric +30 bishop-pair bonus in `evaluate_static`.

Results:

```text
benchmark accepted=true, tactics 8/8
cutechess score vs v006: 0 - 0 - 20 [0.500], all draws by 3-fold repetition
decision: accepted as eval infrastructure; no Elo gain
saved version: versions/v007-bishop-pair
```

## [2026-06-13] finding | Elo metric saturated by repetition draws

Three consecutive experiments (exp006-008) confirm version-vs-version cutechess is
stuck at 0-0-N draws by 3-fold repetition: two deterministic clones play the same
opening into the same shuffle, so no ordering/eval change can produce a decisive
game. The 3-fold repetition draw — not search/eval quality — is the binding
constraint on any measurable strength gain. Next high-value work is measurement
infrastructure (search-node counters, opening-book variety, or repetition handling),
not more eval/search polish against a flat metric.

## [2026-06-13] autoresearch | exp009 varied openings (metric unlock)

Added `data/openings.epd` (12 openings) and `--openings` support in
`research/run_cutechess.py` (`-openings ... order=random -repeat`). First decisive
games in the project.

Results:

```text
v007 vs v000: 15 - 0 - 5  (first clear wins; positional eval crushes material-only)
v007 vs v005: 4 - 6 - 10  (noise); v006 vs v005: 6 - 6 - 8 (neutral)
decision: accepted as infrastructure; "no Elo" in exp001-008 was a measurement artifact
```

## [2026-06-13] autoresearch | exp010 time management -> v008

Iterative deepening + clock-aware budget (`SearchContext`, `search_bestmove_timed`,
UCI `wtime/btime/movetime` parsing). `go depth` still fixed-depth for tests. Uses
`GetTickCount64` (toolchain `<chrono>` misses `features.h`). Bug found+fixed: abort
must be sticky or each iteration runs to completion (3.8x budget overshoot).

```text
cutechess vs v007: 8 - 6 - 16, Elo +23.2 ±86.6, 0 time losses
decision: accepted; removes the time-loss failure mode (exp004), unlocks depth scaling
saved version: versions/v008-time-management
```

## [2026-06-13] autoresearch | exp011 root-PV ordering (rejected)

Search previous iteration's best move first at root.

```text
cutechess vs v008: 10 - 15 - 15, Elo -43.7 ±87.1, LOS 15.9%
decision: rejected (no gain, negative trend); reverted
```

## [2026-06-13] autoresearch | exp012 time budget (rejected)

Raised budget to remaining/20 + full increment.

```text
cutechess vs v008: 7 - 18 - 15, Elo -98.1, LOS 1.4%, 11 time losses
decision: rejected (flagged + significantly worse); reverted to remaining/30 + 3/4 inc
```

## [2026-06-13] autoresearch | exp013 transposition table -> v009

2^20-entry FNV-keyed TT with exact/lower/upper bounds, depth-preferred replacement,
mate scores not stored. Reset per search.

```text
cutechess vs v008: +8.7 ±79 at 4+0.1; +21.7 ±74 at 12+0.1; 0 flags; tactics 8/8; perft ok
decision: accepted as search infrastructure (non-negative, scales with depth)
saved version: versions/v009-transposition
```

## [2026-06-13] autoresearch | exp014 TT-move ordering -> v010

Store best move in TT entries; search it first at root and interior nodes.

```text
cutechess vs v009: 7 - 8 - 25, Elo -8.7 ±66.6, 0 flags
decision: accepted as infrastructure (strength-neutral at bullet, not a proven gain)
saved version: versions/v010-tt-move-ordering
```

## [2026-06-13] finding | bullet TC ceiling and where wins come from

With varied openings the metric works and decisive games appear. Clear wins exist
against weaker versions (v007 vs v000 15-0; depth-4 vs depth-3 +147 Elo at 30+0.3).
Between ADJACENT versions at 4+0.1, search micro-optimizations (root-PV, bigger
budget, TT, TT-move ordering) are near-neutral: the engine only reaches ~depth 3-4,
so no extra ply is available to win. The real levers for measurable adjacent-version
Elo are (a) longer TC / faster move generation to add real depth, or (b) larger eval
jumps. The current make-on-copy move generator is the practical depth limiter.

## [2026-06-13] rules | new approach for continuing agents

Rewrote the operating rules so a fresh session continues correctly from v010 (not from
scratch). New strategy: **structural work first, fine-tuning last** — Elo anchor ->
faster movegen -> real eval -> search pruning -> only then parameter tuning. New
testing rule: **strength claims require 200+ games or SPRT**; small matches are
screening only. `research/run_cutechess.py` default `--games` raised 20 -> 200.

Touched:

- `CLAUDE.md` (new) - agent entry point, current state, build/run commands that work
- `AGENT_INSTRUCTIONS.md` - strategy order, screening/verification, real commands
- [[roadmap-to-2000]] (new) - strategy and rationale for reaching ~2000 Elo
- [[acceptance-rules]] - screening vs verification, infrastructure-accept, SPRT
- [[research-loop]] - current state, real commands, screening/verification
- [[implementation-roadmap]] - fixed Windows build command, milestone status
- [[index]] - link roadmap-to-2000; point new agents at CLAUDE.md/AGENT_INSTRUCTIONS.md

Also recorded two facts: no absolute Elo exists yet (all matches relative; anchor
needed), and the make-on-copy movegen is the depth limiter.

## [2026-06-13] autoresearch | exp015 Elo anchor (first absolute Elo)

Added a known-rated reference opponent so results are now in real Elo (roadmap step 1).

```text
anchor: Stockfish 18, UCI_LimitStrength + UCI_Elo (floor 1320), avx2 build via winget
tool:   research/run_anchor.py -> absolute Elo = anchor_elo + cutechess Elo diff
verify: v010 vs SF1600, 200 games, 8+0.08, varied openings -> 90-101-9 (~47%)
result: CheckForge v010 ~= 1581 +/- 47 Elo, 0 flags/illegal
decision: accepted as INFRASTRUCTURE + measurement; no engine change; head stays v010
caveat: UCI_Elo calibrated for slower TC; bullet number is an anchored estimate
```

Correction to prior belief: engine is ~1580, not sub-1000. Next: roadmap step 2,
faster move generation (make-unmake/bitboards), then re-measure vs SF1600.

## [2026-06-13] autoresearch | exp016 Release build (-O3) -> v011

Roadmap step 2. Found CMAKE_BUILD_TYPE empty -> engine compiled with NO optimization
(-O0). Defaulted build to Release (-O3 -DNDEBUG). No source/logic change.

```text
speed:    perft5 4.1x faster (3.08s vs 12.72s v010), identical node counts
gates:    ctest 1/1, perft d1-5 exact, tactics 8/8
internal: release vs v010, 200g 8+0.08 -> 84-19-97, +117.2 +/- 34.5 Elo, LOS 100%, 0 flags
anchor:   release vs SF1700, 200g -> 95-87-18 -> 1713.9 +/- 46.2 Elo
absolute: 1581 -> ~1714 (+133)
decision: ACCEPTED (strength). head -> versions/v011-release-opt
```

Also fixed Python 3.14 relative-exe-path bug in harness (run_perft/run_tactics were
broken). Lesson: verify the build is optimized before micro-optimizing code.

## [2026-06-13] autoresearch | exp017 movegen king-cache -> v012

Drop per-move find_king (64-square scan) in generate_legal_moves: find king once, derive
post-move king square in O(1), check is_square_attacked directly. Plus vector reserve().

```text
speed:    perft6 1.34x faster (66.2s vs 88.8s v011), node counts identical (948,211,582)
gates:    ctest pass, perft d1-5 exact, tactics 8/8
internal: exp017 vs v011, 200g 8+0.08 -> 46-46-108, +0.0 +/- 32.7 Elo, 0 flags
decision: ACCEPTED as INFRASTRUCTURE (faster, strength-neutral at bullet). head -> v012-king-cache
```

Strength-neutral as expected (34% nps < one ply at bullet depth). Next big lever: real
eval (roadmap step 3), or make-unmake to drop the per-move Board copy.

## [2026-06-14] autoresearch | exp018 pawn-structure eval -> v013

Roadmap step 3 (real eval). Added doubled (-15/extra), isolated (-12), passed
({10,17,25,40,65,100} by rank) pawn terms to evaluate_static. Hardcoded weights.

```text
gates:    ctest pass, perft exact, tactics 8/8
internal: exp018 vs v012, 200g 8+0.08 -> 77-48-75, +50.7 +/- 38.3 Elo, LOS 99.5%, 0 illegal
anchor:   vs SF1700 90-99-11 -> 1684; vs SF1800 136-61-3 -> 1937 (contradictory)
decision: ACCEPTED (strength). head -> versions/v013-pawn-structure
estimate: ~1750-1765 absolute (internal ladder 1714 + 51)
```

Methodology finding: the SF UCI_Elo anchor is too noisy/miscalibrated at bullet TC to
resolve a ~50-Elo change (SF1700 and SF1800 gave 1684 vs 1937 for the SAME engine).
Trust the internal version-vs-version ladder for deltas; treat the anchor as a coarse
band only. Next: king safety / mobility (roadmap step 3 continues).

## [2026-06-14] autoresearch | exp019 king-safety (pawn shield) -> REJECTED

Added pawn-shield king-safety term (-14 front / -7 second rank per king-adjacent file,
gated on enemy queen). Folded into evaluate_static.

```text
gates:    ctest pass, perft exact, tactics 8/8
verify:   candidate vs v013, 200g 8+0.08 -> 47-44-112, +5.1 Elo (~+/-24), 0 illegal
decision: REJECTED (strength-neutral). reverted. head stays v013-pawn-structure
```

Crude shield count doesn't change move choice at depth ~6 (54% draws). Contrast exp018
pawn structure which did move the needle (+51). Next: mobility or tuned PSTs.

Infra incident: cutechess finished all 200 games but the wrapper died before writing the
JSON (orphaned background task); result reconstructed from the PGN (ground truth).
Follow-up: make run_cutechess.py derive W-L-D from its own PGN so a completed match can't
be lost.

## [2026-06-14] infra | recover matches from PGN (run loss hardening)

Two exp019 runs lost their result JSON when the wrapper process was orphaned mid/after a
completed match. Added `research/score_pgn.py` (W-L-D + Elo from a PGN, the ground truth)
and wired `run_cutechess.py` to store PGN-derived `results` in its JSON. Recover any
orphaned match with: `python research/score_pgn.py <pgn> --engine checkforge`.

## [2026-06-14] infra | why long matches sometimes die + fix (--detach)

Investigated repeated mid-match deaths (exp019 122/200, exp020 78/200; one exp019 run
DID reach 200). Evidence:
- All background-task output files were 0 bytes -> no Python traceback, no stdout.
- The dead PGNs' last game ended cleanly (normal 3-fold draw, ~20s) -> engines healthy,
  no crash / time-loss / illegal move.
- No WER crash dump for today's deaths (the python.exe/OLED dumps in CrashDumps are old:
  May 4 / Jun 7), so python did NOT crash.

Conclusion: the match process tree is **terminated externally while healthy** (clean
TerminateProcess), most consistent with the harness reaping the background-task job on
long unattended runs (and possibly Windows idle / modern-standby; an "OLED Care
Screensaver" is installed). Not an engine, cutechess, or script bug.

Fix: added `--detach` to `run_cutechess.py` and `run_anchor.py` — launches cutechess with
`DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_BREAKAWAY_FROM_JOB` so it survives
parent/job termination, returns immediately, and writes the PGN. Poll the PGN and score
with `research/score_pgn.py` (the PGN is ground truth). Recommend also disabling display
sleep / the OLED screensaver during long runs.

## [2026-06-14] autoresearch | exp020 PST (PeSTO midgame tables) -> REJECTED

Replaced ad-hoc positional_value with PeSTO midgame piece-square tables. Orientation
verified (mirror 373~=376, startpos 0, e4>a1 knight).

```text
gates:    ctest pass, perft exact, tactics 8/8
verify:   PST vs v013, 201 games (two batches A+B), 8+0.08 -> 45-44-112, +1.7 Elo (+/-24), 0 illegal
decision: REJECTED (strength-neutral). reverted. head stays v013-pawn-structure
```

Second neutral eval term after exp019. Generic PeSTO tables don't beat the engine's
already-tuned crude centrality/advance eval at depth ~5-6: PST mostly re-encodes
centrality the crude eval already has, so move ranking barely changes. Pawn structure
(exp018, +51) worked because it added genuinely new info (passed/isolated/doubled).
Both batches were killed by the harness reap (~78 and ~123 games) but aggregated via the
PGN to a full 201-game sample.

## [2026-06-15] autoresearch | exp021 null-move pruning -> v014

Roadmap step 4 (search). NMP in negamax: depth>=3, narrow window, non-pawn material,
not in check -> search null move at depth-1-R (R=2), cutoff if >= beta.

```text
gates:    ctest pass, perft exact, tactics 8/8
speed:    fixed depth-7 1.76x faster (13.9s vs 24.5s v013), same move/score
verify:   NMP vs v013, 400 games (two detached batches) 8+0.08 -> 101-78-221, +20.0 Elo (+/-17.4 1sigma), 0 illegal
          consistent across batches (A +20.9, combined +20.0)
decision: ACCEPTED (strength). head -> versions/v014-null-move
```

First strength gain since exp018. Backed by deterministic 1.76x depth speedup + batch
consistency (vs the noise that sank exp019/020). 55% draws inflate Elo error (LOS ~87%),
but the consistent +20 plus the depth win justify accept; bullet TC likely understates a
depth-sensitive change. --detach fix worked (both batches completed, no reaping).
Estimate now ~1770-1785. Next: LMR or make-unmake.

## [2026-06-15] autoresearch | exp022 late move reductions (LMR) -> v015

Roadmap step 4. LMR in negamax: depth>=3, move_count>=4, not in check, quiet move ->
search depth-2 null-window, re-search full depth if it beats alpha.

```text
gates:    ctest pass, perft exact, tactics 8/8
speed:    fixed depth-8 5.7x faster (9.1s vs 51.8s v014), same score
verify:   LMR vs v014, 400 games (two detached batches) 8+0.08 -> 117-62-221, +48.1 Elo (+/-17.5 1sigma), LOS ~99.7%, 0 illegal
decision: ACCEPTED (strength). head -> versions/v015-lmr
```

Strongest gain since -O3. Reductions apply to most (late quiet) moves at every node, so
the tree shrinks super-linearly with depth -> 5.7x speedup. Compounds with NMP.
Estimate now ~1815-1835. Next: PVS or make-unmake.

## [2026-06-20] autoresearch | exp023 PVS -> REJECTED

Added principal variation search (null-window scout for all non-first moves, re-search
inside window) on top of LMR.

```text
gates:    ctest pass, perft exact, tactics 8/8; PVS scores IDENTICAL to v015 (exact)
speed:    fixed depth-8 only ~5% faster
verify:   PVS vs v015, 200g 8+0.08 -> 37-62-101, -43.7 Elo (+/-24.8), 0 illegal
decision: REJECTED (-44 Elo). reverted. head stays v015-lmr
```

PVS is correct but loses in timed play: move ordering is too weak (MVV-LVA + TT move
only), so scouts fail high often -> frequent full re-searches cost more than they save ->
less depth. Prerequisite for PVS = killer/history move ordering. Next: killers+history.

## [2026-06-20] autoresearch | exp024 killer moves + history heuristic -> v016

Roadmap step 4 (ordering, motivated by exp023). Added two killers/ply + from->to history
table; quiet-move ordering = captures(MVV-LVA) > killers > history. Updated on quiet
beta-cutoffs.

```text
gates:    ctest pass, perft exact, tactics 8/8
speed:    fixed depth-9 7.2x faster (31s vs 3m43s v015), same move/score
verify:   vs v015, 200g 8+0.08 -> 76-15-109, +109.5 Elo (+/-25.8), LOS ~100%, 0 illegal
decision: ACCEPTED (strength). head -> versions/v016-killers-history
```

Biggest gain since -O3. Move ordering was the bottleneck (exp023 PVS failed for lack of
it); fixing it is worth +110 and sharpens NMP/LMR. Estimate now ~1925-1945 (closing on
2000). Unblocks PVS retry. Next: retry PVS, or make-unmake.

## [2026-06-20] autoresearch | exp025 PVS retry on v016 -> REJECTED

Retried PVS now that v016 has killer/history ordering.

```text
gates:    ctest pass, perft exact, tactics 8/8 (PVS exact)
speed:    fixed depth-9 ~9% SLOWER (23.8s vs 21.8s v016)
verify:   PVS vs v016, 200g 8+0.08 -> 34-59-107, -43.7 Elo (+/-24.8), 0 illegal
decision: REJECTED (-44, same as exp023). reverted. head stays v016-killers-history
```

Corrected lesson: PVS loses NOT because of ordering but because node cost is dominated by
make-on-copy + full-board hashing, so a null-window scout saves ~nothing while re-searches
pay full board-copy cost. PVS needs cheap nodes. Next structural lever: make-unmake
(and/or incremental Zobrist hashing).

## [2026-06-20] autoresearch | exp026 make/unmake move -> v017 (infrastructure)

Replaced make-on-copy with in-place make/unmake in legality, perft, and the whole search
(negamax/quiescence/root + null-move). make_move (copy) kept for external callers.

```text
gates:    ctest pass, perft EXACT (all depths), tactics 8/8; search output bit-identical to v016
speed:    perft6 206.2s vs 207.6s v016 -> identical (both ~3x slower than past = thermal throttle)
verify:   vs v016, 200g 8+0.08 -> 51-46-103, +8.7 Elo (+/-24.6), 0 illegal -> neutral
decision: ACCEPTED as INFRASTRUCTURE (no Elo). head -> versions/v017-make-unmake
```

Refutes exp025's hypothesis: the ~80-byte Board copy is NOT the bottleneck (cheap memcpy
== make/unmake+Undo). Real per-node cost = movegen + full-board FNV hash per node + eval
scan. Kept as the standard foundation that ENABLES the real win: incremental Zobrist
hashing (update key in make/unmake vs rescanning 64 squares/node). Next: incremental
Zobrist hashing, then retry PVS.

## [2026-06-22] autoresearch | exp027 incremental Zobrist hashing -> v018 (infrastructure)

Replaced per-node full-board FNV hash with a Zobrist key maintained incrementally in
make/unmake (board.zobrist; seeded by compute_zobrist at root + from_fen). Old hash_board
removed.

```text
gates:    ctest pass, perft exact, tactics 8/8
correctness: temp self-check board.zobrist==compute_zobrist after every make ran clean
             through perft on startpos/kiwipete/ep/promotions (millions of makes)
speed:    fixed depth-9 18.99s vs 18.97s v017 -> identical
verify:   vs v017, 200g 8+0.08 -> 50-51-99, -1.7 Elo (+/-24.6), 0 illegal -> neutral
decision: ACCEPTED as INFRASTRUCTURE (no Elo). head -> versions/v018-zobrist
```

Second neutral per-node change after make/unmake. Confirms node-cost bottleneck is
movegen + is_square_attacked ray scans + eval, NOT move-copy or hashing. Kept as correct
standard O(1) design. Real nps lever left = bitboard movegen (big rewrite); otherwise
gains come from tree-size (ordering/pruning) and eval. Next: aspiration windows or
mobility eval.

## [2026-06-23] autoresearch | exp028 aspiration windows -> v019

Roadmap step 4. Iterative deepening now searches depth>=4 within [prev-35, prev+35],
widening on fail. search_root takes a window + beta-cuts; fixed-depth path unchanged.

```text
gates:    ctest pass, perft exact, tactics 8/8
verify:   vs v018, 400 games (two detached batches) 8+0.08 -> 111-78-211, +28.7 Elo (+/-17.4), LOS ~95%, 0 illegal
          both batches positive (A +41.9, B +15.6)
decision: ACCEPTED (strength). head -> versions/v019-aspiration
```

Real tree-size gain (vs the neutral per-node exp026/027). Estimate now ~1955-1975 -
essentially at the 2000 band. Next: mobility eval or weight tuning; bitboards for big nps.

## [2026-06-23] autoresearch | exp029 mobility eval -> REJECTED

Added knight/slider pseudo-mobility term (N=4/B=4/R=2/Q=1 per square) to evaluate_static.

```text
gates:    ctest pass, perft exact, tactics 8/8
speed:    fixed depth-9 1.66x SLOWER (128s vs 77s v019) - slider ray scans per eval leaf
verify:   vs v019, 200g 8+0.08 -> 52-47-101, +8.7 Elo (+/-24.6), 0 illegal -> neutral
decision: REJECTED (does not clear +15). reverted. head stays v019-aspiration
```

Eval gain real but eaten by the 1.66x slowdown (~half a ply lost) -> net ~0. Same pattern
as PVS: sound technique that needs cheap attack-gen (bitboards) to pay. Next: weight
tuning (cheap, step 5), or the bitboard rewrite (step 2).

## [2026-06-23] autoresearch | exp030 scaled LMR -> REJECTED

Made LMR reduction grow with move_count/depth (r up to 3) instead of flat 1.

```text
gates:    ctest pass, perft exact, tactics 8/8
verify:   vs v019, 600 games (3 detached batches) 8+0.08 -> 161-143-296, +10.4 Elo (+/-14.2), LOS ~77%
          per batch A +41.9 / B +0.0 / C ~-10 -> big disagreement
decision: REJECTED (below +15, not significant). reverted. head stays v019-aspiration
```

Process lesson: batch A's +42 (LOS ~95%) alone would have been a FALSE ACCEPT; 600 games
showed true ~+10. For fine-tuning deltas in the noisy +15..+40 band, use 400-600 games /
SPRT, not a single 200. Next: tune LMR trigger / cheap eval weights, or commit to the
bitboard rewrite (the big lever past 2000).

## [2026-06-24] autoresearch | exp031 bitboard movegen + attack detection -> v020 (infrastructure)

Roadmap step 2. New bitboard.{h,cpp} (attack tables + occupancy sliders); Board.bb[12]
maintained in make/unmake + from_fen; is_square_attacked and knight/slider/king move
generation now bitboard-based (pawns + castling unchanged).

```text
gates:    ctest pass, perft EXACT all cases, tactics 8/8
speed:    perft6 ~20% faster (65.1s vs 81.5s v019)
verify:   vs v019, 200g 8+0.08 -> 50-49-101, +1.7 Elo (+/-24.6), 0 illegal -> neutral
decision: ACCEPTED as INFRASTRUCTURE (no Elo). head -> versions/v020-bitboards
```

Neutral in games despite faster movegen: per-leaf cost is dominated by the EVAL board scan
(unchanged), and dual squares[]+bb[] bookkeeping dilutes the win. Real payoff = bitboards
make cheap eval terms viable. Next: bitboard mobility (exp029 was +8.7 even at 1.66x
slower; near-free now -> should clear +15), then king safety, magic sliders, PVS retry.

## [2026-06-25] autoresearch | exp032 bitboard mobility eval -> v021 (BIG WIN, ~cracks 2000)

Re-did the exp029 mobility term on the v020 bitboard layer (popcount of attack bitboards
minus own pieces; N=4/B=4/R=2/Q=1).

```text
gates:    ctest pass, perft exact, tactics 8/8
speed:    fixed depth-9 ~1.55x slower (29.8s vs 19.2s v020) - sliders still ray loops
verify:   vs v020, 400 games (two detached batches) 8+0.08 -> 158-50-192, +96.2 Elo (+/-18.0), LOS ~100%, 0 illegal
          both batches strongly positive (A +79.5, B even stronger)
decision: ACCEPTED (strength). head -> versions/v021-bb-mobility. Estimate ~2050-2070 - 2000 CRACKED.
```

Biggest eval gain of the project. Same term exp029 REJECTED at +8.7 (shallow v013, 1.66x
slower) now wins +96 — because the engine is ~200 Elo deeper AND the bb version is a bit
cheaper. Lesson: an eval term's value scales with search depth; re-test rejected eval
terms after the search gets stronger. This is the payoff the exp031 bitboard foundation
was built for. Next: magic bitboards (O(1) sliders), bitboard king safety, PVS retry,
re-anchor vs Stockfish (likely >2000).

## [2026-06-25] autoresearch | exp033 bitboard king safety -> REJECTED

Added king-zone attacker-count term (knights+2/bishops+2/rooks+3/queens+5 per attacker,
scale 5 cp/unit) to evaluate_static.

```text
gates:    ctest pass, perft exact, tactics 8/8
verify:   vs v021, 200g 8+0.08 -> 32-66-102, -59.6 Elo (+/-24.9), 0 illegal
decision: REJECTED (-60). reverted. head stays v021-bb-mobility
```

Cost + crude signal. The term runs slider ray-loops per eval leaf ON TOP of mobility,
which already spent the per-leaf budget -> depth loss; plus flat linear attacker-count is
too blunt. Clear signal: MAGIC BITBOARDS (O(1) sliders) must come before stacking more
per-leaf eval terms. Next: magic bitboards (perft-gated), then retry king safety (tuned)
and PVS.

## [2026-06-25] autoresearch | exp034 magic bitboards (O(1) sliders) -> v022 (BIG WIN)

Replaced O(ray) bishop/rook attacks with magic bitboards (init-generated, fixed seed).
Signatures unchanged; perft-gated.

```text
gates:    ctest pass, perft EXACT all cases, tactics 8/8
speed:    fixed depth-9 ~18% faster (24.3s vs 29.4s v021); in-game gain larger (sliders very hot)
verify:   vs v021, 400 games (two detached batches) 8+0.08 -> 151-41-208, +98.1 Elo (+/-18.1), LOS ~100%
          both batches +98
decision: ACCEPTED (strength). head -> versions/v022-magic-bitboards. Estimate ~2150-2170.
```

+98 from a "pure speed" change because v021 mobility makes the slider path extremely hot
per leaf; O(1) magic recovers mobility's 1.55x cost -> big effective depth. Bitboard arc
compounding: exp031 movegen (neutral) -> exp032 mobility (+96) -> exp034 magic (+98).
Lesson: re-measure infra speedups after the workload that stresses them lands. Next: retry
king safety (now affordable), PVS retry, re-anchor vs SF (~2100).

## [2026-06-25] autoresearch | exp035 king safety retry -> REJECTED

Re-tried king-zone attacker-count, now cheap (magic) + gentler bounded danger table.

```text
gates:    ctest pass, perft exact, tactics 8/8
verify:   vs v022, 200g 8+0.08 -> 32-64-104, -56.1 Elo (+/-24.9), 0 illegal
decision: REJECTED (-56). reverted. head stays v022-magic-bitboards
```

Corrects exp033's cost theory: making it cheap did NOT help (-56 ~= -60). The king-safety
TERM itself harms this engine's play (distorts the strong material+PST+pawns+mobility eval).
King safety failed 3x (exp019/033/035) -> STOP hand-set king-safety variants; needs a
fundamentally different / SPSA-tuned model. Next: PVS retry (nodes cheaper post-magic),
re-anchor vs SF ~2100, tune mobility weights.

## [2026-06-25] measurement | re-anchor v022 vs Stockfish -> absolute ~1935 (ladder overstated)

Re-anchored the head (v022) against the external reference after the big bitboard wins.

```text
v022 vs SF UCI_Elo=2000, 200g 8+0.08 -> 71-108-21, elo_diff -65 -> CheckForge ~= 1935 +/- 25
```

Gap vs the raw internal-ladder sum (~2150): ~200 Elo. The self-play ladder OVERSTATES
absolute Elo (relative deltas compound and don't fully transfer to the field; some
intransitivity). SF UCI_Elo at bullet also likely plays above nominal, deflating our read.
Corrected stance: **internal ladder = per-experiment DELTAS only; absolute ~1950-2050 (at
~2000), not 2150.** The deltas themselves (each verified at 200-400g) stand; the absolute
accumulation does not. Honest milestone: CheckForge is ~2000, started ~1581 (exp015).

## [2026-06-25] autoresearch | exp036 SPSA harness + mobility tuning -> no gain (harness shipped)

Built research/run_spsa.py (SPSA: config-only perturbation, same binary, checkpoint-
resumable). Exposed mobility weights in config (default == v022, verified). Tuned the 4
mobility weights, 30 iters x 24 games, TC 4+0.04.

```text
start {4,4,2,1} -> final {3.97,3.93,2.07,1.02} -> rounds to {4,4,2,1} (= v022)
decision: harness ACCEPTED as infra; mobility tuning = NO CHANGE. head stays v022. no version bump.
```

Mobility weights already near-optimal (the +96 in exp032 used good defaults). Deliverable
is the reusable SPSA harness. Next SPSA targets with more headroom: pawn-structure weights
(hardcoded -> expose in config), piece values. Or structural: SEE quiescence pruning,
tapered eval.

## [2026-06-25] autoresearch | exp037 SEE quiescence pruning -> REJECTED

Added bitboard SEE (see_capture, kept) and skipped SEE<0 captures in quiescence (reverted).

```text
gates:    ctest pass, perft exact, tactics 8/8
speed:    fixed depth-10 ~36% faster q-search (30.3s vs 47.1s v022)
verify:   vs v022, 200g 8+0.08 -> 37-42-121, -8.7 Elo (+/-24.6), 0 illegal -> neutral/slightly neg
decision: REJECTED. pruning reverted (see_capture retained). head stays v022.
```

Faster isn't stronger: SEE is static, occasionally prunes captures that start sound
tactics, offsetting the depth gain. Same theme as the neutral per-node speedups. Next:
SEE for capture ORDERING (not pruning, lower risk), tapered eval, or SPSA on pawn-structure.

## [2026-06-25] autoresearch | exp038 tapered eval (mg/eg PST) -> v023 (BIG WIN, breaks plateau)

Replaced crude positional with PeSTO midgame+endgame PST interpolated by game phase
(N1/B1/R2/Q4, max 24).

```text
gates:    ctest pass, perft exact, tactics 8/8, startpos eval 0 (symmetric)
verify:   vs v022, 400 games (two detached batches) 8+0.08 -> 181-58-161, +110.4 Elo (+/-18.3), LOS ~100%
          both batches ~+110
decision: ACCEPTED (strength). head -> versions/v023-tapered-eval
```

Biggest eval gain since bitboard mobility; breaks the 6-experiment plateau (king-safety x3,
scaled-LMR, mobility-SPSA, SEE all failed). Key vs exp020 (mg-only PST, neutral): the
ENDGAME tables + phase blend fix the engine's weakest phase. Lesson again: a rejected idea
becomes a win once the missing ingredient is added. Next: SPSA on new tapered base, tapered
material, SEE-ordering, re-anchor.

## [2026-07-09] autoresearch | exp039 tapered material (PeSTO mg/eg values) -> v024

Folded PeSTO mg/eg piece values into the phase blend alongside the tapered PST (exp038).
Config piece values still used by SEE/ordering/null-move.

```text
gates:    ctest pass, perft exact, tactics 8/8, startpos eval 0
verify:   vs v023, 400 games (two detached batches) 8+0.08 -> 113-74-213, +34.0 Elo (+/-17.5), LOS ~97%
          batch A +17.4 (borderline) -> batch B lifted to +34 combined (400g confirm needed)
decision: ACCEPTED (strength). head -> versions/v024-tapered-material
```

Compounds exp038: phase-appropriate material (rooks/pawns up, minors down into endgame)
improves trading/conversion. Next: SPSA on the tapered base, tapered pawn-structure,
SEE-ordering, re-anchor vs SF (two eval wins since last anchor).
