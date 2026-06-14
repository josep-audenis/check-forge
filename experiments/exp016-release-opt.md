# Experiment exp016 — Release build (enable compiler optimization)

## Hypothesis

Roadmap step 2 is "faster execution → more nodes/sec → more depth → Elo." Before
rewriting move generation, check the build flags: `build/CMakeCache.txt` showed
`CMAKE_BUILD_TYPE` **empty**, i.e. g++ compiled the engine with NO optimization (-O0).
Every frozen version (v000–v010), including the exp015 anchor baseline, was unoptimized.

Hypothesis: defaulting the build to Release (-O3 -DNDEBUG) is a large, zero-risk
nodes/sec win that buys real search depth and therefore real Elo — the cheapest possible
form of "faster move generation."

## Change

- `CMakeLists.txt`: default `CMAKE_BUILD_TYPE` to `Release` when unset (and no
  multi-config generator). No source/algorithm change — identical engine logic, just
  optimized codegen.
- Fixed the research harness for Python 3.14 on Windows (it no longer resolves relative
  executable paths via subprocess): `harness._resolve_engine()` now makes real engine
  paths absolute; applied in `run_engine`, `engine_version`, and `run_perft.py`. This
  unbroke `run_perft.py` / `run_tactics.py`.

## Files changed

- `CMakeLists.txt`
- `research/harness.py`
- `research/run_perft.py`

## Expected effect

Much higher nodes/sec → ~1 extra ply on average at the same TC → large Elo gain
(one ply was worth +147 Elo earlier).

## Risks

None to correctness (same logic). Only risk was a codegen/UB difference; gated by perft,
tactics, and unit tests — all pass with identical node counts.

## Tests run

- Unit (ctest): 1/1 pass.
- Perft: all cases pass (depths 1–5), **node counts identical** to v010.
- Tactical suite: 8/8.
- Raw speed: perft(5) on a midgame FEN — **3.08s vs 12.72s for v010 → 4.1× faster**,
  same 30,293,344 nodes.
- Internal verification (200 games, varied openings, 8+0.08), release vs v010:
  **84-19-97, +117.2 ±34.5 Elo, LOS 100%, 0 flags/illegal.**
- Anchor (200 games, 8+0.08), release vs SF1700: **95-87-18 → 1713.9 ±46.2 Elo.**

## Results

```json
{
  "speed": {"perft5_release_s": 3.08, "perft5_v010_s": 12.72, "speedup": 4.13},
  "internal_vs_v010": {"w": 84, "l": 19, "d": 97, "elo_diff": 117.2, "elo_err": 34.5, "los": 100.0},
  "anchor_vs_SF1700": {"w": 95, "l": 87, "d": 18, "checkforge_elo": 1713.9, "elo_err": 46.2},
  "absolute_elo_before": 1580.9,
  "absolute_elo_after": 1713.9
}
```

## Decision

**Accepted (strength).** New head `versions/v011-release-opt`.

## Reason

+117 Elo internal over 200 games with LOS 100% blows past the +15 accept threshold;
correctness fully preserved (identical perft, 8/8 tactics, unit tests). Two independent
measurements agree: v010 1581 + 117 internal ≈ 1698, anchor places release at 1714.
Absolute Elo 1581 → ~1714 (+133).

## Notes

- The single biggest win so far came not from an algorithm but from a one-line build-config
  fix. Lesson: verify the build is optimized before micro-optimizing code.
- Speed headroom remains in the movegen *algorithm* (make-on-copy, `find_king` 64-square
  scans per legality check, no vector reserve). Those are still worth doing on top of -O3.

## Next experiment idea

exp017: algorithmic movegen speedup on top of -O3 — cache king square (drop `find_king`
scans), `reserve()` the move vector, and/or make-unmake to cut the per-move legality
copy. Gate with perft, then re-measure vs SF1700.
