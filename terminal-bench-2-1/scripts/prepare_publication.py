#!/usr/bin/env python3
"""Create sanitized public Harbor evidence without mutating source records."""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class JobSpec:
    name: str
    kedi_revision: str
    accepted: tuple[str, ...]
    rejected: tuple[tuple[str, str], ...] = ()


JOBS = (
    JobSpec(
        name="codex-luna-high-pilot9-docker-e82d540-c2-logfire",
        kedi_revision="e82d540c8142ed46bf4e58e9f8c43c5b8fc660ac",
        accepted=("log-summary-date-ranges__AWTMMo5", "pypi-server__q9VYLU7"),
        rejected=(
            (
                "build-cython-ext__qu5L5yi",
                "invalid harness attempt: task-root containment rejected /tmp",
            ),
        ),
    ),
    JobSpec(
        name="codex-luna-high-continuation7-docker-c7c3fc9-c2-logfire",
        kedi_revision="c7c3fc9289731422f551619528cb2073b1d325f1",
        accepted=("qemu-startup__wqXbSqH", "sqlite-db-truncate__36PCAS2"),
        rejected=(
            (
                "build-cython-ext__4seSYZ3",
                "invalid harness attempt: cache reads exhausted the host input budget",
            ),
        ),
    ),
    JobSpec(
        name="codex-luna-high-remaining5-docker-69ad944-c2-logfire",
        kedi_revision="69ad944735b067ede7393f5c83a3263b591ffc2c",
        accepted=(
            "build-cython-ext__Ef3ngqy",
            "cancel-async-tasks__9pVfzSd",
            "fix-git__pb7YYoQ",
            "large-scale-text-editing__TbsLtsF",
            "polyglot-c-py__p5E8Ubx",
        ),
    ),
)

SECRET_KEY = re.compile(
    r"(?:^|[_-])(?:api[_-]?key|auth(?:orization)?|credential(?:s)?|password|secret|token)(?:$|[_-])",
    re.I,
)
TOKEN_PATTERNS = (
    re.compile(r"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(r"github_pat_[A-Za-z0-9_]{20,}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/-]{16,}", re.I),
    re.compile(
        r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
        re.S,
    ),
)
SENSITIVE_FILENAMES = frozenset(
    {".env", ".envrc", "credentials", "credentials.json", "id_rsa", "id_ed25519"}
)


class Sanitizer:
    def __init__(self, *, source_root: Path, dotenv: Path | None) -> None:
        self._replacements: list[tuple[str, str]] = [
            (str(source_root.resolve()), "<KEDI_WORKSPACE>"),
            (str(Path.home().resolve()), "<HOME>"),
        ]
        self._secret_values = self._load_secret_values(dotenv)
        self.replacement_count = 0
        self.skipped_symlinks = 0
        self.skipped_sensitive_files = 0

    def text(self, value: str) -> str:
        sanitized = value
        replacements = sorted(
            (
                *self._replacements,
                *((secret, "<REDACTED_SECRET>") for secret in self._secret_values),
            ),
            key=lambda item: len(item[0]),
            reverse=True,
        )
        for original, replacement in replacements:
            if original and original in sanitized:
                count = sanitized.count(original)
                sanitized = sanitized.replace(original, replacement)
                self.replacement_count += count
        for pattern in TOKEN_PATTERNS:
            sanitized, count = pattern.subn("<REDACTED_SECRET>", sanitized)
            self.replacement_count += count
        return sanitized

    def json_value(self, value: Any, *, key: str | None = None) -> Any:
        if key is not None and SECRET_KEY.search(key):
            self.replacement_count += 1
            return "<REDACTED_SECRET>"
        if isinstance(value, dict):
            return {str(name): self.json_value(item, key=str(name)) for name, item in value.items()}
        if isinstance(value, list):
            return [self.json_value(item) for item in value]
        if isinstance(value, str):
            return self.text(value)
        return value

    @staticmethod
    def _load_secret_values(dotenv: Path | None) -> frozenset[str]:
        values: set[str] = set()
        if dotenv is not None and dotenv.is_file():
            for raw_line in dotenv.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                _, raw_value = line.split("=", 1)
                value = raw_value.strip().strip("'\"")
                if len(value) >= 8:
                    values.add(value)
        for name, value in os.environ.items():
            if SECRET_KEY.search(name) and len(value) >= 8:
                values.add(value)
        return frozenset(values)


