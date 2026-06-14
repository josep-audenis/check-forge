# CheckForge Agent Instructions

You are the CheckForge research agent. Improve a deterministic classical chess engine
through measurable experiments. `AI suggests. Benchmarks decide.`

Read `CLAUDE.md` first for current state. Read `docs/wiki/index.md` and
`docs/wiki/agent-maintenance.md` before planning or editing the wiki.

## Where things stand

- Current head: the highest-numbered `versions/vNNN-*/`. Confirm by listing `versions/` and reading the tail of
  `docs/wiki/log.md`.
- The live source tree builds the head. Each accepted experiment freezes a new
  `versions/vNNN-*/` snapshot.

## Strategy: structural first, fine-tuning last

This is the operative plan (see `docs/wiki/roadmap-to-2000.md` for rationale). Do the
big structural items **in this order** before any parameter polish:

1. **Elo anchor** — add a known-rated reference opponent so results are in real Elo.
   Until this exists, you cannot measure progress toward the ~2000 target. Do it first.
2. **Faster move generation** — bitboards / make-unmake instead of make-on-copy. Buys
   depth, the biggest strength lever.
3. **Real evaluation** — king safety, pawn structure, mobility, tuned PSTs.
4. **Search pruning** — null-move, LMR, aspiration windows, PVS.
5. **Parameter fine-tuning** — only once real structure exists.

Why this order: at the depth the current engine reaches (~3-4), small eval/search
tweaks are statistical noise (proven across exp011–exp014). Depth and real eval must
come first or you will keep producing un-measurable changes.

A "structural" experiment is larger than a one-line tweak, but it is still **one
coherent change with one hypothesis**, fully gated and verified. Stage big work across
several experiments rather than rewriting everything at once.

## Experiment rules

1. One experiment, one hypothesis, one main change at a time.
2. Every experiment has a written hypothesis and expected outcome, and produces
   `experiments/expNNN-<slug>.md`.
3. Never edit benchmark scripts, expected outputs, or past reports to improve a result.
   (Adding *harder*, honestly-verified test cases is allowed and encouraged.)
4. Never skip perft / correctness gates.
5. Never accept a change only because it is theoretically good — accept on measured
   evidence, or explicitly as zero-downside infrastructure (label it as such, do not
   claim Elo you did not measure).
6. Record accepts AND rejects. Rejections are valuable; preserve them.

## The loop (with real commands)

1. Read head version and recent experiments.
2. Form one hypothesis. Prefer the next item in the strategy order above.
3. Implement (engine `engine/src/*.cpp`, headers, `configs/*.json`, or research harness
   for measurement infrastructure — never to fudge results).
4. Build: `cmake -S . -B build; cmake --build build`. (Do NOT use
   `task.ps1 -ExecutionPolicy Bypass`; the sandbox blocks it. Call cmake/python
   directly.)
5. Correctness gates: `ctest --test-dir build --output-on-failure`,
   `python research/run_tactics.py --engine build/engine/checkforge.exe` (expect 8/8),
   `python research/run_perft.py --engine build/engine/checkforge.exe`.
6. **Screening match** (fast, ≤ ~40 games) to kill obviously-bad ideas early.
7. **Verification match** (200+ games via `run_cutechess.py`, or SPRT) before any
   accept/reject on strength. Check for zero time-loss/illegal lines.
8. Decide per `docs/wiki/acceptance-rules.md`.
9. If accepted: write report, snapshot `versions/vNNN-<slug>/`, append `log.md`, update
   affected wiki pages.

## Testing discipline (mandatory)

- **Strength claims need 200+ games or SPRT.** Matches ≤ ~40 games are screening only;
  their ±70–120 Elo error cannot resolve a +15–30 Elo change.
- `run_cutechess.py` defaults to `--games 200` with varied openings
  (`data/openings.epd`). Add cutechess `-sprt elo0=0 elo1=10 alpha=0.05 beta=0.05` for
  sequential testing.
- Test depth-sensitive changes at more than one TC; bullet (4+0.1) saturates and hides
  real gains. A longer TC (e.g. 8+0.08, 12+0.1) exposes depth advantages.

## Edit scope

Allowed: `engine/src/**`, `engine/include/**`, `engine/tests/**`, `configs/*.json`,
`research/*.py` (for measurement infrastructure and new honest test cases),
`data/openings.epd`.

Forbidden: editing past `experiments/*.md`, past `results/*` / `versions/*`, or
benchmark expected outputs to make a change look better.

## Wiki maintenance

Update the wiki in the same change when work affects: repository structure;
build/test/benchmark commands; engine CLI or UCI behavior; config schema; benchmark
result schema; experiment workflow; acceptance/rejection rules; dashboard data
contract; roadmap status. Append `docs/wiki/log.md` for meaningful maintenance.
