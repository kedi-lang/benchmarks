#!/usr/bin/env python3
"""Replay and validate the Full89 public evidence package."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from autobench import replay_experiment


EXPECTED = {
    "trials": 89,
    "passed": 68,
    "failed": 21,
    "cost_usd": Decimal("4.93781512"),
    "input_tokens": 119_974_598,
    "cache_read_tokens": 113_355_776,
    "output_tokens": 1_122_446,
    "requests": 3_121,
    "tool_calls": 3_800,
}
FORBIDDEN_PATTERNS = (
    re.compile(rb"/" + rb"Users/[^/\s]+"),
    re.compile(rb"/opt/" + rb"kedi-private(?:/[^\s]+)?"),
    re.compile(rb"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(rb"(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{16,}"),
    re.compile(rb"Bearer\s+[A-Za-z0-9._~+/-]{16,}", re.I),
    re.compile(rb"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}"),
    re.compile(rb"\b[0-9]{6,12}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.I),
)
SENSITIVE_FILENAMES = frozenset(
    {".env", ".envrc", ".netrc", "auth.json", "credentials", "credentials.json", "id_rsa", "id_ed25519"}
)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


def metric(run: Any, name: str) -> Any:
    for observation in run.task_result.observations:
        if observation.name == name:
            return observation.value
    return None


def known_secrets(dotenv: Path | None) -> tuple[bytes, ...]:
    if dotenv is None or not dotenv.is_file():
        return ()
    names = re.compile(
        r"(?:api.?key|authorization|credential|password|secret|access.?token|refresh.?token|id.?token|session.?token|bot.?token)",
        re.I,
    )
    values = []
    for raw_line in dotenv.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, raw_value = line.split("=", 1)
        value = raw_value.strip().strip("'\"")
        if names.search(name) and len(value) >= 8:
            values.append(value.encode())
    return tuple(values)


def validate(root: Path, dotenv: Path | None) -> dict[str, Any]:
    index = json.loads((root / "evidence" / "index.json").read_text(encoding="utf-8"))
    assert len(index["trials"]) == EXPECTED["trials"]
    assert len({entry["task_name"] for entry in index["trials"]}) == EXPECTED["trials"]
    experiment = replay_experiment(root / "evidence" / "autobench" / "full89")
    assert len(experiment.runs) == EXPECTED["trials"]
    observed_trials: set[str] = set()
    totals: dict[str, int | Decimal] = {
        "cost_usd": Decimal("0"),
        "input_tokens": 0,
        "cache_read_tokens": 0,
        "output_tokens": 0,
        "requests": 0,
        "tool_calls": 0,
    }
    passed = 0
    for run in experiment.runs:
        output = run.task_result.output
        observed_trials.add(output["trial_name"])
        reward = Decimal(str(metric(run, "terminal_bench.reward.reward")))
        passed += reward == 1
        totals["cost_usd"] += Decimal(str(metric(run, "kedi.cost_usd")))
        for total_name, metric_name in (
            ("input_tokens", "kedi.input_tokens"),
            ("cache_read_tokens", "kedi.cache_read_tokens"),
            ("output_tokens", "kedi.output_tokens"),
            ("requests", "kedi.requests"),
            ("tool_calls", "kedi.tool_calls"),
        ):
            totals[total_name] += int(metric(run, metric_name))
    assert observed_trials == {entry["trial_id"] for entry in index["trials"]}
    assert passed == EXPECTED["passed"]
    assert len(experiment.runs) - passed == EXPECTED["failed"]
    for name, expected in EXPECTED.items():
        if name not in {"trials", "passed", "failed"}:
            assert totals[name] == expected, f"{name}: {totals[name]!r} != {expected!r}"

    checksum_path = root / "checksums.sha256"
    declared: dict[str, str] = {}
    for line in checksum_path.read_text(encoding="utf-8").splitlines():
        expected_digest, relative = line.split("  ", 1)
        declared[relative] = expected_digest
    actual_files = {
        path.relative_to(root).as_posix(): path
        for path in root.rglob("*")
        if path.is_file() and not path.is_symlink() and path != checksum_path
    }
    assert set(declared) == set(actual_files), "checksum manifest does not match publication files"
    for relative, path in actual_files.items():
        assert digest(path) == declared[relative], f"checksum mismatch: {relative}"

    secrets = known_secrets(dotenv)
    largest_file = 0
    total_bytes = 0
    for path in root.rglob("*"):
        assert not path.is_symlink(), f"symlink in publication: {path}"
        if not path.is_file():
            continue
        lower_name = path.name.lower()
        assert lower_name not in SENSITIVE_FILENAMES and not lower_name.startswith(".env."), path
        payload = path.read_bytes()
        largest_file = max(largest_file, len(payload))
        total_bytes += len(payload)
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern.search(payload) is None, f"sensitive pattern in {path}"
        for secret in secrets:
            assert secret not in payload, f"known secret in {path}"
    assert largest_file <= 20_000_000
    return {
        "trials": len(experiment.runs),
        "passed": passed,
        "failed": len(experiment.runs) - passed,
        "cost_usd": str(totals["cost_usd"]),
        "cache_read_ratio": totals["cache_read_tokens"] / totals["input_tokens"],
        "files": len(actual_files) + 1,
        "bytes": total_bytes,
        "largest_file": largest_file,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--dotenv", type=Path)
    options = parser.parse_args()
    result = validate(
        options.root.expanduser().resolve(),
        None if options.dotenv is None else options.dotenv.expanduser().resolve(),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
