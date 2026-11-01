"""Keep a codex_auth_helper model usable across Kedi invocations that run on different event loops.

codex_auth_helper hands Pydantic AI a ready-made `AsyncOpenAI` client, and Pydantic AI only refreshes
clients it created itself, so after the first invocation's loop closes, the next dependent template
fails with `RuntimeError: Event loop is closed`. This guard replaces the two loop-bound httpx clients
(the SDK's and the token manager's) on the innermost model instance whenever a request runs on a new loop.
It patches the instance, because Kedi copies wrapper models but shares the provider model inside them.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

import httpx


def guard_event_loops(model: Any) -> Any:
    client = model.client
    state: dict[str, Any] = {"loop": None, "refreshes": 0}

    def refresh() -> None:
        loop = asyncio.get_running_loop()
        previous = state["loop"]
        state["loop"] = loop
        if previous is None or previous is loop:
            return
        old = client._client
        client._client = httpx.AsyncClient(
            timeout=old.timeout,
            follow_redirects=old.follow_redirects,
            event_hooks=old.event_hooks,
        )
        manager = client.token_manager
        old_auth = manager.http_client
        manager.http_client = httpx.AsyncClient(
            timeout=old_auth.timeout, follow_redirects=old_auth.follow_redirects
        )
        state["refreshes"] += 1

    original_request = model.request
    original_stream = model.request_stream

    async def request(*args: Any, **kwargs: Any) -> Any:
        refresh()
        return await original_request(*args, **kwargs)

    @asynccontextmanager
    async def request_stream(*args: Any, **kwargs: Any) -> AsyncIterator[Any]:
        refresh()
        async with original_stream(*args, **kwargs) as stream:
            yield stream

    model.request = request
    model.request_stream = request_stream
    model.loop_guard_state = state
    return model
