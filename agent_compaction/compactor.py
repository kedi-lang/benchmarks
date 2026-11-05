"""History processors for the experiment: A1 agent-led fork, B2 stateless summary, B1 truncation.

Each strategy is a Kedi `> history: processor:` callable. They share one RecordingModel, which
adds a stable prompt-cache key to every request and remembers the last request's parameters, so
the A1 fork can be sent with exactly the tools and settings the conversation uses.
"""

from __future__ import annotations

import json
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass, field, replace
from typing import Any

from pydantic_ai.messages import ModelMessage, ModelRequest, TextPart, UserPromptPart
from pydantic_ai.models import ModelRequestParameters
from pydantic_ai.models.wrapper import WrapperModel

from .normalizer import BLOCK, Group, ProposalError, normalize, parse_proposal, render_block


class RecordingModel(WrapperModel):
    def __init__(self, wrapped: Any, *, cache_key: str) -> None:
        super().__init__(wrapped)
        self.cache_key = cache_key
        # Kedi copies wrapper models (vars are shallow-copied), so record into a shared dict.
        self.recorded: dict[str, Any] = {}

    @property
    def last_settings(self) -> Any:
        return self.recorded["settings"]

    @property
    def last_parameters(self) -> ModelRequestParameters:
        return self.recorded["parameters"]

    def _with_cache_key(self, settings: Any) -> dict[str, Any]:
        merged = dict(settings or {})
        merged["openai_prompt_cache_key"] = self.cache_key
        merged["parallel_tool_calls"] = False
        return merged

    async def request(self, messages, model_settings, model_request_parameters):  # type: ignore[override]
        settings = self._with_cache_key(model_settings)
        self.recorded.update(settings=settings, parameters=model_request_parameters)
        return await super().request(messages, settings, model_request_parameters)

    @asynccontextmanager
    async def request_stream(  # type: ignore[override]
        self, messages, model_settings, model_request_parameters, run_context=None
    ) -> AsyncIterator[Any]:
        settings = self._with_cache_key(model_settings)
        self.recorded.update(settings=settings, parameters=model_request_parameters)
        async with super().request_stream(
            messages, settings, model_request_parameters, run_context
        ) as stream:
            yield stream


@dataclass
class CompactionLog:
    events: list[dict[str, Any]] = field(default_factory=list)


def _usage(response: Any) -> dict[str, Any]:
    usage = response.usage
    return {
        "input": usage.input_tokens,
        "cache_read": usage.cache_read_tokens,
        "output": usage.output_tokens,
    }


def _text(response: Any) -> str:
    return "".join(part.content for part in response.parts if isinstance(part, TextPart))


def _preview(messages: list[ModelMessage]) -> str:
    chunks: list[str] = []
    for message in messages:
        for part in message.parts:
            content = getattr(part, "content", None)
            if isinstance(content, str):
                chunks.append(content)
            elif getattr(part, "tool_name", None):
                chunks.append(f"<{part.part_kind} {part.tool_name}>")
    return " ".join(" ".join(chunks).split())[:160]


def _groups(ctx: Any) -> list[Group]:
    total = len(ctx.messages)
    return [
        Group(
            group_id=f"g{index}",
            protected=group.protected,
            closed=group.closed,
            current=group.entry_end == total,
            tokens=group.token_estimate,
        )
        for index, group in enumerate(ctx.groups)
    ]


def _assemble(ctx: Any, segments: list[str], block: str) -> list[ModelMessage]:
    spans = {f"g{i}": (g.entry_start, g.entry_end) for i, g in enumerate(ctx.groups)}
    out: list[ModelMessage] = []
    for segment in segments:
        if segment == BLOCK:
            out.append(ModelRequest(parts=[UserPromptPart(block)]))
        else:
            start, end = spans[segment]
            out.extend(ctx.messages[start:end])
    return out


