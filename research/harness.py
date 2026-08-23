from __future__ import annotations

import hashlib
import json
import os
import platform
import random
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_CONFIG = "configs/default.json"


def utc_id(prefix: str = "experiment") -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{prefix}"


def file_sha256(path: str | None) -> str | None:
    if not path or not Path(path).is_file():
        return None
    data = Path(path).read_bytes()
    return hashlib.sha256(data).hexdigest()


def file_metadata(path: str | None, *, count_nonempty_lines: bool = False) -> dict[str, Any] | None:
    """Return reproducibility metadata for a file without assuming it exists."""
    if not path:
        return None
    resolved = Path(path).resolve()
    result: dict[str, Any] = {
        "path": str(resolved),
        "exists": resolved.is_file(),
        "sha256": file_sha256(str(resolved)),
    }
    if resolved.is_file():
        result["size_bytes"] = resolved.stat().st_size
        if count_nonempty_lines:
            entries = [
                line.strip()
                for line in resolved.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            # EPD position identity is its first four whitespace-separated FEN
            # fields. Operations after those fields must not inflate diversity.
            position_keys = [
                " ".join(entry.split()[:4]) if len(entry.split()) >= 4 else entry
                for entry in entries
            ]
            result["nonempty_lines"] = len(entries)
            result["unique_nonempty_lines"] = len(set(entries))
            result["duplicate_nonempty_lines"] = len(entries) - len(set(entries))
            result["unique_positions"] = len(set(position_keys))
            result["duplicate_positions"] = len(entries) - len(set(position_keys))
    return result


def prepare_opening_schedule(
    source: str, destination: str, *, pairs: int, seed: int
) -> dict[str, Any]:
    """Write deterministic IID-with-replacement EPD schedule for opening pairs."""
    if pairs <= 0:
        raise ValueError("pairs must be positive")
    source_path = Path(source).resolve()
    entries = [
        line.strip()
        for line in source_path.read_text(encoding="utf-8", errors="replace").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    population: dict[str, str] = {}
    for entry in entries:
        fields = entry.split()
        key = " ".join(fields[:4]) if len(fields) >= 4 else entry
        population.setdefault(key, entry)
    if not population:
        raise ValueError("opening source contains no positions")
    rng = random.Random(seed)
    values = list(population.values())
    scheduled = [rng.choice(values) for _ in range(pairs)]
    destination_path = Path(destination).resolve()
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    destination_path.write_text("\n".join(scheduled) + "\n", encoding="utf-8")
    return {
        "sampling": "iid_with_replacement_from_unique_epd_positions",
        "rng": "python_random_mt19937",
        "seed": seed,
        "pairs": pairs,
        "population_positions": len(values),
        "source": file_metadata(str(source_path), count_nonempty_lines=True),
        "schedule": file_metadata(str(destination_path), count_nonempty_lines=True),
    }


def _resolve_engine(engine: str) -> str:
    # Python 3.14 on Windows no longer resolves relative executable paths against
    # cwd, so make any real file path absolute before handing it to subprocess.
    p = Path(engine)
    return str(p.resolve()) if p.exists() else engine


def run_engine(engine: str, args: list[str], config: str | None = DEFAULT_CONFIG, timeout: float = 10.0) -> subprocess.CompletedProcess[str]:
    engine = _resolve_engine(engine)
    command = [engine]
    if config:
        command += ["--config", config]
    command += args
    return subprocess.run(command, check=False, capture_output=True, text=True, timeout=timeout)


def engine_version(engine: str) -> str:
    try:
        completed = subprocess.run(
            [_resolve_engine(engine), "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    if completed.returncode != 0:
        return "unknown"
    output = (completed.stdout or completed.stderr).strip()
    return output.splitlines()[0] if output else "unknown"


def command_version(executable: str, *args: str) -> str:
    """Best-effort version capture for third-party match tools and engines."""
    try:
        completed = subprocess.run(
            [_resolve_engine(executable), *(args or ("--version",))],
            check=False,
            capture_output=True,
            text=True,
            timeout=5.0,
        )
    except (OSError, subprocess.TimeoutExpired):
        return "unknown"
    output = (completed.stdout or completed.stderr).strip()
    return output.splitlines()[0] if output else "unknown"


def executable_metadata(executable: str, *, version: str | None = None) -> dict[str, Any]:
    """Identify an executable by resolved path, content hash, size, and version."""
    resolved = _resolve_engine(executable)
    metadata = file_metadata(resolved) or {"path": resolved, "exists": False, "sha256": None}
    metadata["version"] = version if version is not None else engine_version(resolved)
    return metadata


def environment_metadata() -> dict[str, Any]:
    """Capture host facts that can affect timed engine measurements."""
    return {
        "platform": platform.platform(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "logical_cpus": os.cpu_count(),
        "python": sys.version.split()[0],
    }


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
    resolved_engine = _resolve_engine(engine)
    version = engine_version(resolved_engine)
    return {
        "schema_version": 2,
        "engine": engine,
        "engine_version": version,
        "engine_artifact": executable_metadata(resolved_engine, version=version),
        "git_commit": git_commit(),
        "config": file_metadata(config),
        "environment": environment_metadata(),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def timed(call):
    start = time.perf_counter()
    value = call()
    elapsed = time.perf_counter() - start
    return value, elapsed
