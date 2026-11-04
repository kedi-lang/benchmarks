"""Q1: does a compaction fork (same prefix + one appended message) read the prefix from cache?

Requests, all on the same model, instructions and tool definitions:
  R1  long history                         -> warms the cache
  R2  history + normal follow-up           -> baseline cache read
  R3  history + compaction instruction     -> fork, prompted JSON (the plan's design)
  R4  history + compaction instruction     -> fork with an extra output tool (alternative)
  R5  [kept prefix] + compaction block     -> request after compaction (partial prefix)
  R6  compaction block only                -> stateless reset baseline (no prefix)

Run: .venv/bin/python -m benchmarks.agent_compaction.cache_probe [--model gpt-6-luna]
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import random
import re
import tempfile
import uuid

from pydantic_ai.direct import model_request
from pydantic_ai.messages import CachePoint, ModelRequest, ModelResponse, TextPart, UserPromptPart
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.tools import ToolDefinition

from benchmarks.agent_compaction.codex_model import build_model

TOOLS = [
    ToolDefinition(
        name="read_file",
        description="Read a repository file.",
        parameters_json_schema={
            "type": "object",
            "properties": {"path": {"type": "string"}},
            "required": ["path"],
        },
    ),
    ToolDefinition(
        name="search",
        description="Search the repository.",
        parameters_json_schema={
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    ),
]
OUTPUT_TOOL = ToolDefinition(
    name="final_result",
    description="Return the compaction proposal.",
    parameters_json_schema={"type": "object", "properties": {"keep": {"type": "array"}}},
)

COMPACT = (
    "Compact this conversation. Reply with JSON only: "
    '{"keep": [group ids to keep verbatim], "summaries": [{"text": "...", "covers": [ids]}], '
    '"rules": [...], "facts": [...], "pending": [...]}. Groups: g0..g5 are the turns in order.'
)


def _log(seed: int, lines: int) -> str:
    rng = random.Random(seed)
    return "\n".join(
        f"{i:05d} worker-{rng.randint(1, 9)} status={rng.choice(['ok', 'retry', 'slow'])} "
        f"latency_ms={rng.randint(5, 900)} key={rng.getrandbits(48):012x}"
        for i in range(lines)
    )


def history(breakpoints: bool = False) -> list:
    turns = [
        ("Rule: never write outside src/. Here is service log A:\n" + _log(1, 400), "Noted the rule and log A."),
        ("Log B:\n" + _log(2, 400), "Log B read."),
        ("The deploy port is 8123. Log C:\n" + _log(3, 400), "Port 8123 noted; log C read."),
    ]
    messages: list = []
    for user, assistant in turns:
        # A breakpoint at each turn boundary makes every group end a resumable cache prefix.
        content = [user, CachePoint()] if breakpoints else user
        messages.append(ModelRequest(parts=[UserPromptPart(content)]))
        messages.append(ModelResponse(parts=[TextPart(assistant)]))
    return messages


def usage_row(label: str, traffic: str) -> dict:
    """Read usage from the last raw response: Pydantic AI 2.57 drops Codex cached_tokens."""
    last = [json.loads(line) for line in open(traffic) if '"response"' in line][-1]["body"]
    usage = json.loads(re.findall(r'"usage":(\{"input_tokens".*?"total_tokens":\d+)', last)[-1] + "}")
    details = usage.get("input_tokens_details", {})
    read = details.get("cached_tokens", 0)
    return {
        "request": label,
        "input": usage["input_tokens"],
        "cache_read": read,
        "cache_write": details.get("cache_write_tokens", 0),
        "output": usage["output_tokens"],
        "cached_%": round(100 * read / usage["input_tokens"], 1) if usage["input_tokens"] else 0,
    }


async def main(model_name: str, effort: str, breakpoints: bool, grow: bool) -> None:
    traffic = os.path.join(tempfile.mkdtemp(), "traffic.jsonl")
    os.environ["KEDI_BENCH_TRAFFIC"] = traffic
    model = build_model(model_name, effort)
    settings = {"openai_prompt_cache_key": f"agent-compaction-probe-{uuid.uuid4().hex[:8]}"}
    params = ModelRequestParameters(function_tools=TOOLS, allow_text_output=True)
    base = history(breakpoints)
    rows = []

    async def ask(label, messages, parameters=params):
        response = await model_request(
            model, messages, model_settings=settings, model_request_parameters=parameters
        )
        rows.append(usage_row(label, traffic))
        return response

    if grow:
        # A real conversation grows turn by turn: each turn boundary is once the request's tail.
        for turn in range(1, len(base) // 2):
            await ask(f"R0 grow turn {turn}", base[: 2 * turn - 1])
    await ask("R1 warm", base + [ModelRequest(parts=[UserPromptPart("Summarize log A in one line.")])])
    await ask("R2 follow-up", base + [ModelRequest(parts=[UserPromptPart("Summarize log B in one line.")])])
    fork = await ask("R3 fork JSON", base + [ModelRequest(parts=[UserPromptPart(COMPACT)])])
    await ask(
        "R4 fork +output tool",
        base + [ModelRequest(parts=[UserPromptPart(COMPACT)])],
        ModelRequestParameters(function_tools=TOOLS, output_tools=[OUTPUT_TOOL], output_mode="tool"),
    )
    block = "[Compacted history]\nRules:\n- never write outside src/\nFacts:\n- deploy port is 8123"
    await ask(
        "R5 kept prefix + block",
        base[:2] + [ModelRequest(parts=[UserPromptPart(block + "\n\nWhat is the deploy port?")])],
    )
    await ask("R6 block only", [ModelRequest(parts=[UserPromptPart(block + "\n\nWhat is the deploy port?")])])

    for row in rows:
        print(json.dumps(row))
    text = "".join(p.content for p in fork.parts if isinstance(p, TextPart))
    print("fork output:", text[:600])


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="gpt-6-luna")
    parser.add_argument("--effort", default="medium")
    parser.add_argument("--breakpoints", action="store_true")
    parser.add_argument("--grow", action="store_true")
    args = parser.parse_args()
    asyncio.run(main(args.model, args.effort, args.breakpoints, args.grow))
