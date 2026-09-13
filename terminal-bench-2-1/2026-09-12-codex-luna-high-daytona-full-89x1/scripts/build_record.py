#!/usr/bin/env python3
"""Build one replayable Autobench record from the sanitized 89-task evidence."""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from autobench import (
    Benchmark,
    CapturePolicy,
    Case,
    Direction,
    FactorValue,
    FileRecorder,
    ObservationRole,
    Semantic,
    Variant,
    run_benchmark_spec,
)
from autobench.records.staging import FileRecordSession


ROOT = Path(os.environ.get("KEDI_PUBLICATION_ROOT", Path.cwd())).resolve()


def sha256(path: Path) -> str:
    value = hashlib.sha256()
    with path.open("rb") as stream:
        while chunk := stream.read(1024 * 1024):
            value.update(chunk)
    return value.hexdigest()


class PublicationRecordSession(FileRecordSession):
    async def finish(self, result):
        environment = result.environment.model_copy(update={"cwd": "<PUBLICATION_ROOT>"})
        return await super().finish(result.model_copy(update={"environment": environment}))


class PublicationRecorder(FileRecorder):
    def open_sync(self, start):
        environment = start.environment.model_copy(update={"cwd": "<PUBLICATION_ROOT>"})
        session = super().open_sync(start.model_copy(update={"environment": environment}))
        return PublicationRecordSession(
            recorder=self,
            start=session.start,
            state=session.state,
            manifest=session.manifest,
        )


def duration_seconds(result: dict[str, Any]) -> float | None:
    value = result.get("duration_seconds")
    if value is not None:
        return float(value)
    started = result.get("started_at")
    finished = result.get("finished_at")
    if not started or not finished:
        return None
    return (
        datetime.fromisoformat(str(finished).replace("Z", "+00:00"))
        - datetime.fromisoformat(str(started).replace("Z", "+00:00"))
    ).total_seconds()


def optional_metric(
    ctx,
    name: str,
    value: Any,
    *,
    semantic_type: str,
    unit: str | None = None,
    direction: Direction | None = None,
    role: ObservationRole = ObservationRole.DIAGNOSTIC,
    span_id: str,
) -> None:
    if value is not None:
        ctx.metric(
            name,
            value,
            semantic_type=semantic_type,
            unit=unit,
            direction=direction,
            role=role,
            span_id=span_id,
        )


def task(ctx, case):
    value = case.input
    if not isinstance(value, dict):
        raise TypeError("case input must be a mapping")
    trial = (ROOT / str(value["trial_dir"])).resolve()
    result_path = trial / "result.json"
    kedi_path = trial / "agent" / "kedi-result.json"
    result = json.loads(result_path.read_text(encoding="utf-8"))
    kedi = json.loads(kedi_path.read_text(encoding="utf-8"))
    rewards = ((result.get("verifier_result") or {}).get("rewards") or {})
    usage = kedi.get("usage") or {}
    exception = result.get("exception_info") or {}
    with ctx.span(
        "capture terminal-bench publication metrics",
        kind="workflow",
        input={"task_name": result["task_name"], "trial_name": result["trial_name"]},
    ) as span:
        for name, reward in rewards.items():
            ctx.metric(
                f"terminal_bench.reward.{name}",
                reward,
                semantic_type=Semantic.QUALITY_CORRECTNESS,
                direction=Direction.MAXIMIZE,
                role=ObservationRole.OBJECTIVE,
                span_id=span.id,
            )
        ctx.check(
            "terminal_bench.grader_completed",
            bool(rewards),
            reason="official Harbor verifier produced rewards",
            span_id=span.id,
        )
        ctx.check(
            "kedi.trial_completed",
            kedi.get("state") == "completed",
            reason=f"Kedi state: {kedi.get('state')}",
            span_id=span.id,
        )
        optional_metric(
            ctx,
            "terminal_bench.duration",
            duration_seconds(result),
            semantic_type=Semantic.TIME_LATENCY,
            unit="s",
            direction=Direction.MINIMIZE,
            span_id=span.id,
        )
        specs = (
            ("input_tokens", Semantic.LLM_TOKENS_INPUT, "token", None),
            ("cache_read_tokens", Semantic.LLM_TOKENS_CACHED_INPUT, "token", None),
            ("cache_write_tokens", Semantic.LLM_TOKENS_CACHE_WRITE, "token", None),
            ("output_tokens", Semantic.LLM_TOKENS_OUTPUT, "token", None),
            ("total_tokens", Semantic.LLM_TOKENS_TOTAL, "token", None),
            ("requests", Semantic.LLM_REQUEST_COUNT, "request", None),
            ("tool_calls", "tool.call.count", "call", None),
            ("cost_usd", Semantic.MONEY_COST, "USD", Direction.MINIMIZE),
        )
        for name, semantic_type, unit, direction in specs:
            optional_metric(
                ctx,
                f"kedi.{name}",
                usage.get(name),
                semantic_type=semantic_type,
                unit=unit,
                direction=direction,
                role=ObservationRole.OBJECTIVE if name == "cost_usd" else ObservationRole.DIAGNOSTIC,
                span_id=span.id,
            )
        input_tokens = usage.get("input_tokens")
        cache_tokens = usage.get("cache_read_tokens")
        if input_tokens and cache_tokens is not None:
            ctx.metric(
                "kedi.cache_read_ratio",
                cache_tokens / input_tokens,
                semantic_type="coverage.ratio",
                unit="ratio",
                direction=Direction.MAXIMIZE,
                role=ObservationRole.DIAGNOSTIC,
                span_id=span.id,
            )
        if exception.get("exception_type"):
            ctx.diagnostic(
                "terminal_bench.exception",
                exception["exception_type"],
                semantic_type=Semantic.ERROR_TYPE,
                span_id=span.id,
            )
        evidence_reference = {
            "trial_root": str(value["trial_dir"]),
            "result_sha256": sha256(result_path),
            "kedi_result_sha256": sha256(kedi_path),
            "sanitization_manifest": "evidence/sanitization-report.json",
        }
        ctx.artifact(
            "terminal_bench.public_evidence_reference",
            evidence_reference,
            media_type="application/json",
            span_id=span.id,
        )
        output = {
            "task_name": str(result["task_name"]).removeprefix("terminal-bench/"),
            "trial_name": result["trial_name"],
            "harbor_exception": exception.get("exception_type"),
            "rewards": rewards,
            "kedi_state": kedi.get("state"),
            "usage": usage,
            "evidence_reference": evidence_reference,
        }
        span.set_output(output)
        return output


