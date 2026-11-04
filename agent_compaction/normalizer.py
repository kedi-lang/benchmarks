"""Turn a model's compaction proposal into a safe, cache-friendly history layout.

The model proposes which groups to keep and what to summarize; Kedi decides the layout:
forced keeps, original order for verbatim groups, and the compaction block placed at the
first dropped group so everything before it stays byte-identical (and cached).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Group:
    group_id: str
    protected: bool = False
    closed: bool = True
    current: bool = False  # the group of the request being made now
    tokens: int = 0


@dataclass(frozen=True)
class Summary:
    text: str
    covers: tuple[str, ...] = ()


@dataclass(frozen=True)
class Proposal:
    keep: tuple[str, ...]
    summaries: tuple[Summary, ...] = ()
    rules: tuple[str, ...] = ()
    facts: tuple[str, ...] = ()
    pending: tuple[str, ...] = ()


class ProposalError(ValueError):
    """The proposal references groups that do not exist; the model gets this text back."""


BLOCK = "__compaction_block__"


@dataclass
class Layout:
    """Ordered segments: group ids, and BLOCK where the compaction message goes."""

    segments: list[str]
    dropped: list[str]
    forced: list[str] = field(default_factory=list)
    reordered: bool = False  # the model listed kept groups out of original order
    uncovered: list[str] = field(default_factory=list)  # dropped, not covered by any summary
    prefix_groups: int = 0  # verbatim groups before the block (cache-preserved)


def parse_proposal(data: dict[str, Any]) -> Proposal:
    def strings(key: str) -> tuple[str, ...]:
        value = data.get(key, [])
        if not isinstance(value, list) or not all(isinstance(item, str) for item in value):
            raise ProposalError(f"`{key}` must be a list of strings")
        return tuple(value)

    summaries = data.get("summaries", [])
    if not isinstance(summaries, list):
        raise ProposalError("`summaries` must be a list")
    parsed = []
    for item in summaries:
        if not isinstance(item, dict) or not isinstance(item.get("text"), str):
            raise ProposalError("each summary needs a `text` string")
        covers = item.get("covers", [])
        if not isinstance(covers, list) or not all(isinstance(c, str) for c in covers):
            raise ProposalError("summary `covers` must be a list of group ids")
        parsed.append(Summary(item["text"], tuple(covers)))
    return Proposal(
        keep=strings("keep"),
        summaries=tuple(parsed),
        rules=strings("rules"),
        facts=strings("facts"),
        pending=strings("pending"),
    )


def normalize(groups: list[Group], proposal: Proposal) -> Layout:
    known = {group.group_id for group in groups}
    referenced = set(proposal.keep) | {c for s in proposal.summaries for c in s.covers}
    unknown = sorted(referenced - known)
    if unknown:
        raise ProposalError(f"unknown group ids: {', '.join(unknown)}")

    forced = [
        g.group_id
        for g in groups
        if (g.protected or not g.closed or g.current) and g.group_id not in proposal.keep
    ]
    keep = set(proposal.keep) | set(forced)
    order = [g.group_id for g in groups]
    listed = [gid for gid in proposal.keep if gid in known]
    reordered = listed != sorted(listed, key=order.index)

    dropped = [gid for gid in order if gid not in keep]
    covered = {c for s in proposal.summaries for c in s.covers} - keep

    segments: list[str] = []
    prefix_groups = 0
    placed = False
    for gid in order:
        if gid in keep:
            segments.append(gid)
            if not placed:
                prefix_groups += 1
        elif not placed:
            segments.append(BLOCK)
            placed = True
    return Layout(
        segments=segments,
        dropped=dropped,
        forced=forced,
        reordered=reordered,
        uncovered=[gid for gid in dropped if gid not in covered],
        prefix_groups=prefix_groups,
    )


def render_block(proposal: Proposal, layout: Layout, archive_ref: str | None = None) -> str:
    """The single compaction message, highest-priority content first."""
    parts = ["[Compacted history]"]
    if proposal.rules:
        parts.append("Rules:\n" + "\n".join(f"- {r}" for r in proposal.rules))
    if proposal.facts:
        parts.append("Facts and decisions:\n" + "\n".join(f"- {f}" for f in proposal.facts))
    if proposal.pending:
        parts.append("Pending work:\n" + "\n".join(f"- {p}" for p in proposal.pending))
    if proposal.summaries:
        parts.append("Summaries:\n" + "\n".join(f"- {s.text}" for s in proposal.summaries))
    if layout.uncovered:
        parts.append("Archived without summary: " + ", ".join(layout.uncovered))
    if archive_ref:
        parts.append(f"Full dropped history is archived as {archive_ref}.")
    return "\n\n".join(parts)
