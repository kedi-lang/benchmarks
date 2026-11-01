"""Run task 1 under one compaction strategy and record grade, usage and compaction events.

    .venv/bin/python -m benchmarks.agent_compaction.run --strategy A1 --seeds 1 2 3
Strategies: none (B0), B1 truncation, B2 stateless summary, A1 agent-led fork.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from . import state, task1, task2
from .compactor import (
    CompactionLog,
    RecordingModel,
    fork_compactor,
    stateless_compactor,
    truncation_compactor,
)

RECORDS = Path(__file__).parent / "records"

SOURCE_HEAD = """\
```
from benchmarks.agent_compaction.state import PROCESSOR, CONDITION, TASK, read_log
```

~Report(incidents: list[str], owner: str)

> profile: auditor:
    > adapter: pydantic
    > artifacts:
        enabled: false
"""
HISTORY = """\
    > history:
        enabled: true
        compaction_mode: native
        compaction_threshold: __THRESHOLD__
"""
HISTORY = """\
    > history:
        enabled: true
        processor: `PROCESSOR`
        processor_condition: `CONDITION`
"""
SOURCE_TAIL = """\
    > use: `read_log`

[task: str] = `TASK`
> use: auditor
>> <task> The final report is [report: Report].
"""


def _native_model(model_name: str, effort: str, cache_key: str, events: list) -> Any:
    """The provider model itself (native compaction needs a real OpenAIResponsesModel).

    Same settings the RecordingModel adds, plus HTTP hooks that log provider compactions.
    """
    import httpx
    from codex_auth_helper import create_codex_responses_model

    from benchmarks.subagent_comparison.common.prompts import BASE_INSTRUCTIONS

    model = create_codex_responses_model(
        model_name,
        instructions=BASE_INSTRUCTIONS,
        settings={
            "openai_reasoning_effort": effort,
            "openai_prompt_cache_key": cache_key,
            "parallel_tool_calls": False,
        },
        connection="http",
        fallback="error",
    )
    model.client.max_retries = 0
    model.client.timeout = httpx.Timeout(600.0, connect=60.0)

    async def on_response(response: Any) -> None:
        body = (await response.aread()).decode("utf-8", "replace")
        compact_endpoint = response.request.url.path.endswith("/compact")
        if compact_endpoint or '"type":"compaction"' in body:
            usage = re.findall(r'"usage":(\{"input_tokens".*?"total_tokens":\d+)', body)
            parsed = json.loads(usage[-1] + "}") if usage else {}
            events.append(
                {
                    "strategy": "native",
                    "endpoint": "compact" if compact_endpoint else "inline",
                    "status": response.status_code,
                    "input": parsed.get("input_tokens") if compact_endpoint else None,
                    "cache_read": (parsed.get("input_tokens_details") or {}).get("cached_tokens")
                    if compact_endpoint
                    else None,
                    "output": parsed.get("output_tokens") if compact_endpoint else None,
                }
            )

    model.client._client.event_hooks["response"].append(on_response)
    return model


def _estimated_tokens(messages: list) -> int:
    """Kedi's estimator (UTF-8 bytes / 3), so native triggers at the same point as the others."""
    from pydantic_ai.messages import ModelMessagesTypeAdapter

    return len(ModelMessagesTypeAdapter.dump_json(messages)) // 3


