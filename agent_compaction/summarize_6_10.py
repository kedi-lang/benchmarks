"""Regenerate results/PHASES_6_10.md: phases 6–10 (held-out tests, scope supplement, reset/reassert, more
seeds, second models).

    .venv/bin/python -m agent_compaction.summarize_6_10

The last attempt per (task, strategy, seed) counts; infrastructure failures that remain after the single
allowed rerun are reported as missing, not as strategy failures.
"""

from __future__ import annotations

import json
import statistics
from math import comb
from pathlib import Path

from . import legend, task2, task3

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
OUT = ROOT / "results" / "PHASES_6_10.md"
# A 503 (server unavailable) is infrastructure like a connection error: the request was not served.
INFRA = ("RateLimit", "Timeout", "usage_limit_reached", "ModelConnectionError", "status_code: 503")
FORKS = {"A1", "A1-free", "A1-fixed", "B2", "B3"}  # strategies whose compaction is a separate request
SETUP = (
    "Every strategy compacts at an estimate of 18K tokens. The model is `gpt-6-luna` at reasoning effort "
    "medium unless a section names another. Each section names its records, its seeds and whether it was "
    "pre-registered. Token and call columns are medians over the runs that completed. Paired comparisons "
    "use the exact McNemar test on (task, seed) pairs and drop a pair with a missing side. Role: *primary* "
    "tests a pre-registered hypothesis; *secondary* and *descriptive* comparisons were named in the "
    "pre-registration without being hypotheses; *exploratory* ones were not pre-registered."
)


def _runs(folders: list[str], task: str, strategy: str) -> dict[int, dict]:
    out: dict[int, dict] = {}
    for folder in folders:
        path = RECORDS / folder / f"{task}_t18k_{strategy}.jsonl"
        if path.exists():
            for line in path.read_text().splitlines():
                record = json.loads(line)
                out[record["seed"]] = record
    return out


def _grade(task: str, seed: int, answer: dict) -> dict:
    if task in task3.VARIANTS:
        return task3.grade(task3.scenario(task, seed), answer)
    return task2.grade(task2.scenario(task, seed), answer)


def _outcomes(runs: dict[int, dict], task: str) -> dict[int, bool | None]:
    out: dict[int, bool | None] = {}
    for seed, record in runs.items():
        if record["error"] and any(word in record["error"] for word in INFRA):
            out[seed] = None
        else:
            out[seed] = bool(record["answer"]) and _grade(task, seed, record["answer"])["strict"]
    return out


def _mcnemar(a: dict, b: dict) -> tuple[int, int, int, float, float]:
    keys = [k for k in a.keys() & b.keys() if a[k] is not None and b[k] is not None]
    x = sum(1 for k in keys if a[k] and not b[k])
    y = sum(1 for k in keys if b[k] and not a[k])
    n = x + y
    one = sum(comb(n, i) for i in range(x, n + 1)) / 2**n if n else 1.0
    two = min(1.0, 2 * sum(comb(n, i) for i in range(0, min(x, y) + 1)) / 2**n) if n else 1.0
    return len(keys), x, y, one, two


def _medians(records: list[dict]) -> str:
    if not records:
        return "– | – | –"
    total_in = statistics.median(r["usage"]["input"] + (r["usage"].get("compaction_input") or 0) for r in records)
    total_out = statistics.median(
        r["usage"]["output"] + sum((e.get("output") or 0) for e in r["compactions"]) for r in records
    )
    calls = statistics.median(
        r["usage"]["requests"] + sum(1 for e in r["compactions"] if e.get("strategy") in FORKS) for r in records
    )
    return f"{int(total_in) // 1000}K | {int(total_out)} | {calls:g}"


