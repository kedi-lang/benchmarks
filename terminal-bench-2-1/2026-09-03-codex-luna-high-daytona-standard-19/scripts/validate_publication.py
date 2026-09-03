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
    "accepted_trials": 18,
    "rejected_trials": 1,
    "all_trials": 19,
    "reward": Decimal("11"),
    "autobench_passed": 8,
    "autobench_failed": 11,
    "usage_measured_trials": 14,
    "cost_usd": Decimal("4.37852572"),
    "requests": 659,
    "tool_calls": 972,
    "input_tokens": 44_370_227,
    "cache_read_tokens": 26_459_136,
    "output_tokens": 222_604,
    "omitted_oversized_files": 0,
}
EXPECTED_EXCEPTIONS = {
    "make-doom-for-mips__TbPXyau": "AgentTimeoutError",
    "train-fasttext__CmHht4h": "AgentTimeoutError",
    "winning-avg-corewars__3okytfk": "RuntimeError",
}
FORBIDDEN_PATTERNS = (
    re.compile(rb"/" + rb"Users/[^/\s]+"),
    re.compile(rb"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(rb"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(rb"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(rb"Bearer\s+[A-Za-z0-9._~+/-]{16,}", re.I),
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)
SENSITIVE_FILENAMES = frozenset(
    {".env", ".envrc", "credentials", "credentials.json", "id_rsa", "id_ed25519"}
)


def _metric(run: Any, name: str) -> Any | None:
    for observation in run.task_result.observations:
        if observation.kind == "metric" and observation.name == name:
            return observation.value
    return None


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
    accepted_ids = {
        trial["trial_id"]
        for job in index["jobs"]
        for trial in job["accepted_trials"]
    }
    rejected_ids = {
        trial["trial_id"]
        for job in index["jobs"]
        for trial in job["rejected_trials"]
    }
    assert len(accepted_ids) == EXPECTED["accepted_trials"]
    assert len(rejected_ids) == EXPECTED["rejected_trials"]
    assert len(accepted_ids | rejected_ids) == EXPECTED["all_trials"]

    totals: dict[str, int | Decimal] = {
        "reward": Decimal("0"),
        "cost_usd": Decimal("0"),
        "requests": 0,
        "tool_calls": 0,
        "input_tokens": 0,
        "cache_read_tokens": 0,
        "output_tokens": 0,
    }
    statuses: dict[str, int] = {}
    observed_trials: set[str] = set()
    usage_measured_trials = 0
    records = sorted((evidence / "autobench").iterdir())
    assert len(records) == 1
    experiment = replay_experiment(records[0])
    for run in experiment.runs:
        output = run.task_result.output
        if not isinstance(output, dict):
            raise AssertionError(f"unexpected task output for {run.case_id!r}")
        trial_id = output["trial_name"]
        observed_trials.add(trial_id)
        status = str(run.status)
        statuses[status] = statuses.get(status, 0) + 1

        exception = output.get("harbor_exception")
        assert exception == EXPECTED_EXCEPTIONS.get(trial_id), (
            trial_id,
            exception,
        )
        reward = _metric(run, "terminal_bench.reward.reward")
        if trial_id in accepted_ids:
            assert reward is not None, f"accepted trial lacks reward: {trial_id}"
            totals["reward"] += Decimal(str(reward))
        else:
            assert trial_id in rejected_ids
            assert reward is None, f"rejected trial unexpectedly has reward: {trial_id}"

        cost = _metric(run, "kedi.cost_usd")
        if cost is None:
            continue
        usage_measured_trials += 1
        totals["cost_usd"] += Decimal(str(cost))
        for total_name, metric_name in (
            ("requests", "kedi.requests"),
            ("tool_calls", "kedi.tool_calls"),
            ("input_tokens", "kedi.input_tokens"),
            ("cache_read_tokens", "kedi.cache_read_tokens"),
            ("output_tokens", "kedi.output_tokens"),
        ):
            value = _metric(run, metric_name)
            assert value is not None, f"partial usage metrics in {trial_id}"
            totals[total_name] += int(value)

    assert observed_trials == accepted_ids | rejected_ids
    assert statuses == {
        "passed": EXPECTED["autobench_passed"],
        "failed": EXPECTED["autobench_failed"],
    }
    assert usage_measured_trials == EXPECTED["usage_measured_trials"]
    for name, actual in totals.items():
        assert actual == EXPECTED[name], f"{name}: {actual!r} != {EXPECTED[name]!r}"

    sanitization = json.loads(
        (evidence / "sanitization-report.json").read_text(encoding="utf-8")
    )
    omitted = sanitization["skipped_oversized_files"]
    assert len(omitted) == EXPECTED["omitted_oversized_files"]
    known_secrets = _known_secrets(dotenv)
    file_count = 0
    byte_count = 0
    largest_file = 0
    for path in root.rglob("*"):
        assert not path.is_symlink(), f"symlink in publication bundle: {path}"
        if not path.is_file():
            continue
        assert path.name.lower() not in SENSITIVE_FILENAMES, path
        payload = path.read_bytes()
        file_count += 1
        byte_count += len(payload)
        largest_file = max(largest_file, len(payload))
        for pattern in FORBIDDEN_PATTERNS:
            assert pattern.search(payload) is None, f"sensitive pattern in {path}"
        for secret in known_secrets:
            assert secret not in payload, f"known secret in {path}"
    assert largest_file <= 20_000_000

    return {
        "accepted_trials": len(accepted_ids),
        "rejected_trials": len(rejected_ids),
        "reward": str(totals["reward"]),
        "usage_measured_trials": usage_measured_trials,
        "cost_usd": str(totals["cost_usd"]),
        "file_count": file_count,
        "bytes": byte_count,
        "largest_file": largest_file,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parents[1],
    )
    parser.add_argument("--dotenv", type=Path)
    args = parser.parse_args()
    result = validate(
        args.root.expanduser().resolve(),
        dotenv=None if args.dotenv is None else args.dotenv.expanduser().resolve(),
    )
    print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
