"""The Codex model builder and base instruction the recorded runs used.

Copied verbatim from the Kedi workspace's `benchmarks/subagent_comparison/common/model.py` and
`prompts.py` (unchanged since 2026-10-31), which every recorded run imported. The copy lets this
folder run on its own.
"""

from __future__ import annotations

from typing import Any

import httpx

BASE_INSTRUCTIONS = "You are a careful assistant. Follow the task instructions exactly."


def build_model(name: str, effort: str) -> Any:
    from codex_auth_helper import create_codex_responses_model

    model = create_codex_responses_model(
        name,
        instructions=BASE_INSTRUCTIONS,
        settings={"openai_reasoning_effort": effort},
        connection="http",
        fallback="error",
    )
    # Kedi rejects finite request budgets when provider retries are enabled.
    model.client.max_retries = 0
    # The default 5 s connect timeout trips when a coordinator opens a burst of connections.
    model.client.timeout = httpx.Timeout(600.0, connect=60.0)
    _record_traffic(model)
    return model


def _record_traffic(model: Any) -> None:
    """Persist every raw request and response body, so later questions need no rerun."""
    import json
    import os

    path = os.environ.get("KEDI_BENCH_TRAFFIC")
    if not path:
        return

    def write(kind: str, body: bytes) -> None:
        with open(path, "a", encoding="utf-8") as stream:
            stream.write(json.dumps({"kind": kind, "body": body.decode("utf-8", "replace")}) + "\n")

    async def on_request(request: Any) -> None:
        write("request", request.content)

    async def on_response(response: Any) -> None:
        write("response", await response.aread())

    hooks = model.client._client.event_hooks
    hooks["request"].append(on_request)
    hooks["response"].append(on_response)
