"""Values the Kedi program's Python prelude reads; the runner sets them before each run."""

from __future__ import annotations

from typing import Any

from . import task1, task2

PROCESSOR: Any = None
CONDITION: Any = None
SEED = 0
TASK = task1.TASK
SCENARIO: Any = None  # a task2.Scenario, or None for task 1


def read_log(name: str) -> str:
    """Read one service log by name, e.g. log_1."""
    if SCENARIO is not None:
        return task2.log_text(SCENARIO, name)
    return task1.log_text(SEED, name)


read_log.__kedi_tool_risk__ = "read_only"  # type: ignore[attr-defined]
