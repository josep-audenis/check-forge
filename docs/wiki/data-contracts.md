# Data Contracts

Data contracts let engine, benchmark scripts, research loop, and dashboard evolve without guessing.

## Config JSON

Planned file:

```text
configs/default.json
```

Implemented shape:

```json
{
  "piece_values": {
    "pawn": 100,
    "knight": 320,
    "bishop": 330,
    "rook": 500,
    "queen": 900
  },
  "eval_weights": {},
  "search_params": {
    "default_depth": 3
  }
}
```

Rules:

```text
- invalid config fails safely
- benchmark result records config path/hash
- config changes must affect engine behavior when relevant
- engine accepts `--config <path>` before commands, including `uci`
```

## Benchmark Result JSON

Implemented file pattern:

```text
results/latest.json
results/<experiment_id>/summary.json
results/<experiment_id>/<benchmark>.json
```

Aggregate shape:

```json
{
  "experiment_id": "20260612T104006Z-baseline",
  "engine": "build/engine/checkforge.exe",
  "engine_version": "CheckForge 0.1.0-phase4",
  "git_commit": "51da13aa01ee69f81a10aa3d6e22023f9a0e13bf",
  "config": {
    "path": "configs/default.json",
    "sha256": "..."
  },
  "steps": [
    {
      "name": "perft",
      "passed": true,
      "output": "results/<experiment_id>/perft.json"
    }
  ],
  "accepted": true,
  "reason": "All correctness and smoke benchmarks passed."
}
```

## Measurement Result JSON (schema v2)

External match outputs preserve `wins`, `losses`, `draws`, `games`, `score`,
`elo_diff`, and `elo_err`. Added fields:

```json
{
  "schema_version": 2,
  "measurement_valid": true,
  "profile_passed": true,
  "results": {
    "elo_se": 22.6,
    "elo_ci": [-26.9, 62.3],
    "elo_err": 44.9,
    "elo_error_confidence": 0.95,
    "pairing": {
      "complete": true,
      "pairs": 100,
      "pentanomial": {"counts": [16, 11, 40, 13, 20]},
      "confidence_unit": "opening_pair",
      "schedule_validation": {"complete": true, "mismatches": []}
    },
    "validation_errors": []
  },
  "reproducibility": {
    "seed": 1,
    "concurrency": 1,
    "openings": {
      "path": "...",
      "sha256": "...",
      "nonempty_lines": 500,
      "unique_nonempty_lines": 500,
      "duplicate_nonempty_lines": 0,
      "unique_positions": 500,
      "duplicate_positions": 0
    },
    "opening_schedule": {
      "sampling": "iid_with_replacement_from_unique_epd_positions",
      "seed": 1,
      "pairs": 2300,
      "schedule": {"path": "...", "sha256": "..."}
    },
    "cutechess": {"path": "...", "version": "...", "sha256": "..."},
    "opponent_artifact": {"path": "...", "version": "...", "sha256": "..."}
  }
}
```

`elo_err` is requested-confidence half-width when finite; default confidence is 95%.
`elo_se` is one standard error. Pair validation, completed-game count, illegal markers,
and any candidate/opponent time forfeits contribute to `measurement_valid`.
Strength decisions use separate `profile_passed`; valid H0 or inconclusive results do
not pass. Anchor aggregates use random effects plus spread, I-squared, artifact-hash,
and engine-family gates.

## Experiment Report Markdown

Reports live in:

```text
experiments/
```

See [[experiment-template]].

## Dashboard Contract

Dashboard should read:

```text
- results/*.json
- experiments/*.md
```

Dashboard should not become source of truth at first.

## Links

- [[dashboard-strategy]]
- [[research-loop]]
- [[experiment-template]]
