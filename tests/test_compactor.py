import pytest

from agent_compaction.compactor import FORK_PROMPT, FREE, KEEP, _recent_keep
from agent_compaction.normalizer import BLOCK, Group, Proposal, ProposalError, normalize

GROUPS = [
    Group("g0", protected=True),  # system/instructions
    Group("g1"),
    Group("g2"),
    Group("g3"),
    Group("g4"),
    Group("g5", current=True),
]


def test_recent_count_keeps_the_latest_groups_and_the_protected_ones():
    layout = normalize(GROUPS, Proposal(keep=tuple(_recent_keep(GROUPS, 2))))
    assert layout.segments == ["g0", BLOCK, "g4", "g5"]
    assert layout.dropped == ["g1", "g2", "g3"]


def test_recent_count_zero_keeps_only_forced_groups_and_a_count_past_the_start_keeps_all():
    assert normalize(GROUPS, Proposal(keep=tuple(_recent_keep(GROUPS, 0)))).dropped == ["g1", "g2", "g3", "g4"]
    assert normalize(GROUPS, Proposal(keep=tuple(_recent_keep(GROUPS, 99)))).dropped == []


@pytest.mark.parametrize("count", [None, True, -1, "2", 2.5])
def test_recent_count_must_be_a_non_negative_integer(count):
    with pytest.raises(ProposalError):
        _recent_keep(GROUPS, count)


def test_recent_prompt_asks_for_a_count_not_for_ids():
    prompt = FORK_PROMPT.format(keep=KEEP["recent"], fields=FREE, index="g0: 10, task")
    assert '"keep_recent"' in prompt and '"keep":' not in prompt
