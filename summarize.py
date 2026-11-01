"""Regenerate results/RESULTS.md from the raw records, so every published number traces to data.

    .venv/bin/python -m benchmarks.agent_compaction.summarize
"""

from __future__ import annotations

import json
import re
import statistics
from math import comb
from pathlib import Path

from . import task1, task2

ROOT = Path(__file__).parent
RECORDS = ROOT / "records"
OUT = ROOT / "results" / "RESULTS.md"

PHASES = [
    ("phase2_task1_baselines", "Phase 2 — task 1 baselines"),
    ("phase3_task1_ablation", "Phase 3 — task 1 ablation"),
    ("phase4_edge_cases", "Phase 4 — edge cases"),
    ("phase5_native", "Phase 5 — provider (native) compaction"),
]
ORDER = ["none", "B1", "B2", "B3", "native", "A1-fixed", "A1", "A1-free"]
DESCRIPTION = {
    "none": "no compaction",
    "B1": "truncation, keep last 2 groups",
    "B2": "stateless free-text summary, keep last 2",
    "B3": "stateless structured summary, keep last 2",
    "A1": "fork, structured, model selects kept groups",
    "A1-free": "fork, free text, model selects kept groups",
    "A1-fixed": "fork, structured, keep last 2",
    "native": "OpenAI server-side compaction (context_management), same trigger",
}


def _load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _task_of(path: Path) -> str:
    return path.name.split("_")[0]


def _strategy_of(path: Path) -> str:
    return path.stem.split("_")[-1]


def _grade(task: str, record: dict) -> dict:
    """Strict and lenient pass, recomputed from the stored answer (one grader for every phase)."""
    answer = record["answer"]
    if not answer:
        return {"strict": False, "lenient": False, "error": record["error"] or "no answer"}
    if task == "task1":
        want = task1.expected(record["seed"])
        raw = [str(x) for x in answer.get("incidents", [])]
        ids = sorted({m.upper() for x in raw for m in re.findall(r"inc-\d+", x, re.IGNORECASE)})
        owner = answer.get("owner") == want["owner"]
        return {
            "strict": sorted(raw) == want["incidents"] and owner,
            "lenient": ids == want["incidents"] and owner,
        }
    grade = task2.grade(task2.scenario(task, record["seed"]), answer)
    return {"strict": grade["strict"], "lenient": grade["lenient"], **grade}


def _fisher_greater(a: int, n1: int, b: int, n2: int) -> float:
    """One-sided Fisher exact test: P(first group >= a successes) under no difference."""
    k, n = a + b, n1 + n2
    return sum(comb(k, i) * comb(n - k, n1 - i) for i in range(a, min(k, n1) + 1)) / comb(n, n1)


def _mcnemar_greater(left: list[bool], right: list[bool]) -> tuple[int, int, float]:
    """Exact one-sided McNemar on paired runs: P(at least b of the b + c discordant pairs favor left)."""
    b = sum(1 for x, y in zip(left, right) if x and not y)
    c = sum(1 for x, y in zip(left, right) if y and not x)
    n = b + c
    return b, c, sum(comb(n, i) for i in range(b, n + 1)) / 2**n if n else 1.0


def _paired(strategy: str) -> dict[tuple[str, int], bool]:
    """Strict pass keyed by (task, seed), from the canonical phase of each task and strategy."""
    sources = [("phase3_task1_ablation", "task1"), ("phase4_edge_cases", "rev"), ("phase4_edge_cases", "long"), ("phase4_edge_cases", "big")]
    if strategy == "none":
        sources[0] = ("phase2_task1_baselines", "task1")
    if strategy == "native":
        sources = [("phase5_native", t) for _, t in sources]
    out: dict[tuple[str, int], bool] = {}
    for folder, task in sources:
        for path in (RECORDS / folder).glob(f"{task}_*{strategy}.jsonl"):
            if _strategy_of(path) != strategy:
                continue
            for record in _load(path):
                out[(task, record["seed"])] = _grade(task, record)["strict"]
    return out


def _row(task: str, strategy: str, records: list[dict]) -> dict:
    grades = [_grade(task, r) for r in records]
    total_input = [r["usage"]["input"] + (r["usage"].get("compaction_input") or 0) for r in records]
    # Separate compaction requests add calls; native compaction happens inside a normal request.
    calls = [
        r["usage"]["requests"]
        + sum(1 for e in r["compactions"] if e.get("endpoint") != "inline")
        for r in records
    ]
    return {
        "task": task,
        "strategy": strategy,
        "n": len(records),
        "strict": sum(g["strict"] for g in grades),
        "lenient": sum(g["lenient"] for g in grades),
        "median_input": int(statistics.median(total_input)),
        "calls": calls,
        "compactions": [len(r["compactions"]) for r in records],
        "errors": sum(1 for r in records if r["error"]),
        "policy_violations": sum(g.get("policy_violations", 0) for g in grades),
        "retracted_reported": sum(g.get("retracted_reported", 0) for g in grades),
        "missing": sum(g.get("missing", 0) for g in grades),
    }


