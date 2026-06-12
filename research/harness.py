from __future__ import annotations

import hashlib
import json
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = "configs/default.json"


def utc_id(prefix: str = "experiment") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{prefix}"


def file_sha256(path: str | None) -> str | None:
    if not path:
        return None
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def run_engine(engine: str, args: list[str], config: str | None = DEFAULT_CONFIG, timeout: float = 10.0) -> subprocess.CompletedProcess[str]:
    command = [engine]
    if config:
        command += ["--config", config]
    command += args
    return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)


def engine_version(engine: str) -> str:
    completed = subprocess.run([engine, "--version"], check=False, capture_output=True, text=True, timeout=5.0)
    if completed.returncode != 0:
        return "unknown"
    return completed.stdout.strip()


def git_commit() -> str | None:
    completed = subprocess.run(["git", "rev-parse", "HEAD"], check=False, capture_output=True, text=True)
    if completed.returncode != 0:
        return None
    return completed.stdout.strip()


def write_json(path: str, payload: dict[str, Any]) -> None:
    output = Path(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def base_metadata(engine: str, config: str | None = DEFAULT_CONFIG) -> dict[str, Any]:
    return {
        "engine": engine,
        "engine_version": engine_version(engine),
        "git_commit": git_commit(),
        "config": {
            "path": config,
            "sha256": file_sha256(config) if config else None,
        },
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def timed(call):
    start = time.perf_counter()
    value = call()
    elapsed = time.perf_counter() - start
    return value, elapsed
