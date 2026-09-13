#!/usr/bin/env python3
"""Create a sanitized, immutable publication copy of the Full89 run."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from pathlib import Path
from typing import Any


BATCHES = {
    "standard81-c2": "daytona-luna-high-full89-c2-c1-20260912-standard81-c2",
    "high-memory8-c1": "daytona-luna-high-full89-c2-c1-20260912-high-memory8-c1",
}
MANIFEST_FILES = (
    "manifest.json",
    "experiment-contract.json",
    "expected-sources.json",
    "config-standard81-c2.json",
    "config-high-memory8-c1.json",
)
SECRET_KEY = re.compile(
    r"(?:^|[_-])(?:api[_-]?key|authorization|credentials?|password|secret|"
    r"access[_-]?token|refresh[_-]?token|id[_-]?token|session[_-]?token|"
    r"bot[_-]?token|auth[_-]?(?:file|json|token))(?:$|[_-])",
    re.I,
)
TOKEN_PATTERNS = (
    re.compile(rb"sk-[A-Za-z0-9_-]{16,}"),
    re.compile(rb"(?:github_pat_|gh[pousr]_)[A-Za-z0-9_]{16,}"),
    re.compile(rb"Bearer\s+[A-Za-z0-9._~+/-]{16,}", re.I),
    re.compile(rb"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{8,}"),
    re.compile(rb"\b[0-9]{6,12}:[A-Za-z0-9_-]{20,}\b"),
    re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----", re.I),
)
SENSITIVE_FILENAMES = frozenset(
    {
        ".env",
        ".envrc",
        ".netrc",
        "auth.json",
        "cookies.json",
        "credentials",
        "credentials.json",
        "id_ed25519",
        "id_rsa",
    }
)
MAX_PUBLIC_FILE_BYTES = 20_000_000


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def looks_like_text(payload: bytes) -> bool:
    if b"\x00" in payload[:8192]:
        return False
    try:
        payload.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


class Sanitizer:
    def __init__(self, source_run: Path, dotenv: Path | None) -> None:
        self._replacements = (
            (str(source_run.resolve()), "<SOURCE_RUN>"),
            (str(Path.home().resolve()), "<HOME>"),
            ("/opt/" + "kedi-private", "<PRIVATE_RUNTIME>"),
            ("/opt/kedi-full89-20260912", "<REMOTE_RUN>"),
        )
        self._secret_values = self._load_secret_values(dotenv)
        self.replacement_count = 0
        self.skipped_sensitive_files: list[str] = []
        self.skipped_sensitive_binary_files: list[dict[str, Any]] = []
        self.skipped_oversized_files: list[dict[str, Any]] = []
        self.skipped_symlinks: list[str] = []

    @staticmethod
    def _load_secret_values(dotenv: Path | None) -> tuple[bytes, ...]:
        values: set[bytes] = set()
        if dotenv is not None and dotenv.is_file():
            for raw_line in dotenv.read_text(encoding="utf-8").splitlines():
                line = raw_line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                name, raw_value = line.split("=", 1)
                value = raw_value.strip().strip("'\"")
                if SECRET_KEY.search(name.strip()) and len(value) >= 8:
                    values.add(value.encode())
        for name, value in os.environ.items():
            if SECRET_KEY.search(name) and len(value) >= 8:
                values.add(value.encode())
        return tuple(sorted(values, key=len, reverse=True))

    def bytes_contain_secret(self, payload: bytes) -> bool:
        return any(value in payload for value in self._secret_values) or any(
            pattern.search(payload) is not None for pattern in TOKEN_PATTERNS
        )

    def text(self, value: str) -> str:
        sanitized = value
        for original, replacement in sorted(self._replacements, key=lambda item: -len(item[0])):
            if original and original in sanitized:
                self.replacement_count += sanitized.count(original)
                sanitized = sanitized.replace(original, replacement)
        payload = sanitized.encode()
        for secret in self._secret_values:
            count = payload.count(secret)
            if count:
                payload = payload.replace(secret, b"<REDACTED_SECRET>")
                self.replacement_count += count
        for pattern in TOKEN_PATTERNS:
            payload, count = pattern.subn(b"<REDACTED_SECRET>", payload)
            self.replacement_count += count
        return payload.decode("utf-8")

    def json_value(self, value: Any, *, key: str | None = None) -> Any:
        if key is not None and SECRET_KEY.search(key):
            self.replacement_count += 1
            return "<REDACTED_SECRET>"
        if isinstance(value, dict):
            return {
                str(name): self.json_value(item, key=str(name))
                for name, item in value.items()
            }
        if isinstance(value, list):
            return [self.json_value(item) for item in value]
        if isinstance(value, str):
            return self.text(value)
        return value

    def copy_file(self, source: Path, target: Path, *, display_path: str) -> bool:
        lower_name = source.name.lower()
        if (
            lower_name in SENSITIVE_FILENAMES
            or lower_name.startswith(".env.")
            or source.suffix.lower() in {".key", ".pem"}
        ):
            self.skipped_sensitive_files.append(display_path)
            return False
        size = source.stat().st_size
        if size > MAX_PUBLIC_FILE_BYTES:
            self.skipped_oversized_files.append(
                {"path": display_path, "bytes": size, "sha256": sha256(source)}
            )
            return False
        payload = source.read_bytes()
        target.parent.mkdir(parents=True, exist_ok=True)
        if not looks_like_text(payload):
            if self.bytes_contain_secret(payload):
                self.skipped_sensitive_binary_files.append(
                    {"path": display_path, "bytes": size, "sha256": sha256(source)}
                )
                return False
            target.write_bytes(payload)
            return True
        text = payload.decode("utf-8")
        if source.suffix.lower() == ".json":
            try:
                value = json.loads(text)
            except json.JSONDecodeError:
                sanitized = self.text(text)
            else:
                sanitized = json.dumps(
                    self.json_value(value),
                    ensure_ascii=False,
                    indent=2,
                    sort_keys=True,
                ) + "\n"
        else:
            sanitized = self.text(text)
        target.write_text(sanitized, encoding="utf-8")
        return True


def trial_entry(batch: str, trial: Path) -> dict[str, Any]:
    result = json.loads((trial / "result.json").read_text(encoding="utf-8"))
    reward = ((result.get("verifier_result") or {}).get("rewards") or {}).get("reward")
    agent = result.get("agent_result") or {}
    exception = result.get("exception_info") or {}
    return {
        "batch": batch,
        "trial_id": trial.name,
        "task_name": str(result.get("task_name") or trial.name.split("__", 1)[0]).removeprefix(
            "terminal-bench/"
        ),
        "reward": reward,
        "exception_type": exception.get("exception_type"),
        "duration_seconds": result.get("duration_seconds"),
        "started_at": result.get("started_at"),
        "finished_at": result.get("finished_at"),
        "cost_usd": agent.get("cost_usd"),
        "input_tokens": agent.get("n_input_tokens"),
        "cache_read_tokens": agent.get("n_cache_tokens"),
        "output_tokens": agent.get("n_output_tokens"),
    }


def copy_tree(source: Path, target: Path, sanitizer: Sanitizer, *, prefix: str) -> dict[str, int]:
    files = 0
    byte_count = 0
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        display = f"{prefix}/{relative.as_posix()}"
        if path.is_symlink():
            sanitizer.skipped_symlinks.append(display)
            continue
        if path.is_dir():
            continue
        if not path.is_file():
            continue
        destination = target / relative
        if sanitizer.copy_file(path, destination, display_path=display):
            files += 1
            byte_count += destination.stat().st_size
    return {"files": files, "bytes": byte_count}


def prepare(source_run: Path, output_root: Path, dotenv: Path | None) -> None:
    if (output_root / "evidence").exists() or any(
        (output_root / "manifests" / name).exists() for name in MANIFEST_FILES
    ):
        raise FileExistsError(f"publication payload already exists: {output_root}")
    source_evidence = source_run / "analysis-evidence"
    source_jobs = source_evidence / "jobs"
    if not source_jobs.is_dir():
        raise FileNotFoundError(source_jobs)
    sanitizer = Sanitizer(source_run, dotenv)
    output_root.mkdir(parents=True, exist_ok=True)
    manifests = output_root / "manifests"
    manifests.mkdir(exist_ok=True)
    for name in MANIFEST_FILES:
        source = source_run / name
        if not source.is_file():
            raise FileNotFoundError(source)
        sanitizer.copy_file(source, manifests / name, display_path=f"manifests/{name}")

    entries: list[dict[str, Any]] = []
    copy_stats: dict[str, dict[str, int]] = {}
    for batch, job_name in BATCHES.items():
        source_job = source_jobs / job_name
        if not source_job.is_dir():
            raise FileNotFoundError(source_job)
        trials = sorted(path.parent for path in source_job.glob("*/result.json"))
        entries.extend(trial_entry(batch, trial) for trial in trials)
        target_job = output_root / "evidence" / "harbor" / job_name
        target_job.mkdir(parents=True)
        copy_stats[batch] = copy_tree(
            source_job,
            target_job,
            sanitizer,
            prefix=f"evidence/harbor/{job_name}",
        )

    task_names = [entry["task_name"] for entry in entries]
    if len(entries) != 89 or len(set(task_names)) != 89:
        raise RuntimeError(
            f"expected 89 unique tasks, observed {len(entries)} trials/{len(set(task_names))} tasks"
        )
    index = {
        "schema_version": 1,
        "experiment_id": "daytona-luna-high-full89-c2-c1-20260912",
        "scope": "89 unique Terminal-Bench 2.1 tasks, one trial per task",
        "batches": BATCHES,
        "trials": sorted(entries, key=lambda entry: entry["task_name"]),
    }
    evidence = output_root / "evidence"
    (evidence / "index.json").write_text(
        json.dumps(index, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    report = {
        "schema_version": 1,
        "source_sha256": {
            name: sha256(source_run / name) for name in MANIFEST_FILES
        },
        "jobs": copy_stats,
        "max_public_file_bytes": MAX_PUBLIC_FILE_BYTES,
        "replacement_count": sanitizer.replacement_count,
        "skipped_sensitive_files": sanitizer.skipped_sensitive_files,
        "skipped_sensitive_binary_files": sanitizer.skipped_sensitive_binary_files,
        "skipped_oversized_files": sanitizer.skipped_oversized_files,
        "skipped_symlinks": sanitizer.skipped_symlinks,
    }
    (evidence / "sanitization-report.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-run", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dotenv", type=Path)
    options = parser.parse_args()
    prepare(
        options.source_run.expanduser().resolve(),
        options.output_root.expanduser().resolve(),
        None if options.dotenv is None else options.dotenv.expanduser().resolve(),
    )


if __name__ == "__main__":
    main()
