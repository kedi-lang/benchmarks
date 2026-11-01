import pytest

from benchmarks.agent_compaction.normalizer import (
    BLOCK,
    Group,
    Proposal,
    ProposalError,
    Summary,
    normalize,
    parse_proposal,
    render_block,
)

GROUPS = [
    Group("g0", protected=True),  # system/instructions
    Group("g1"),
    Group("g2"),
    Group("g3"),
    Group("g4"),
    Group("g5", current=True),
]


def test_block_sits_at_the_first_dropped_group_and_kept_groups_keep_original_order():
    layout = normalize(GROUPS, Proposal(keep=("g4", "g1"), summaries=(Summary("s", ("g2",)),)))
    assert layout.segments == ["g0", "g1", BLOCK, "g4", "g5"]
    assert layout.prefix_groups == 2
    assert layout.reordered is True
    assert layout.dropped == ["g2", "g3"]
    assert layout.uncovered == ["g3"]


def test_protected_unclosed_and_current_groups_are_forced():
    groups = [Group("a", protected=True), Group("b", closed=False), Group("c"), Group("d", current=True)]
    layout = normalize(groups, Proposal(keep=()))
    assert layout.forced == ["a", "b", "d"]
    assert layout.segments == ["a", "b", BLOCK, "d"]


def test_unknown_ids_are_rejected_and_covers_of_kept_groups_ignored():
    with pytest.raises(ProposalError, match="unknown group ids: g9"):
        normalize(GROUPS, Proposal(keep=("g9",)))
    layout = normalize(GROUPS, Proposal(keep=("g1",), summaries=(Summary("s", ("g1", "g2")),)))
    assert layout.uncovered == ["g3", "g4"]


def test_nothing_dropped_has_no_block():
    layout = normalize(GROUPS, Proposal(keep=tuple(g.group_id for g in GROUPS)))
    assert BLOCK not in layout.segments and layout.dropped == []


def test_parse_proposal_validates_shapes():
    proposal = parse_proposal(
        {"keep": ["g1"], "summaries": [{"text": "t", "covers": ["g2"]}], "rules": ["r"]}
    )
    assert proposal.summaries[0].covers == ("g2",)
    with pytest.raises(ProposalError):
        parse_proposal({"keep": "g1"})
    with pytest.raises(ProposalError):
        parse_proposal({"keep": [], "summaries": [{"covers": []}]})


def test_rendered_block_puts_rules_first_and_names_the_archive():
    proposal = Proposal(keep=(), rules=("never touch /etc",), facts=("port is 8123",))
    layout = normalize(GROUPS, proposal)
    text = render_block(proposal, layout, archive_ref="artifact:history-1")
    assert text.index("Rules") < text.index("Facts")
    assert "artifact:history-1" in text