async def build(root: Path) -> None:
    global ROOT
    ROOT = root
    os.environ["KEDI_PUBLICATION_ROOT"] = str(root)
    index = json.loads((root / "evidence" / "index.json").read_text(encoding="utf-8"))
    cases = []
    for entry in index["trials"]:
        job = root / "evidence" / "harbor" / index["batches"][entry["batch"]]
        trial = job / entry["trial_id"]
        cases.append(
            Case(
                id=entry["trial_id"],
                input={
                    "job_dir": job.relative_to(root).as_posix(),
                    "trial_dir": trial.relative_to(root).as_posix(),
                    "trial_name": entry["trial_id"],
                    "task_name": entry["task_name"],
                },
                metadata={
                    "source": "harbor",
                    "dataset": "terminal-bench@2.1",
                    "batch": entry["batch"],
                    "qemu_fixed": entry["task_name"] in {"qemu-alpine-ssh", "qemu-startup"},
                },
            )
        )
    if len(cases) != 89:
        raise RuntimeError(f"expected 89 cases, got {len(cases)}")
    variant = Variant(
        id="pydantic-luna-high-websocket",
        factors=[
            FactorValue(name="capture_only", value=True),
            FactorValue(name="adapter", value="pydantic"),
            FactorValue(name="model", value="codex/gpt-5.6-luna"),
            FactorValue(name="effort", value="high"),
            FactorValue(name="transport", value="websocket-http-fallback"),
            FactorValue(name="evidence_payload", value="sanitized-harbor-sibling"),
        ],
    )
    benchmark = (
        Benchmark("kedi-tb21-full89-daytona-publication")
        .description(
            "Import one full, single-trial Terminal-Bench 2.1 run as immutable Autobench evidence."
        )
        .capture(
            CapturePolicy(
                max_collection_items=1_000,
                max_string_length=100_000,
                max_inline_bytes=64_000,
                max_artifact_bytes=20_000_000,
                max_depth=16,
            )
        )
        .dataset(
            cases,
            dataset_id="terminal-bench-2-1-qemu-fixed",
            version="20260912",
            metadata={"trials": 89, "attempts_per_task": 1},
        )
        .variants([variant])
        .task("build_record:task")
    )
    record = root / "evidence" / "autobench" / "full89"
    schema_cache = root / ".autobench-schema-cache"
    previous_autobench_home = os.environ.get("AUTOBENCH_HOME")
    os.environ["AUTOBENCH_HOME"] = schema_cache.name
    previous_cwd = Path.cwd()
    os.chdir(root)
    try:
        await run_benchmark_spec(
            benchmark.to_spec(),
            concurrency_limit=8,
            recorder=PublicationRecorder(
                record,
                source_files=(
                    root / "manifests" / "experiment-contract.json",
                    root / "manifests" / "manifest.json",
                    Path(__file__).resolve(),
                ),
                path_root=root,
                durability="synced",
            ),
        )
    finally:
        os.chdir(previous_cwd)
        shutil.rmtree(schema_cache, ignore_errors=True)
        if previous_autobench_home is None:
            os.environ.pop("AUTOBENCH_HOME", None)
        else:
            os.environ["AUTOBENCH_HOME"] = previous_autobench_home


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    options = parser.parse_args()
    asyncio.run(build(options.root.expanduser().resolve()))


if __name__ == "__main__":
    main()