STRUCTURED = """\
  "rules": [standing rules and constraints you must keep obeying],
  "facts": [facts, values and decisions you will need, latest version only],
  "pending": [work still to do],
  "summaries": [{{"text": "...", "covers": [ids of dropped groups it replaces]}}]"""
FREE = '  "summary": "free-text summary of everything you still need from the dropped groups"'
KEEP = {
    "free": '  "keep": [ids of groups to keep verbatim; everything not kept is removed],\n',
    "recent": '  "keep_recent": how many of the most recent groups to keep verbatim (an integer); all older groups are removed,\n',
    "fixed": "",
}
FORK_PROMPT = """\
Your context is about to be compacted. Decide what of the conversation above you still need.
Reply with JSON only, no prose:
{{
{keep}{fields}
}}
Groups (id: tokens, preview):
{index}"""
STATELESS_PROMPT = """\
The following conversation excerpt will be removed from an assistant's context; the assistant will
continue the task without seeing it. Reply with JSON only, no prose:
{{
{fields}
}}
Excerpt (group id, then content):
{transcript}"""
B2_PROMPT = """\
Summarize the following conversation excerpt for an assistant that will continue the task without
seeing it. Keep every rule and constraint, every fact or value that may be needed, the latest
decisions, and the pending work. Be concise.

{transcript}"""

RULE_PHRASES = ("legacy", "uppercase", "highest severity")


def _all_text(messages: list[ModelMessage]) -> str:
    return _preview_full(list(messages)).lower()


def _retention(before: list[ModelMessage], after: list[ModelMessage]) -> dict[str, Any]:
    """Planted facts and rule phrases present before vs after one compaction."""
    seen = set(re.findall(r"inc-\d+", _all_text(before)))
    after_text = _all_text(after)
    kept = {i for i in seen if i in after_text}
    return {
        "facts_seen": len(seen),
        "facts_kept": len(kept),
        "rules_kept": [phrase for phrase in RULE_PHRASES if phrase in after_text],
    }


def _parse_json(raw: str) -> dict[str, Any]:
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    data = json.loads(match.group(0) if match else raw)
    if not isinstance(data, dict):
        raise ValueError("proposal must be a JSON object")
    return data


def _index(ctx: Any, groups: list[Group]) -> str:
    return "\n".join(
        f"{g.group_id}: {g.tokens}, {_preview(ctx.messages[s.entry_start : s.entry_end])}"
        for g, s in zip(groups, ctx.groups)
    )


async def _fork(model: RecordingModel, ctx: Any, prompt: str) -> Any:
    """The conversation's own request plus one appended instruction (same prefix, same tools)."""
    tail = ctx.messages[-1]
    fork_tail = replace(tail, parts=[*tail.parts, UserPromptPart(prompt)])
    # Tools stay declared (they are part of the cached prefix) but cannot be called, and text
    # is allowed so the reply can be JSON instead of the structured output tool.
    return await model.wrapped.request(
        [*ctx.messages[:-1], fork_tail],
        {**model.last_settings, "tool_choice": "none"},
        replace(model.last_parameters, allow_text_output=True),
    )


async def _stateless(model: RecordingModel, prompt: str) -> Any:
    return await model.wrapped.request(
        [ModelRequest(parts=[UserPromptPart(prompt)])],
        model.last_settings,
        ModelRequestParameters(),
    )


def _fixed_drop(groups: list[Group], keep_recent: int) -> set[str]:
    droppable = [g for g in groups if g.closed and not g.protected and not g.current]
    return {g.group_id for g in droppable[: -keep_recent or None]}