def run_one(
    strategy: str, seed: int, threshold: int, model_name: str, effort: str, task: str = "t1"
) -> dict:
    from kedi.agent_adapter import PydanticAdapter
    from kedi.agent_adapter.invocation import InvocationUsage, observe_invocations
    from kedi.interactive_session import InteractiveSession
    from kedi.promise import force

    from benchmarks.subagent_comparison.common.model import build_model

    state.SEED = seed
    case = None if task == "t1" else task2.scenario(task, seed)
    state.SCENARIO = case
    state.TASK = task1.TASK if case is None else task2.task_text(case)
    cache_key = f"ac-{uuid.uuid4().hex[:10]}"
    log = CompactionLog()
    native = strategy in {"native", "native-compact"}
    model = (
        _native_model(model_name, effort, cache_key, log.events)
        if native
        else RecordingModel(build_model(model_name, effort), cache_key=cache_key)
    )
    processor = state.PROCESSOR = {
        "A1": lambda: fork_compactor(model, log, structured=True, dynamic=True),
        "A1-free": lambda: fork_compactor(model, log, structured=False, dynamic=True),
        "A1-fixed": lambda: fork_compactor(model, log, structured=True, dynamic=False),
        "B2": lambda: stateless_compactor(model, log, structured=False),
        "B3": lambda: stateless_compactor(model, log, structured=True),
        "B1": lambda: truncation_compactor(log),
        "none": lambda: None,
        "native": lambda: None,
        "native-compact": lambda: None,
    }[strategy]()
    state.CONDITION = lambda info: info.estimated_tokens >= threshold
    # `native` attaches the same capability Kedi's `compaction_mode: native` would; the DSL path
    # cannot be used here because Kedi checks the model type on its budget wrapper (bug, see REPORT).
    history = HISTORY if processor else ""
    source = SOURCE_HEAD + history + SOURCE_TAIL
    adapter_options: dict = {}
    if strategy == "native":
        from pydantic_ai.models.openai import OpenAICompaction

        adapter_options["capabilities"] = [OpenAICompaction(token_threshold=threshold)]
    if strategy == "native-compact":
        from pydantic_ai.models.openai import OpenAICompaction

        # Stateless `/responses/compact` (what Codex uses for remote compaction), same trigger point.
        adapter_options["capabilities"] = [
            OpenAICompaction(trigger=lambda messages: _estimated_tokens(messages) >= threshold)
        ]

    usages: list[InvocationUsage] = []
    started = time.monotonic()
    error = None
    answer: dict = {}
    try:
        with observe_invocations(usages.append):
            with InteractiveSession(adapter=PydanticAdapter(model, **adapter_options)) as session:
                session.execute(source)
                answer = force(session._env["report"]).model_dump(mode="json")
    except Exception as exc:  # recorded, the batch continues
        error = f"{type(exc).__name__}: {str(exc)[:300]}"
    total = sum(usages, InvocationUsage())
    fork_input = sum(e.get("input", 0) or 0 for e in log.events)
    fork_cached = sum(e.get("cache_read", 0) or 0 for e in log.events)
    return {
        "strategy": strategy,
        "seed": seed,
        "threshold": threshold,
        "model": model_name,
        "seconds": round(time.monotonic() - started, 1),
        "error": error,
        "answer": answer,
        "task": task,
        "grade": (task1.grade(seed, answer) if case is None else task2.grade(case, answer))
        if answer
        else None,
        "usage": {
            "requests": total.requests,
            "input": total.input_tokens,
            "cache_read": total.cache_read_tokens,
            "output": total.output_tokens,
            "compaction_input": fork_input,
            "compaction_cache_read": fork_cached,
        },
        "compactions": log.events,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", required=True, choices=["none", "B1", "B2", "B3", "A1", "A1-free", "A1-fixed", "native", "native-compact"])
    parser.add_argument("--seeds", type=int, nargs="+", default=[1])
    parser.add_argument("--threshold", type=int, default=18_000)
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--task", default="t1", choices=["t1", *task2.VARIANTS])
    args = parser.parse_args()
    RECORDS.mkdir(exist_ok=True)
    name = "task1" if args.task == "t1" else args.task
    out = RECORDS / f"{name}_t{args.threshold // 1000}k_{args.strategy}.jsonl"
    for seed in args.seeds:
        record = run_one(args.strategy, seed, args.threshold, args.model, args.effort, args.task)
        with out.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record) + "\n")
        g = record["grade"] or {}
        print(
            json.dumps(
                {
                    "strategy": args.strategy,
                    "seed": seed,
                    "error": record["error"],
                    "ok": bool(g) and g.get("strict", g.get("incidents_exact") and g["owner"]),
                    "grade": g,
                    "usage": record["usage"],
                    "compactions": len(record["compactions"]),
                }
            )
        )


if __name__ == "__main__":
    main()