def main() -> None:
    lines = [
        "# Agent-led compaction — results",
        "",
        "Generated by `summarize.py` from `records/`; do not edit by hand.",
        "Strict = ids only, uppercase, exact set, correct owner. Lenient = ids extracted, format ignored.",
        "Total input = main requests + compaction requests. Calls = main requests + compaction requests.",
        "",
    ]
    pooled: dict[str, list[bool]] = {}
    for folder, title in PHASES:
        lines += [f"## {title}", "", "| task | strategy | n | strict | lenient | median total input | calls | compactions | errors | policy viol. | retracted reported | missing |", "|---|---|---|---|---|---|---|---|---|---|---|---|"]
        files = sorted((RECORDS / folder).glob("*.jsonl"))
        for task in dict.fromkeys(_task_of(f) for f in files):
            for strategy in ORDER:
                path = next((f for f in files if _task_of(f) == task and _strategy_of(f) == strategy), None)
                if path is None:
                    continue
                records = _load(path)
                row = _row(task, strategy, records)
                lines.append(
                    f"| {task} | {strategy} | {row['n']} | {row['strict']}/{row['n']} | {row['lenient']}/{row['n']} "
                    f"| {row['median_input'] // 1000}K | {row['calls']} | {row['compactions']} | {row['errors']} "
                    f"| {row['policy_violations']} | {row['retracted_reported']} | {row['missing']} |"
                )
                if folder != "phase2_task1_baselines":
                    pooled.setdefault(strategy, []).extend(_grade(task, r)["strict"] for r in records)
        lines.append("")

    # Phase 2 is the earlier run of the same task-1 code path; pool phase 3 + 4 for the tests,
    # adding phase-2 `none` because phase 3 did not rerun it.
    none = _load(RECORDS / "phase2_task1_baselines" / "task1_none.jsonl")
    pooled.setdefault("none", []).extend(_grade("task1", r)["strict"] for r in none)
    lines += ["## Pooled strict pass (task 1 + edge cases)", "", "| strategy | description | pass |", "|---|---|---|"]
    for strategy in ORDER:
        if strategy in pooled:
            values = pooled[strategy]
            lines.append(f"| {strategy} | {DESCRIPTION[strategy]} | {sum(values)}/{len(values)} |")
    lines += [
        "",
        "Paired comparison on the same (task, seed) runs — exact one-sided McNemar (primary):",
        "",
        "| left | right | pairs | left only | right only | p |",
        "|---|---|---|---|---|---|",
    ]
    comparisons = [("A1-free", s) for s in ("none", "B2", "B3", "native", "A1")] + [("A1", "B3"), ("A1", "native")]
    for scope, tasks in (("all", None), ("rev+long", {"rev", "long"})):
        for left, right in comparisons:
            a, b = _paired(left), _paired(right)
            keys = sorted(k for k in a.keys() & b.keys() if tasks is None or k[0] in tasks)
            if not keys:
                continue
            only_left, only_right, p = _mcnemar_greater([a[k] for k in keys], [b[k] for k in keys])
            lines.append(f"| {left} | {right} ({scope}) | {len(keys)} | {only_left} | {only_right} | {p:.4f} |")
    lines += ["", "Unpaired one-sided Fisher exact (secondary, ignores pairing):", ""]
    pairs = [("A1-free", "none"), ("A1-free", "B2"), ("A1-free", "B3"), ("A1-free", "native")]
    for left, right in pairs:
        if left in pooled and right in pooled:
            a, b = pooled[left], pooled[right]
            p = _fisher_greater(sum(a), len(a), sum(b), len(b))
            lines.append(f"- {left} vs {right}: p = {p:.4f}")
    fork = pooled.get("A1", []) + pooled.get("A1-free", [])
    stateless = pooled.get("B2", []) + pooled.get("B3", [])
    if fork and stateless:
        p = _fisher_greater(sum(fork), len(fork), sum(stateless), len(stateless))
        lines.append(f"- fork (A1 + A1-free) {sum(fork)}/{len(fork)} vs stateless (B2 + B3) {sum(stateless)}/{len(stateless)}: p = {p:.2e}")
    # Rule adherence where a rule arrives mid-task (rev + long): only compaction can carry it.
    lines += ["", "Strict pass on rev + long (mid-task rule, retraction, update):", ""]
    for strategy in ORDER:
        folder = "phase5_native" if strategy == "native" else "phase4_edge_cases"
        values = [
            _grade(task, r)["strict"]
            for task in ("rev", "long")
            for path in [RECORDS / folder / f"{task}_t18k_{strategy}.jsonl"]
            if path.exists()
            for r in _load(path)
        ]
        if values:
            lines.append(f"- {strategy}: {sum(values)}/{len(values)}")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
