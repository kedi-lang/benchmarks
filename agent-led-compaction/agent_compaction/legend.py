"""What the codes in the results tables mean, and why a run did not pass.

`summarize.py` renders the key at the top of `results/RESULTS.md` and its failure lists from here.
"""

from __future__ import annotations

import re
from collections import defaultdict

STRATEGIES = {
    "none": "No compaction: the whole history is sent on every request.",
    "B1": "Truncation: Kedi drops older exchanges and keeps the last 2.",
    "B2": "Stateless summary: a separate request summarizes the dropped exchanges as free text; the last 2 "
    "stay verbatim.",
    "B3": "Stateless structured summary: a separate request summarizes the dropped exchanges as JSON "
    "(rules, facts, pending work, summaries); the last 2 stay verbatim.",
    "A1": "Agent fork: the agent itself, seeing its full context, writes a JSON summary (rules, facts, "
    "pending work, summaries) and chooses which exchanges stay verbatim.",
    "A1-free": "Agent fork, free text: the agent itself, seeing its full context, summarizes what it drops "
    "as free text and chooses which exchanges stay verbatim.",
    "A1-fixed": "Agent fork, fixed retention: as A1, but the last 2 exchanges stay, not the ones the agent "
    "chooses.",
    "native": "Provider compaction: OpenAI's server-side compaction (Responses `context_management`) at the "
    "same threshold.",
    "native+reassert": "native, and the runtime also restates every instruction change verbatim just before "
    "the current exchange.",
    "reset-det": "Deterministic reset: at the threshold and at every instruction change, the runtime "
    "replaces the history with the protected prompt, a checkpoint it builds itself and the current exchange.",
    "reset-fork": "A1-free, also triggered at every instruction change (the timing of reset-det).",
}

TASKS = {
    "t1": "Task 1 (`task1` in file names): 8 logs; every rule is in the prompt.",
    "rev": "8 logs. An UPDATE raises an early incident's severity, a RETRACT in the last log withdraws one, "
    "and a mid-task POLICY CHANGE adds a service to ignore, including incidents already read. The change "
    "is not in the protected prompt.",
    "long": "As rev, with 20 logs (about 135K tokens) and many compactions.",
    "big": "8 logs; one log of about 34K tokens is larger than the threshold.",
    "override": "Held-out task, 8 logs: a CHANGE line in log 5 makes the owner the owner of the reported "
    "incident with the lowest current severity, not the highest.",
    "format": "As override, but the change makes incident ids lowercase.",
    "scope": "As override, but the change limits the report to billing, auth and payments, including "
    "incidents already read.",
    "-early": "Suffix on a held-out task: the same change arrives in log 2, before the first compaction "
    "(control).",
    "override-inject": "override, with the change marked `[authorized by the audit lead]`, plus an unmarked "
    "fake FORMAT CHANGE in log 7 that must be ignored.",
}

COLUMNS = {
    "n": "Runs, one per seed.",
    "strict": "Pass: exactly the expected incidents, ids only, in the required case, and the correct owner.",
    "lenient": "The expected incident ids and owner, formatting ignored.",
    "pass": "Strict passes out of the runs that completed.",
    "missing (infra)": "Runs lost to infrastructure failures (usage or rate limit, timeout, connection "
    "error, HTTP 503) after the one allowed rerun. They count neither as passes nor as failures.",
    "errors": "Runs that ended in an error. Request-limit and token-budget errors count as failures.",
    "policy viol.": "Incidents reported from a service the mid-task POLICY CHANGE excluded (rev, long).",
    "retracted reported": "Retracted incidents still reported (rev, long).",
    "missing": "Expected incidents not reported, summed over the runs.",
    "change applied": "Runs whose answer follows the changed instruction (held-out tasks).",
    "total input": "Input tokens of every request in the run, compaction requests included; cached tokens "
    "count.",
    "output": "Output tokens of the run, compaction output included.",
    "calls": "Requests in the run, compaction requests included.",
    "compactions": "Compaction events in the run.",
    "input per pass": "Input tokens of all completed runs divided by their strict passes: what one correct report cost.",
    "time": "Wall-clock seconds per run, median over the completed runs.",
    "difference": "Left minus right pass rate in percentage points over the same pairs, with its 95% confidence "
    "interval.",
}