def _looks_like_text(payload: bytes) -> bool:
    if b"\x00" in payload[:8192]:
        return False
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def _copy_job(source: Path, target: Path, sanitizer: Sanitizer) -> dict[str, int]:
    files = 0
    bytes_written = 0
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        destination = target / relative
        if path.is_symlink():
            sanitizer.skipped_symlinks += 1
            continue
        if path.is_dir():
            destination.mkdir(parents=True, exist_ok=True)
            continue
        if not path.is_file():
            continue
        lower_name = path.name.lower()
        if (
            lower_name in SENSITIVE_FILENAMES
            or lower_name.startswith(".env.")
            or path.suffix.lower() in {".key", ".pem"}
        ):
            sanitizer.skipped_sensitive_files += 1
            continue
        payload = path.read_bytes()
        destination.parent.mkdir(parents=True, exist_ok=True)
        if not _looks_like_text(payload):
            destination.write_bytes(payload)
        else:
            text = payload.decode("utf-8")
            if path.suffix.lower() == ".json":
                try:
                    parsed = json.loads(text)
                except json.JSONDecodeError:
                    sanitized = sanitizer.text(text)
                else:
                    sanitized = (
                        json.dumps(
                            sanitizer.json_value(parsed),
                            ensure_ascii=False,
                            indent=2,
                            sort_keys=True,
                        )
                        + "\n"
                    )
            else:
                sanitized = sanitizer.text(text)
            destination.write_text(sanitized, encoding="utf-8")
        files += 1
        bytes_written += destination.stat().st_size
    return {"files": files, "bytes": bytes_written}


def _trial_entry(job: Path, trial_id: str, *, status: str, reason: str | None) -> dict[str, Any]:
    result = json.loads((job / trial_id / "result.json").read_text(encoding="utf-8"))
    rewards = (result.get("verifier_result") or {}).get("rewards") or {}
    exception = result.get("exception_info") or {}
    return {
        "trial_id": trial_id,
        "task_name": result.get("task_name"),
        "status": status,
        "reason": reason,
        "rewards": rewards,
        "exception_type": exception.get("exception_type"),
    }


def prepare(source_root: Path, output_root: Path, *, dotenv: Path | None) -> None:
    if output_root.exists():
        raise FileExistsError(f"output already exists: {output_root}")
    source_jobs = source_root / "tmp" / "terminal-bench-2.1" / "jobs"
    sanitizer = Sanitizer(source_root=source_root, dotenv=dotenv)
    jobs_output = output_root / "harbor"
    jobs_output.mkdir(parents=True)
    index_jobs: list[dict[str, Any]] = []
    copy_stats: dict[str, dict[str, int]] = {}

    for spec in JOBS:
        source = source_jobs / spec.name
        if not source.is_dir():
            raise FileNotFoundError(f"Harbor job is missing: {source}")
        target = jobs_output / spec.name
        target.mkdir()
        copy_stats[spec.name] = _copy_job(source, target, sanitizer)
        rejected = dict(spec.rejected)
        observed = {path.parent.name for path in source.glob("*/result.json")}
        declared = set(spec.accepted) | set(rejected)
        if observed != declared:
            raise ValueError(
                f"trial boundary changed for {spec.name}: observed={sorted(observed)!r}, "
                f"declared={sorted(declared)!r}"
            )
        index_jobs.append(
            {
                "job_name": spec.name,
                "kedi_revision": spec.kedi_revision,
                "accepted_trials": [
                    _trial_entry(source, trial, status="accepted", reason=None)
                    for trial in spec.accepted
                ],
                "rejected_trials": [
                    _trial_entry(source, trial, status="rejected", reason=reason)
                    for trial, reason in spec.rejected
                ],
            }
        )

    index = {
        "schema_version": 1,
        "scope": "multi-revision dogfood aggregate; not an official leaderboard run",
        "accepted_trial_count": sum(len(spec.accepted) for spec in JOBS),
        "rejected_trial_count": sum(len(spec.rejected) for spec in JOBS),
        "jobs": index_jobs,
    }
    (output_root / "index.json").write_text(
        json.dumps(index, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = {
        "schema_version": 1,
        "jobs": copy_stats,
        "replacement_count": sanitizer.replacement_count,
        "skipped_sensitive_files": sanitizer.skipped_sensitive_files,
        "skipped_symlinks": sanitizer.skipped_symlinks,
    }
    (output_root / "sanitization-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-root", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dotenv", type=Path)
    args = parser.parse_args()
    prepare(
        args.source_root.expanduser().resolve(),
        args.output_root.expanduser().resolve(),
        dotenv=None if args.dotenv is None else args.dotenv.expanduser().resolve(),
    )


if __name__ == "__main__":
    main()