def _table(
    title: str,
    note: str,
    folders: list[str],
    tasks: list[str],
    strategies: list[str],
    left: str,
    roles: dict[str, str] | None = None,
) -> list[str]:
    lines = [
        f"## {title}",
        "",
        note,
        "",
        "| task | strategy | pass | missing (infra) | policy viol. | change applied | median total input | median output | median calls |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    pooled: dict[str, dict] = {}
    failures = []
    for task in tasks:
        held_out = task in task3.VARIANTS
        for strategy in strategies:
            runs = _runs(folders, task, strategy)
            if not runs:
                continue
            outcomes = _outcomes(runs, task)
            pooled.setdefault(strategy, {}).update({(task, k): v for k, v in outcomes.items()})
            done = [seed for seed, v in outcomes.items() if v is not None]
            grades = {seed: _grade(task, seed, runs[seed]["answer"]) for seed in done if runs[seed]["answer"]}
            viol = "–" if held_out else sum(g.get("policy_violations", 0) for g in grades.values())
            applied = sum(1 for g in grades.values() if g.get("change_applied")) if held_out else "–"
            lines.append(
                f"| {task} | {strategy} | {sum(bool(outcomes[s]) for s in done)}/{len(done)} "
                f"| {len(runs) - len(done)} | {viol} | {applied} | {_medians([runs[s] for s in done])} |"
            )
            failures.append(
                (
                    task,
                    strategy,
                    [
                        (seed, f"missing ({legend.error_label(runs[seed]['error'])})")
                        if v is None
                        else (seed, legend.why_failed(task, runs[seed], grades.get(seed)))
                        for seed, v in outcomes.items()
                        if not v
                    ],
                )
            )
    lines += ["", *legend.failure_lines(failures)]
    lines += [
        f"Paired exact McNemar, {left} vs each, pooled over the tasks above:",
        "",
        "| comparison | role | pairs | left only | right only | p one-sided | p two-sided |",
        "|---|---|---|---|---|---|---|",
    ]
    for strategy in strategies:
        if strategy != left and strategy in pooled and left in pooled:
            n, x, y, one, two = _mcnemar(pooled[left], pooled[strategy])
            role = (roles or {}).get(strategy, "exploratory")
            lines.append(f"| {left} vs {strategy} | {role} | {n} | {x} | {y} | {one:.4f} | {two:.4f} |")
    return lines + [""]


def _probe(label: str, folders: list[str], tasks: list[str]) -> list[str]:
    lines = [f"Rule-recall probe on failed runs ({label}), asked after the final report:", ""]
    for strategy in ("native", "A1-free", "B3", "none"):
        failed = recalled = 0
        for task in tasks:
            for seed, record in _runs(folders, task, strategy).items():
                if record["answer"] and not _grade(task, seed, record["answer"])["strict"] and record.get("probe"):
                    failed += 1
                    recalled += bool(record["probe"]["recalls_change"])
        lines.append(f"- {strategy}: {recalled}/{failed} failed runs named the changed instruction")
    return lines + [""]


def _fake_obeyed(folders: list[str], task: str, strategies: list[str]) -> list[str]:
    lines = ["Fake instruction obeyed (secondary, descriptive), out of the completed runs:", ""]
    for strategy in strategies:
        runs = _runs(folders, task, strategy)
        done = [seed for seed, v in _outcomes(runs, task).items() if v is not None]
        obeyed = sum(
            1 for seed in done if runs[seed]["answer"] and _grade(task, seed, runs[seed]["answer"])["fake_obeyed"]
        )
        lines.append(f"- {strategy}: {obeyed}/{len(done)}")
    return lines + [""]


def main() -> None:
    heldout = ["override", "format", "scope"]
    early = ["override-early", "format-early", "scope-early"]
    s6 = ["A1-free", "native", "B3", "none"]
    s7 = ["A1-free", "native", "native+reassert", "reset-det", "reset-fork", "none"]
    p6, p9, p10 = (
        "`protocol/PREREGISTRATION.md`",
        "`protocol/PREREGISTRATION_PHASE9.md`",
        "`protocol/PREREGISTRATION_PHASE10.md`",
    )
    lines = ["# Phases 6–10 — results", "", "Generated by `summarize_6_10.py` from `records/`; do not edit by hand.", ""]
    lines += legend.key(
        SETUP,
        ["A1-free", "native", "native+reassert", "B3", "reset-det", "reset-fork", "none"],
        ["override", "format", "scope", "-early", "override-inject", "rev", "long"],
        ["pass", "missing (infra)", "policy viol.", "change applied", "total input", "output", "calls"],
    )
    lines += _table(
        "Phase 6 — held-out test, instruction change after the first compaction (k = 5)",
        f"Pre-registered ({p6}). H1: A1-free passes more often than native, pooled over the three tasks. "
        "Seeds 101–115. Records: `records/phase6_heldout/`, which also keeps the first attempts that hit the "
        "usage limit.",
        ["phase6_heldout"], heldout, s6, "A1-free",
        {"native": "primary (H1)", "B3": "secondary", "none": "secondary"},
    )
    lines += _probe("H3, pre-registered", ["phase6_heldout"], heldout)
    lines += _table(
        "Phase 6 — control, instruction change before the first compaction (k = 2)",
        f"Pre-registered control (H2, {p6}): reported descriptively. Seeds 101–115. Records: "
        "`records/phase6_heldout/`.",
        ["phase6_heldout"], early, s6, "A1-free",
        {"native": "descriptive (H2)", "B3": "descriptive", "none": "descriptive"},
    )
    lines += _table(
        "Phase 6b — scope supplement (k = 5)",
        "Exploratory: outside the pre-registration, run because the pre-registered `scope` runs were lost to "
        "usage limits. Seeds 101–115. Records: `records/phase6b_scope_supplement/`.",
        ["phase6b_scope_supplement"], ["scope"], s6, "A1-free",
    )
    lines += _probe("exploratory", ["phase6b_scope_supplement"], ["scope"])
    lines += _table(
        "Phases 7 + 8 — reset and reassert, rev and long",
        "Exploratory. Seeds 1–5 (phase 7) and 6–15 (phase 8); rev seed 8 cannot be generated. Records: "
        "`records/phase7_reset_reassert/`, `records/phase8_more_seeds/`.",
        ["phase7_reset_reassert", "phase8_more_seeds"], ["rev", "long"], s7, "A1-free",
    )
    lines += _table(
        "Phases 7 + 8 — long only",
        "Exploratory: the `long` rows above, compared on their own.",
        ["phase7_reset_reassert", "phase8_more_seeds"], ["long"], s7, "A1-free",
    )
    lines += _table(
        "Phase 9 H4 — long horizon",
        f"Pre-registered ({p9}): one of three primary hypotheses, reported with and without a Holm "
        "correction. New seeds 201–215. Records: `records/phase9_prereg/`.",
        ["phase9_prereg"], ["long"], ["A1-free", "native", "native+reassert"], "A1-free",
        {"native": "primary (H4)", "native+reassert": "secondary"},
    )
    lines += _table(
        "Phase 9 H5 — second model, `gpt-6.1-terra` at effort low",
        f"Pre-registered ({p9}). The phase 6 task data (seeds 101–115) with another model. Records: "
        "`records/phase9_prereg/`.",
        ["phase9_prereg"], ["override", "format"], ["A1-free", "native"], "A1-free",
        {"native": "primary (H5)"},
    )
    lines += _table(
        "Phase 9 H6 — untrusted fake instruction in tool output",
        f"Pre-registered ({p9}). Seeds 101–115. Records: `records/phase9_prereg/`.",
        ["phase9_prereg"], ["override-inject"], ["A1-free", "native", "none"], "A1-free",
        {"native": "primary (H6)", "none": "secondary"},
    )
    lines += _fake_obeyed(["phase9_prereg"], "override-inject", ["A1-free", "native", "none"])
    lines += _table(
        "Phase 10 H7 — second model family, `deepseek/deepseek-v4.1-flash`",
        f"Pre-registered ({p10}), with a single primary: A1-free vs B3. Through OpenRouter, effort medium, "
        "seeds 401–415. Records: `records/phase10_prereg/`.",
        ["phase10_prereg"], ["long"], ["A1-free", "B3", "none"], "A1-free",
        {"B3": "primary (H7)", "none": "descriptive"},
    )
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
