"""Regenerate results/RESULTS.md (phases 1–5) from the raw records, so every published number traces to data.

    .venv/bin/python -m agent_compaction.summarize
"""

from __future__ import annotations

import json
import re
import statistics
from math import comb
from pathlib import Path

from . import legend, task1, task2

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
OUT = ROOT / "results" / "RESULTS.md"

PHASES = [
    ("phase2_task1_baselines", "Phase 2 — task 1 baselines", "The first comparison."),
    (
        "phase3_task1_ablation",
        "Phase 3 — task 1 ablation",
        "Task 1 again, to separate the fork's ingredients: summary schema (A1 vs A1-free) and who chooses "
        "what stays (A1 vs A1-fixed), next to the stateless summaries.",
    ),
    ("phase4_edge_cases", "Phase 4 — edge cases", "Tasks built to break the fork: rev, long and big."),
    (
        "phase5_native",
        "Phase 5 — provider (native) compaction",
        "The harness attached OpenAI's compaction capability directly (`legacy_native`), before Kedi's "
        "native path took over in phase 6.",
    ),
]
ORDER = ["none", "B1", "B2", "B3", "native", "A1-fixed", "A1", "A1-free"]
COLUMNS = [
    "n", "strict", "lenient", "total input", "calls", "compactions", "errors", "policy viol.",
    "retracted reported", "missing",
]
SETUP = (
    "Phases 1–5 are exploratory: they were designed and run before any pre-registration, and many "
    "comparisons were made, so their p-values describe these runs and test no hypothesis (the "
    "pre-registered tests are in `PHASES_6_10.md`). The model is `gpt-6-luna` at reasoning effort medium. "
    "Every strategy compacts at an estimate of 18K tokens. Seeds 1–5 give the same five scenarios to every "
    "strategy. Kedi and library versions per phase are in `environment.json`. The `calls` and "
    "`compactions` columns list one value per seed, in seed order."
)


def _load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _task_of(path: Path) -> str:
    return path.name.split("_")[0]


def _strategy_of(path: Path) -> str:
    return path.stem.split("_")[-1]


def _grade(task: str, record: dict) -> dict | None:
    """The grade recomputed from the stored answer (one grader for every phase); None without an answer."""
    answer = record["answer"]
    if not answer:
        return None
    if task == "task1":
        want = task1.expected(record["seed"])
        raw = [str(x) for x in answer.get("incidents", [])]
        ids = sorted({m.upper() for x in raw for m in re.findall(r"inc-\d+", x, re.IGNORECASE)})
        legacy = {i.incident_id.upper() for i in task1.incidents(record["seed"]) if i.service == "legacy"}
        owner = answer.get("owner") == want["owner"]
        return {
            "strict": sorted(raw) == want["incidents"] and owner,
            "lenient": ids == want["incidents"] and owner,
            "owner": owner,
            "missing": len(set(want["incidents"]) - set(ids)),
            "legacy_reported": len(legacy & set(ids)),
        }
    return task2.grade(task2.scenario(task, record["seed"]), answer)


def _passed(task: str, record: dict) -> bool:
    grade = _grade(task, record)
    return bool(grade and grade["strict"])


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
    if strategy in {"none", "B1"}:  # phase 3 did not rerun them
        sources[0] = ("phase2_task1_baselines", "task1")
    if strategy == "native":
        sources = [("phase5_native", t) for _, t in sources]
    out: dict[tuple[str, int], bool] = {}
    for folder, task in sources:
        for path in (RECORDS / folder).glob(f"{task}_*{strategy}.jsonl"):
            if _strategy_of(path) != strategy:
                continue
            for record in _load(path):
                out[(task, record["seed"])] = _passed(task, record)
    return out


def _row(task: str, strategy: str, records: list[dict]) -> str:
    grades = [_grade(task, r) or {} for r in records]
    total_input = [r["usage"]["input"] + (r["usage"].get("compaction_input") or 0) for r in records]
    # Separate compaction requests add calls; native compaction happens inside a normal request.
    calls = [
        r["usage"]["requests"] + sum(1 for e in r["compactions"] if e.get("endpoint") != "inline")
        for r in records
    ]
    n = len(records)
    return (
        f"| {task} | {strategy} | {n} | {sum(bool(g.get('strict')) for g in grades)}/{n} "
        f"| {sum(bool(g.get('lenient')) for g in grades)}/{n} | {int(statistics.median(total_input)) // 1000}K "
        f"| {calls} | {[len(r['compactions']) for r in records]} | {sum(1 for r in records if r['error'])} "
        f"| {sum(g.get('policy_violations', 0) for g in grades)} | {sum(g.get('retracted_reported', 0) for g in grades)} "
        f"| {sum(g.get('missing', 0) for g in grades)} |"
    )