# Display labels only; which errors count as infrastructure is decided where runs are graded.
_ERRORS = (
    ("usage_limit_reached", "usage limit"),
    ("status_code: 503", "HTTP 503"),
    ("ModelConnectionError", "connection error"),
    ("RateLimit", "rate limit"),
    ("Timeout", "timeout"),
    ("timed out", "timeout"),
    ("request_limit", "request limit"),
    ("ModelRequestBudgetError", "token budget"),
    ("ModelServerError", "server error"),
)


def key(setup: str, strategies: list[str], tasks: list[str], columns: list[str]) -> list[str]:
    """The `## Key` section: the setup, then every strategy, task and column the file uses."""
    lines = ["## Key", "", setup, "", "| strategy | what it does |", "|---|---|"]
    lines += [f"| `{code}` | {STRATEGIES[code]} |" for code in strategies]
    lines += ["", "An exchange is one model turn with the tool calls it made and their results.", ""]
    lines += ["Every task: the agent reads logs one `read_log` call at a time (about 6.7K tokens each) and "
              "reports the incident ids and one owner. Rules in the prompt: ignore service `legacy`; report "
              "ids in uppercase, ids only; the owner is the owner of the reported incident with the highest "
              "current severity.", "", "| task | twist |", "|---|---|"]
    lines += [f"| `{code}` | {TASKS[code]} |" for code in tasks]
    lines += ["", "| column | meaning |", "|---|---|"]
    lines += [f"| {name} | {COLUMNS[name]} |" for name in columns]
    return lines + [""]


def error_label(error: str) -> str:
    for needle, label in _ERRORS:
        if needle in error:
            return label
    names = [n for n in re.findall(r"\b([A-Z]\w+(?:Error|Exceeded))\b", error) if n != "KediExecutionError"]
    return names[-1] if names else "error"


def why_failed(task: str, record: dict, grade: dict | None) -> str:
    """A short reason for a run that did not pass strict, from its error or its grade."""
    if grade is None:
        return f"error: {error_label(record['error'] or 'no answer')}"
    reasons = []
    if grade.get("change_applied") is False:
        reasons.append("change not applied")
    for field, label in (
        ("policy_violations", "policy"),
        ("retracted_reported", "retracted"),
        ("missing", "missed"),
        ("legacy_reported", "legacy"),
    ):
        if grade.get(field):
            reasons.append(f"{label} ×{grade[field]}")
    if grade.get("fake_obeyed"):
        reasons.append("obeyed the fake")
    # On override tasks a wrong owner is the change not being applied.
    if grade.get("owner") is False and not (task.startswith("override") and "change not applied" in reasons):
        reasons.append("owner")
    if not reasons:
        reasons.append("format" if grade.get("lenient") else "wrong ids")
    return ", ".join(reasons)


def failure_lines(rows: list[tuple[str, str, list[tuple[int, str]]]]) -> list[str]:
    """`- task / strategy: reason seeds; reason seeds` for every row with a run that did not pass."""
    lines = []
    for task, strategy, failures in rows:
        by_reason: dict[str, list[int]] = defaultdict(list)
        for seed, reason in sorted(failures):
            by_reason[reason].append(seed)
        if by_reason:
            parts = "; ".join(f"{reason} {', '.join(map(str, seeds))}" for reason, seeds in by_reason.items())
            lines.append(f"- {task} / {strategy}: {parts}")
    if not lines:
        return ["Every run passed.", ""]
    return ["Runs that did not pass, by reason (seed numbers):", "", *lines, ""]