def _recent_keep(groups: list[Group], count: Any) -> list[str]:
    """A1-recent: the fork names how many of the latest groups stay; protected ones are still forced in."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ProposalError("`keep_recent` must be a non-negative integer")
    return [g.group_id for g in groups[max(len(groups) - count, 0) :]] if count else []


def _transcript(ctx: Any, drop: set[str]) -> str:
    return "\n\n".join(
        f"[{f'g{i}'}]\n" + _preview_full(ctx.messages[s.entry_start : s.entry_end])
        for i, s in enumerate(ctx.groups)
        if f"g{i}" in drop
    )


def _finish(ctx, log, event, segments: list[str] | None, block: str) -> list[ModelMessage]:
    """Assemble, measure retention, record; a no-drop result keeps native history unchanged."""
    out = list(ctx.messages) if not segments or BLOCK not in segments else _assemble(ctx, segments, block)
    event.update(_retention(ctx.messages, out))
    log.events.append(event)
    return out


def _segments_for_drop(groups: list[Group], drop: set[str]) -> list[str]:
    segments: list[str] = []
    for g in groups:
        if g.group_id not in drop:
            segments.append(g.group_id)
        elif BLOCK not in segments:
            segments.append(BLOCK)
    return segments


def fork_compactor(
    model: RecordingModel, log: CompactionLog, *, structured: bool, keep: str, keep_recent: int = 2
):
    """Who picks the verbatim groups: the fork, any of them (A1 structured, A1-free free text); the fork, a
    count of the latest ones (A1-recent, free text); or nobody, the last `keep_recent` (A1-fixed, structured)."""
    name = {
        (True, "free"): "A1",
        (False, "free"): "A1-free",
        (False, "recent"): "A1-recent",
        (True, "fixed"): "A1-fixed",
    }[(structured, keep)]

    async def process(ctx: Any) -> list[ModelMessage]:
        groups = _groups(ctx)
        prompt = FORK_PROMPT.format(
            keep=KEEP[keep],
            fields=STRUCTURED if structured else FREE,
            index=_index(ctx, groups),
        )
        response = await _fork(model, ctx, prompt)
        event: dict[str, Any] = {"strategy": name, "before": ctx.estimated_tokens, **_usage(response)}
        try:
            data = _parse_json(_text(response))
            if keep == "fixed":
                drop = _fixed_drop(groups, keep_recent)
                data["keep"] = [g.group_id for g in groups if g.group_id not in drop]
            elif keep == "recent":
                data["keep"] = _recent_keep(groups, data.get("keep_recent"))
                event["keep_recent"] = data["keep_recent"]
            if not structured:
                summary = data.get("summary")
                if not isinstance(summary, str):
                    raise ProposalError("`summary` must be a string")
                data = {"keep": data.get("keep", [])}
            proposal = parse_proposal(data)
            layout = normalize(groups, proposal)
        except (ProposalError, ValueError) as exc:
            event["fallback"] = str(exc)[:200]
            return _fallback(ctx, log, event)
        event.update(kept=len([s for s in layout.segments if s != BLOCK]), dropped=len(layout.dropped))
        if structured:
            event.update(rules=list(proposal.rules), facts=list(proposal.facts), pending=list(proposal.pending))
            block = render_block(proposal, layout)
        else:
            block = "[Compacted history]\n" + summary
        return _finish(ctx, log, event, layout.segments if layout.dropped else None, block)

    return process


def _fallback(ctx: Any, log: CompactionLog, event: dict[str, Any]) -> list[ModelMessage]:
    out = ctx.keep_recent_groups(4)
    event.update(_retention(ctx.messages, out))
    log.events.append(event)
    return out


def stateless_compactor(
    model: RecordingModel, log: CompactionLog, *, structured: bool, keep_recent: int = 2
):
    """B2 (free-text summary) and B3 (structured JSON) over the older groups; recent ones stay."""
    name = "B3" if structured else "B2"

    async def process(ctx: Any) -> list[ModelMessage]:
        groups = _groups(ctx)
        drop = _fixed_drop(groups, keep_recent)
        transcript = _transcript(ctx, drop)
        prompt = (
            STATELESS_PROMPT.format(fields=STRUCTURED, transcript=transcript)
            if structured
            else B2_PROMPT.format(transcript=transcript)
        )
        response = await _stateless(model, prompt)
        event: dict[str, Any] = {"strategy": name, "before": ctx.estimated_tokens, "dropped": len(drop), **_usage(response)}
        if not structured:
            block = "[Compacted history]\n" + _text(response)
        else:
            try:
                proposal = parse_proposal({"keep": [], **_parse_json(_text(response))})
                layout = normalize(groups, replace(proposal, keep=tuple(g.group_id for g in groups if g.group_id not in drop)))
            except (ProposalError, ValueError) as exc:
                event["fallback"] = str(exc)[:200]
                return _fallback(ctx, log, event)
            event.update(rules=list(proposal.rules), facts=list(proposal.facts), pending=list(proposal.pending))
            block = render_block(proposal, layout)
        return _finish(ctx, log, event, _segments_for_drop(groups, drop) if drop else None, block)

    return process


def truncation_compactor(log: CompactionLog, *, keep_recent: int = 2):
    """B1: drop older groups, keep the recent ones."""

    def process(ctx: Any) -> list[ModelMessage]:
        log.events.append({"strategy": "B1", "before": ctx.estimated_tokens})
        return ctx.keep_recent_groups(keep_recent)

    return process


def _preview_full(messages: list[ModelMessage]) -> str:
    lines: list[str] = []
    for message in messages:
        for part in message.parts:
            content = getattr(part, "content", None)
            name = getattr(part, "tool_name", None)
            if isinstance(content, str):
                lines.append(f"[{part.part_kind}{' ' + name if name else ''}] {content}")
            elif name:
                lines.append(f"[{part.part_kind} {name}] {getattr(part, 'args', '')}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------------------------
# Phase 7 (brief P1): does a reset or a restated policy explain the fork's advantage?
# ---------------------------------------------------------------------------------------------

EVIDENCE = re.compile(
    r"^(?:\d{4} )?.*?\b((?:INCIDENT|UPDATE|RETRACT) inc-\d+.*|[A-Z ]*CHANGE:.*)$", re.MULTILINE
)
POLICY = re.compile(r"[A-Z ]*CHANGE:.*")


def _observed(messages: list[ModelMessage]) -> dict[str, Any]:
    """Facts, instruction changes and progress, taken only from tool results already returned."""
    from pydantic_ai.messages import ToolCallPart, ToolReturnPart

    calls: dict[str, str] = {}
    evidence: list[str] = []
    read: list[str] = []
    for message in messages:
        for part in message.parts:
            if isinstance(part, ToolCallPart):
                args = part.args if isinstance(part.args, dict) else json.loads(part.args or "{}")
                calls[part.tool_call_id] = str(args.get("name", "?"))
            elif isinstance(part, ToolReturnPart) and part.tool_name == "read_log":
                name = calls.get(part.tool_call_id, "?")
                read.append(name)
                for line in EVIDENCE.findall(str(part.content)):
                    evidence.append(f"[{name}] {line.strip()}")
    return {"read": read, "evidence": evidence, "policies": [e for e in evidence if POLICY.search(e)]}


def _progress(read: list[str]) -> str:
    numbers = sorted({int(n.removeprefix("log_")) for n in read if n.startswith("log_") and n[4:].isdigit()})
    last = numbers[-1] if numbers else 0
    return (
        f"Logs already read: {', '.join(f'log_{n}' for n in numbers) or 'none'}. "
        f"Next log to read: log_{last + 1} (if it exists; the task says how many logs there are)."
    )


def _deterministic_block(observed: dict[str, Any]) -> str:
    parts = ["[Runtime checkpoint — built from tool results already returned, not a model summary]"]
    if observed["policies"]:
        parts.append(
            "Instruction changes received during the task (latest wins):\n"
            + "\n".join(f"- {p}" for p in observed["policies"])
        )
    facts = [e for e in observed["evidence"] if not POLICY.search(e)]
    parts.append("Evidence lines seen so far:\n" + ("\n".join(f"- {f}" for f in facts) or "- none"))
    parts.append("Progress: " + _progress(observed["read"]))
    return "\n\n".join(parts)


def _accumulate(state: dict[str, Any], messages: list[ModelMessage]) -> dict[str, Any]:
    """Runtime ledger of everything tool results have returned so far, kept across resets."""
    ledger = state.setdefault("ledger", {"read": [], "evidence": []})
    observed = _observed(messages)
    for name in observed["read"]:
        if name not in ledger["read"]:
            ledger["read"].append(name)
    for line in observed["evidence"]:
        if line not in ledger["evidence"]:
            ledger["evidence"].append(line)
    return {
        "read": ledger["read"],
        "evidence": ledger["evidence"],
        "policies": [e for e in ledger["evidence"] if POLICY.search(e)],
    }


def _new_policy(state: dict[str, Any], messages: list[ModelMessage]) -> bool:
    seen = len(_accumulate(state, messages)["policies"])
    fresh = seen > state.get("policies", 0)
    state["policies"] = seen
    return fresh


def deterministic_reset(log: CompactionLog, *, threshold: int):
    """reset-det: at the threshold and on every instruction change, replace the history with the
    protected prompt, a runtime-built checkpoint and the current exchange (same-session replacement)."""
    state: dict[str, Any] = {}

    def process(ctx: Any) -> list[ModelMessage]:
        policy = _new_policy(state, list(ctx.messages))
        if ctx.estimated_tokens < threshold and not policy:
            return list(ctx.messages)
        groups = _groups(ctx)
        layout = normalize(groups, parse_proposal({"keep": []}))
        observed = _accumulate(state, list(ctx.messages))
        event = {
            "strategy": "reset-det",
            "before": ctx.estimated_tokens,
            "trigger": "policy" if policy else "threshold",
            "dropped": len(layout.dropped),
            "policies": observed["policies"],
        }
        if not layout.dropped:
            event.update(_retention(ctx.messages, ctx.messages))
            log.events.append(event)
            return list(ctx.messages)
        return _finish(ctx, log, event, layout.segments, _deterministic_block(observed))

    return process


def fork_with_policy_trigger(model: RecordingModel, log: CompactionLog, *, threshold: int):
    """reset-fork: A1-free, also triggered by every instruction change (reset timing held equal)."""
    inner = fork_compactor(model, log, structured=False, keep="free")
    state: dict[str, Any] = {}

    async def process(ctx: Any) -> list[ModelMessage]:
        policy = _new_policy(state, list(ctx.messages))
        if ctx.estimated_tokens < threshold and not policy:
            return list(ctx.messages)
        before = len(log.events)
        out = await inner(ctx)
        if len(log.events) > before:
            log.events[-1]["trigger"] = "policy" if policy else "threshold"
        return out

    return process


def policy_reassert(log: CompactionLog):
    """native+reassert: when an instruction change or a new native compaction appears, the runtime
    restates the instruction changes verbatim in a message just before the current exchange."""
    from pydantic_ai.messages import CompactionPart

    state: dict[str, Any] = {"compactions": 0}

    def process(ctx: Any) -> list[ModelMessage]:
        messages = list(ctx.messages)
        policy = _new_policy(state, messages)
        compactions = sum(isinstance(p, CompactionPart) for m in messages for p in m.parts)
        fresh_compaction = compactions > state["compactions"]
        state["compactions"] = compactions
        observed = _accumulate(state, messages)
        if not observed["policies"] or not (policy or fresh_compaction):
            return messages
        current = ctx.groups[-1]
        block = (
            "[Runtime restatement of instruction changes received during the task (latest wins)]\n"
            + "\n".join(f"- {p}" for p in observed["policies"])
        )
        log.events.append(
            {"strategy": "native+reassert", "trigger": "policy" if policy else "native-compaction",
             "before": ctx.estimated_tokens}
        )
        return [*messages[: current.entry_start], ModelRequest(parts=[UserPromptPart(block)]), *messages[current.entry_start :]]

    return process