def _cache_probe() -> list[str]:
    runs: list[dict] = []
    for row in _load(RECORDS / "phase1_cache_probe" / "probe_runs.jsonl"):
        if "mode" in row:
            runs.append({"mode": row["mode"], "date": row["date"], "cached": {}})
        else:
            runs[-1]["cached"][row["request"]] = row["cached_%"]
    lines = [
        "## Phase 1 — does the fork reuse the conversation's cached prefix?",
        "",
        f"Records: `records/phase1_cache_probe/probe_runs.jsonl`, a rerun on {runs[0]['date'][:10]} with raw "
        "records; the first run left only notes. A toy history of 3 turns (about 26K tokens) with two "
        "tools and one cache key per run, sent three times as it is (`default`) and three times after two "
        "growth turns (`--grow`). Each row is a request kind: R1 warm-up, R2 an ordinary follow-up, R3 the "
        "fork (the same prefix plus one appended message, JSON reply), R4 the fork with an extra output "
        "tool, R5 a kept prefix with the compaction block, R6 the block alone. Cached is the share of the "
        "request's input tokens read from the provider cache.",
        "",
        "| request | runs with ≥ 50% cached | cached % per run |",
        "|---|---|---|",
    ]
    for kind in dict.fromkeys(k for run in runs for k in run["cached"]):
        values = [(run["mode"], run["cached"][kind]) for run in runs if kind in run["cached"]]
        modes = dict.fromkeys(mode for mode, _ in values)
        per_run = "; ".join(f"{mode}: {', '.join(f'{v:g}' for m, v in values if m == mode)}" for mode in modes)
        lines.append(f"| {kind} | {sum(v >= 50 for _, v in values)}/{len(values)} | {per_run} |")
    return lines + [
        "",
        "`REPORT.md` §3 reports the first run's notes. This rerun does not reproduce them, so no cache claim is "
        "made (`FINDINGS.md` §8b).",
        "",
    ]


def _breakdown() -> list[str]:
    tasks = ["task1", "rev", "long", "big"]
    lines = [
        "## Pooled strict pass",
        "",
        "One row per strategy over the same (task, seed) scenarios: task 1 from phase 3 (phase 2 for none and "
        "B1, which phase 3 did not rerun), the edge cases from phase 4, and every native run from phase 5. "
        "B1 and A1-fixed ran on task 1 only, so their totals cover 5 runs, not 20.",
        "",
        "| strategy | task 1 | rev | long | big | rev + long | all |",
        "|---|---|---|---|---|---|---|",
    ]

    def cell(values: list[bool]) -> str:
        return f"{sum(values)}/{len(values)}" if values else "–"

    for strategy in ORDER:
        results = _paired(strategy)
        cells = [cell([v for (t, _), v in results.items() if t == task]) for task in tasks]
        cells.append(cell([v for (t, _), v in results.items() if t in {"rev", "long"}]))
        cells.append(cell(list(results.values())))
        lines.append(f"| `{strategy}` | {' | '.join(cells)} |")
    return lines + [""]


def main() -> None:
    lines = ["# Phases 1–5 — results", "", "Generated by `summarize.py` from `records/`; do not edit by hand.", ""]
    lines += legend.key(SETUP, ORDER, ["t1", "rev", "long", "big"], COLUMNS)
    lines += _cache_probe()
    for folder, title, note in PHASES:
        lines += [
            f"## {title}",
            "",
            f"{note} Records: `records/{folder}/`.",
            "",
            "| task | strategy | n | strict | lenient | median total input | calls | compactions | errors | policy viol. | retracted reported | missing |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ]
        files = sorted((RECORDS / folder).glob("*.jsonl"))
        failures = []
        for task in dict.fromkeys(_task_of(f) for f in files):
            for strategy in ORDER:
                path = next((f for f in files if _task_of(f) == task and _strategy_of(f) == strategy), None)
                if path is None:
                    continue
                records = _load(path)
                lines.append(_row(task, strategy, records))
                failures.append(
                    (task, strategy, [(r["seed"], legend.why_failed(task, r, _grade(task, r))) for r in records if not _passed(task, r)])
                )
        lines += ["", *legend.failure_lines(failures)]
    lines += _breakdown()
    lines += [
        "Paired comparisons (exploratory): exact one-sided McNemar on the same (task, seed) scenarios.",
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
    lines += ["", "Unpaired one-sided Fisher exact (exploratory; ignores the pairing):", ""]
    pooled = {strategy: list(_paired(strategy).values()) for strategy in ORDER}
    for left, right in [("A1-free", "none"), ("A1-free", "B2"), ("A1-free", "B3"), ("A1-free", "native")]:
        a, b = pooled[left], pooled[right]
        lines.append(f"- {left} vs {right}: p = {_fisher_greater(sum(a), len(a), sum(b), len(b)):.4f}")
    fork, stateless = pooled["A1"] + pooled["A1-free"], pooled["B2"] + pooled["B3"]
    p = _fisher_greater(sum(fork), len(fork), sum(stateless), len(stateless))
    lines.append(f"- fork (A1 + A1-free) {sum(fork)}/{len(fork)} vs stateless (B2 + B3) {sum(stateless)}/{len(stateless)}: p = {p:.2e}")
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
