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
