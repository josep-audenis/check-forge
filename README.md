# CheckForge

AutoResearch lab for deterministic classical chess engines.

Start here:

- [Project wiki](docs/wiki/index.md)
- [Wiki maintenance rules](docs/wiki/agent-maintenance.md)
- [Original project plan](PROJECT-PLA.md)

Phase 0 commands:

```powershell
powershell -ExecutionPolicy Bypass -File task.ps1 build
powershell -ExecutionPolicy Bypass -File task.ps1 test
powershell -ExecutionPolicy Bypass -File task.ps1 benchmark
powershell -ExecutionPolicy Bypass -File task.ps1 cutechess
```

Linux/macOS:

```bash
make build
make test
make benchmark
make cutechess
```

Current gate before engine research:

```powershell
powershell -ExecutionPolicy Bypass -File task.ps1 test
powershell -ExecutionPolicy Bypass -File task.ps1 benchmark
```

`benchmark` writes aggregate JSON to `results/latest.json` and per-step JSON under `results/<experiment_id>/`.
`cutechess` requires `cutechess-cli` on `PATH`; internal UCI self-play runs as part of `benchmark`.
