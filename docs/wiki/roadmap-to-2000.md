# Roadmap To ~2000 Elo

Target: a deterministic classical engine around 2000 Elo, reached through the
autoresearch loop. This page is the strategic plan. Read it before choosing the next
experiment.

## Where the engine is

As of v010: depth ~3-4 alpha-beta with material + crude piece-square eval, quiescence,
MVV-LVA ordering, check extension, iterative deepening + time management,
transposition table, TT-move ordering, minimal UCI.

Absolute Elo is known via the Stockfish anchor: **v011 ≈ 1714 ±46** (exp016, vs SF1700,
95-87-18); v010 was ≈1581 (exp015, vs SF1600). The engine is still structurally weak
(no king safety / pawn structure / mobility eval; slow make-on-copy movegen; draws many
games by repetition) — the headroom to ~2000 is in the structural items below.

**exp016 finding:** the build was compiling at -O0 (no optimization). Defaulting to
Release (-O3) was a 4.1× nodes/sec win → +117 Elo, zero logic change. Always build
optimized; verify before micro-optimizing code.

## The key finding that sets the strategy

With varied openings (exp009) the metric finally produces decisive games. Results:

```text
- v007 vs v000 (eval vs material-only): 15 - 0 - 5  -> big differences ARE decisive
- depth-4 vs depth-3: +147 Elo at 30+0.3            -> depth is the dominant lever
- adjacent micro-tweaks (root-PV, budget, TT, TT-move) at 4+0.1: all within noise
```

Conclusion: **at ~depth 3-4, small eval/search tweaks cannot win — there is no extra
ply to convert.** The path to 2000 is structural depth and real eval, not polish.

## Order of work (structural first, fine-tuning last)

### 1. Elo anchor (DONE — exp015)
Anchor = Stockfish 18 pinned via `UCI_LimitStrength` + `UCI_Elo`, measured by
`research/run_anchor.py` (absolute Elo = anchor_elo + cutechess Elo diff). v010 ≈ 1581.
Set `--anchor-elo` near the expected level so the match scores ~50% (tightest error).
Caveat: `UCI_Elo` is calibrated for slower TC; the bullet number is an anchored estimate.

### 2. Faster move generation (biggest single lever) — IN PROGRESS
exp016 took the free part: enabling -O3 (4.1× nodes/sec, +117 Elo). Remaining
algorithmic work: replace make-on-copy (allocates a Board per move) with make-unmake or
bitboards; cache the king square (legality currently calls `find_king`, a 64-square
scan, per move); `reserve()` the move vector. More nodes/sec → depth, and depth was
worth +147 Elo for one ply here. Gate hard with perft (must stay exact at depths 1-5 +
tricky positions).

### 3. Real evaluation — IN PROGRESS
exp018 added pawn structure (doubled/isolated/passed): +51 Elo internal vs v012 → v013.
Remaining: king safety (pawn shield / open files near king), mobility, tuned PSTs. Expose
weights in config so later tuning is config-only. Several hundred Elo of headroom lives
here, and eval terms are measurable at the current depth (unlike search micro-tweaks).

**Anchor-noise caveat (exp018):** the SF `UCI_Elo` anchor at 200 games / bullet TC has
±47 Elo error and miscalibrates/saturates — the same engine measured 1684 vs SF1700 and
1937 vs SF1800. Trust the internal version-vs-version ladder for deltas; use the anchor
only as a coarse band. For a tighter absolute number, raise game counts or pick one fixed
unsaturated SF level.

### 4. Search pruning / extensions / ordering — IN PROGRESS
exp021 null-move pruning: +20 → v014 (1.76× fixed-depth). exp022 LMR: +48 over 400g →
v015 (5.7×, LOS ~99.7%). exp023 PVS: REJECTED −44 (move ordering too weak). exp024 killer
moves + history heuristic: +110 → v016 (7.2× fixed-depth, LOS ~100%) — ordering was the
real bottleneck. exp025 retried PVS on the strong ordering and it **still lost −44**: the
node cost here is dominated by make-on-copy + full-board hashing, not the search window,
so PVS cannot pay until nodes are cheap.

Estimate after v016 ≈ 1925–1945 — within striking distance of the 2000 target.

exp026 added **make/unmake** (v017, infrastructure) — but it was **performance-neutral**:
the ~80-byte Board copy is a cheap memcpy, not the bottleneck. Corrected node-cost model:
the real per-node costs are move generation, the **full-board FNV hash recomputed every
node**, and the eval scan. exp027 then added **incremental Zobrist hashing** (v018, infra) — also **neutral**: the
per-node FNV hash was not the bottleneck either. Two experiments now agree the real
per-node cost is **move generation + `is_square_attacked` ray scans (legality on every
pseudo-move) + the eval scan**, not move-copy or hashing. The only big nps lever left is a
**bitboard movegen/attack-detection rewrite** (a multi-experiment project). Otherwise,
keep gaining via tree-size levers (ordering/pruning — where LMR +48 and killers+history
+110 came from) and real eval.

exp028 added **aspiration windows** (v019): +29 Elo over 400 games (LOS ~95%) — a real
tree-size gain. **Estimate ≈ 1955–1975, essentially at the 2000 target band.** Remaining
clean levers: mobility / tuned eval (steps 3/5), then a bitboard rewrite (step 2) to push
well past 2000.

### 5. Parameter fine-tuning (last)
Once real structure exists, tune eval weights and search params (hand-tuning or
SPSA-style) against the anchor with large samples.

## Is ~2000 reachable this way?

Yes, in principle — 2000 is routine for a classical engine with fast movegen
(depth 8-12+), a real eval, and standard pruning, and the autoresearch loop is a sound
way to get there as long as experiments tackle the structural items above and are
verified at 200+ games / SPRT. It will NOT happen via micro-tweaks at the current
depth. Beyond ~2300-2400 the effort rises steeply (strong eval tuning, SF-grade
search) and is out of scope for now.

## Testing requirement

Strength claims require 200+ games or SPRT. See [[acceptance-rules]]. Small matches are
screening only.

## Links

- [[overview]]
- [[research-loop]]
- [[acceptance-rules]]
- [[implementation-roadmap]]
