#!/usr/bin/env python3
"""Replay and validate the public Terminal-Bench evidence package."""

from __future__ import annotations

import argparse
import json
import re
from decimal import Decimal
from pathlib import Path
from typing import Any

from autobench import replay_experiment


EXPECTED = {
    "accepted_trials": 9,
    "all_trials": 11,
    "reward": 6,
    "cost_usd": Decimal("0.32662052"),
    "requests": 193,
    "tool_calls": 335,
    "input_tokens": 3_731_773,
    "cache_read_tokens": 2_681_216,
    "output_tokens": 52_404,
}
FORBIDDEN_PATTERNS = (
    re.compile(rb"/Users/[^/\s]+"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(rb"Bearer\s+[A-Za-z0-9._~+/-]{16,}", re.I),
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
SENSITIVE_FILENAMES = frozenset(
    {".env", ".envrc", "credentials", "credentials.json", "id_rsa", "id_ed25519"}
)


def _metric(run: Any, name: str) -> Any:
    for observation in run.task_result.observations:
        if observation.kind == "metric" and observation.name == name:
            return observation.value
    raise AssertionError(f"missing metric {name!r} in {run.case_id!r}")


def _known_secrets(dotenv: Path | None) -> tuple[bytes, ...]:
    if dotenv is None:
        return ()
    values: list[bytes] = []
    for raw_line in dotenv.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        value = line.split("=", 1)[1].strip().strip("'\"")
        if len(value) >= 8:
            values.append(value.encode())
    return tuple(values)


def validate(root: Path, *, dotenv: Path | None) -> dict[str, Any]:
    evidence = root / "evidence"
    index = json.loads((evidence / "index.json").read_text(encoding="utf-8"))
    accepted_ids = {trial["trial_id"] for job in index["jobs"] for trial in job["accepted_trials"]}
    rejected_ids = {trial["trial_id"] for job in index["jobs"] for trial in job["rejected_trials"]}
    assert len(accepted_ids) == EXPECTED["accepted_trials"]
    assert len(accepted_ids | rejected_ids) == EXPECTED["all_trials"]

    totals: dict[str, int | Decimal] = {
        "reward": 0,
        "cost_usd": Decimal("0"),
        "requests": 0,
        "tool_calls": 0,
        "input_tokens": 0,
        "cache_read_tokens": 0,
        "output_tokens": 0,
    }
    observed_trials: set[str] = set()
    replayed_records = 0
    for record in sorted((evidence / "autobench").iterdir()):
        experiment = replay_experiment(record)
        replayed_records += 1
        for run in experiment.runs:
            output = run.task_result.output
            if not isinstance(output, dict):
                raise AssertionError(f"unexpected task output for {run.case_id!r}")
            trial_id = output["trial_name"]
            observed_trials.add(trial_id)
            if trial_id not in accepted_ids:
                continue
            assert run.status == "passed"
            assert output.get("harbor_exception") is None
            assert output["kedi_state"] == "completed"
            totals["reward"] += int(_metric(run, "terminal_bench.reward.reward"))
            totals["cost_usd"] += Decimal(str(_metric(run, "kedi.cost_usd")))
            for total_name, metric_name in (
                ("requests", "kedi.requests"),
                ("tool_calls", "kedi.tool_calls"),
                ("input_tokens", "kedi.input_tokens"),
                ("cache_read_tokens", "kedi.cache_read_tokens"),
                ("output_tokens", "kedi.output_tokens"),
            ):
                totals[total_name] += int(_metric(run, metric_name))
    assert replayed_records == 3
    assert observed_trials == accepted_ids | rejected_ids
    for name, expected in EXPECTED.items():
        if name not in totals:
            continue
        assert totals[name] == expected, f"{name}: {totals[name]!r} != {expected!r}"

    known_secrets = _known_secrets(dotenv)
    file_count = 0
    byte_count = 0
    largest_file = 0
    for path in evidence.rglob("*"):
        if not path.is_file():
            continue
        file_count += 1
        payload = path.read_bytes()
        byte_count += len(payload)
        largest_file = max(largest_file, len(payload))
        lower_name = path.name.lower()
        assert lower_name not in SENSITIVE_FILENAMES
        assert not lower_name.startswith(".env.")
        assert path.suffix.lower() not in {".key", ".pem"}
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern.search(payload) is None, f"forbidden value in {path}"
        for secret in known_secrets:
            assert secret not in payload, f"known dotenv value in {path}"
    assert largest_file < 100_000_000

    return {
        "accepted_trials": len(accepted_ids),
        "all_trials": len(observed_trials),
        "autobench_records": replayed_records,
        "evidence_bytes": byte_count,
        "evidence_files": file_count,
        "largest_file_bytes": largest_file,
        **{
            name: str(value) if isinstance(value, Decimal) else value
            for name, value in totals.items()
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--dotenv", type=Path)
    args = parser.parse_args()
    summary = validate(
        args.root.expanduser().resolve(),
        dotenv=None if args.dotenv is None else args.dotenv.expanduser().resolve(),
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
