"""Regenerate results/RESULTS.md, every phase's tables, from the raw records, so every published number
traces to data.

    .venv/bin/python -m agent_compaction.summarize

The last attempt per (task, strategy, seed) counts; infrastructure failures that remain after the single
allowed rerun are reported as missing, not as strategy failures.
"""

from __future__ import annotations

import json
import math
import re
import statistics
from math import comb
from pathlib import Path

from . import legend, task1, task2, task3

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "records"
OUT = ROOT / "results" / "RESULTS.md"
# A 503 (server unavailable) is infrastructure like a connection error: the request was not served.
INFRA = ("RateLimit", "Timeout", "usage_limit_reached", "ModelConnectionError", "status_code: 503")
FORKS = {"A1", "A1-free", "A1-fixed", "B2", "B3"}  # strategies whose compaction is a separate request
STRATEGIES = ["none", "B1", "B2", "B3", "native", "native+reassert", "A1-fixed", "A1", "A1-free", "reset-det", "reset-fork"]
TASKS = ["t1", "rev", "long", "big", "override", "format", "scope", "-early", "override-inject"]
COLUMNS = [
    "pass", "lenient", "missing (infra)", "policy viol.", "change applied", "total input", "input per pass", "output",
    "calls", "compactions", "time", "difference",
]
SETUP = (
    "Every strategy compacts at an estimate of 18K tokens. The model is `gpt-6-luna` at reasoning effort "
    "medium unless a section names another. Each section names its records, its seeds and whether it was "
    "pre-registered: phases 6, 9 and 10 were; phases 1–5, 6b, 7 and 8 are exploratory, with many "
    "comparisons, so their p-values describe the runs and test no hypothesis. Seeds give every strategy "
    "the same scenarios. Token columns are medians over the runs that completed; calls and compactions "
    "show the median and, in brackets, the maximum. Paired comparisons use the exact McNemar test on "
    "(task, seed) pairs and drop a pair with a missing side; the difference in pass rate comes with a 95% "
    "confidence interval for paired proportions (Newcombe's method 10). Role: *primary* tests a pre-registered "
    "hypothesis; *secondary* and *descriptive* comparisons were named in the pre-registration without "
    "being hypotheses; *exploratory* ones were not pre-registered. Kedi and library versions per phase are "
    "in `environment.json`."
)


def _load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()]


def _runs(folders: list[str], task: str, strategy: str) -> dict[int, dict]:
    """The last attempt per seed; phases 2–3 name files `task1_<strategy>`, later ones add `_t18k`."""
    out: dict[int, dict] = {}
    for folder in folders:
        for name in (f"{task}_t18k_{strategy}.jsonl", f"{task}_{strategy}.jsonl"):
            path = RECORDS / folder / name
            if path.exists():
                out.update((record["seed"], record) for record in _load(path))
    return out


def _grade(task: str, seed: int, answer: dict) -> dict:
    """The grade recomputed from the stored answer, with one grader per task family for every phase."""
    if task in task3.VARIANTS:
        return task3.grade(task3.scenario(task, seed), answer)
    if task != "task1":
        return task2.grade(task2.scenario(task, seed), answer)
    want = task1.expected(seed)
    raw = [str(x) for x in answer.get("incidents", [])]
    ids = sorted({m.upper() for x in raw for m in re.findall(r"inc-\d+", x, re.IGNORECASE)})
    legacy = {i.incident_id.upper() for i in task1.incidents(seed) if i.service == "legacy"}
    owner = answer.get("owner") == want["owner"]
    return {
        "strict": sorted(raw) == want["incidents"] and owner,
        "lenient": ids == want["incidents"] and owner,
        "owner": owner,
        "missing": len(set(want["incidents"]) - set(ids)),
        "legacy_reported": len(legacy & set(ids)),
    }


def _outcomes(runs: dict[int, dict], task: str) -> dict[int, bool | None]:
    """Strict pass per seed; None for a run lost to infrastructure."""
    out: dict[int, bool | None] = {}
    for seed, record in runs.items():
        if record["error"] and any(word in record["error"] for word in INFRA):
            out[seed] = None
        else:
            out[seed] = bool(record["answer"]) and _grade(task, seed, record["answer"])["strict"]
    return out


def _wilson(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    p, d = k / n, 1 + z * z / n
    centre, half = p + z * z / (2 * n), z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return (centre - half) / d, (centre + half) / d


def _difference(both: int, left: int, right: int, neither: int) -> str:
    """Left minus right pass rate in points, with Newcombe's (1998, method 10) 95% interval for paired data."""
    n = both + left + right + neither
    if not n:
        return "–"
    p1, p2 = (both + left) / n, (both + right) / n
    l1, u1 = _wilson(both + left, n)
    l2, u2 = _wilson(both + right, n)
    margins = (both + left) * (right + neither) * (both + right) * (left + neither)
    phi = (both * neither - left * right) / math.sqrt(margins) if margins else 0.0
    low = math.sqrt((p1 - l1) ** 2 - 2 * phi * (p1 - l1) * (u2 - p2) + (u2 - p2) ** 2)
    high = math.sqrt((u1 - p1) ** 2 - 2 * phi * (u1 - p1) * (p2 - l2) + (p2 - l2) ** 2)
    diff = p1 - p2
    return f"{diff * 100:+.0f} ({(diff - low) * 100:.0f} to {(diff + high) * 100:.0f})"


def _mcnemar(a: dict, b: dict) -> tuple[int, int, int, float, float, str]:
    keys = [k for k in a.keys() & b.keys() if a[k] is not None and b[k] is not None]
    x = sum(1 for k in keys if a[k] and not b[k])
    y = sum(1 for k in keys if b[k] and not a[k])
    both = sum(1 for k in keys if a[k] and b[k])
    n = x + y
    one = sum(comb(n, i) for i in range(x, n + 1)) / 2**n if n else 1.0
    two = min(1.0, 2 * sum(comb(n, i) for i in range(0, min(x, y) + 1)) / 2**n) if n else 1.0
    return len(keys), x, y, one, two, _difference(both, x, y, len(keys) - both - x - y)


def _fisher_greater(a: int, n1: int, b: int, n2: int) -> float:
    """One-sided Fisher exact test: P(first group >= a successes) under no difference."""
    k, n = a + b, n1 + n2
    return sum(comb(k, i) * comb(n - k, n1 - i) for i in range(a, min(k, n1) + 1)) / comb(n, n1)


def _usage(records: list[dict], passes: int) -> str:
    if not records:
        return "– | – | – | – | – | –"
    inputs = [r["usage"]["input"] + (r["usage"].get("compaction_input") or 0) for r in records]
    total_in = statistics.median(inputs)
    per_pass = f"{sum(inputs) // passes // 1000}K" if passes else "–"
    total_out = statistics.median(
        r["usage"]["output"] + sum((e.get("output") or 0) for e in r["compactions"]) for r in records
    )
    calls = [r["usage"]["requests"] + sum(1 for e in r["compactions"] if e.get("strategy") in FORKS) for r in records]
    compactions = [len(r["compactions"]) for r in records]
    return (
        f"{int(total_in) // 1000}K | {per_pass} | {int(total_out)} | {statistics.median(calls):g} ({max(calls)}) "
        f"| {statistics.median(compactions):g} ({max(compactions)}) | {statistics.median(r['seconds'] for r in records):.0f} s"
    )


def _table(
    title: str,
    note: str,
    folders: list[str],
    tasks: list[str],
    strategies: list[str],
    left: str | None = None,
    roles: dict[str, str] | None = None,
) -> list[str]:
    lines = [
        f"## {title}",
        "",
        note,
        "",
        "| task | strategy | pass | lenient | missing (infra) | policy viol. | change applied | median total input | input per pass | median output | calls | compactions | median time |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|---|",
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
            # Only rev and long change the policy mid-task.
            viol = sum(g.get("policy_violations", 0) for g in grades.values()) if task in {"rev", "long"} else "–"
            applied = sum(1 for g in grades.values() if g.get("change_applied")) if held_out else "–"
            passes = sum(bool(outcomes[s]) for s in done)
            lines.append(
                f"| {task} | {strategy} | {passes}/{len(done)} "
                f"| {sum(bool(g['lenient']) for g in grades.values())}/{len(done)} | {len(runs) - len(done)} "
                f"| {viol} | {applied} | {_usage([runs[s] for s in done], passes)} |"
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
    if left is None:
        return lines
    lines += [
        f"Paired exact McNemar, {left} vs each, pooled over the tasks above:",
        "",
        "| comparison | role | pairs | left only | right only | p one-sided | p two-sided | difference, points (95% CI) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for strategy in strategies:
        if strategy != left and strategy in pooled and left in pooled:
            n, x, y, one, two, diff = _mcnemar(pooled[left], pooled[strategy])
            role = (roles or {}).get(strategy, "exploratory")
            lines.append(f"| {left} vs {strategy} | {role} | {n} | {x} | {y} | {one:.4f} | {two:.4f} | {diff} |")
    return lines + [""]


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
        f"Exploratory. Records: `records/phase1_cache_probe/probe_runs.jsonl`, a rerun on {runs[0]['date'][:10]} "
        "with raw records; the first run left only notes. A toy history of 3 turns (about 26K tokens) with "
        "two tools and one cache key per run, sent three times as it is (`default`) and three times after "
        "two growth turns (`--grow`). Each row is a request kind: R1 warm-up, R2 an ordinary follow-up, R3 "
        "the fork (the same prefix plus one appended message, JSON reply), R4 the fork with an extra output "
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


def _paired(strategy: str) -> dict[tuple[str, int], bool | None]:
    """Phases 2–5 strict pass keyed by (task, seed), from the canonical phase of each task and strategy."""
    sources = [("phase3_task1_ablation", "task1"), ("phase4_edge_cases", "rev"), ("phase4_edge_cases", "long"), ("phase4_edge_cases", "big")]
    if strategy in {"none", "B1"}:  # phase 3 did not rerun them
        sources[0] = ("phase2_task1_baselines", "task1")
    if strategy == "native":
        sources = [("phase5_native", task) for _, task in sources]
    out: dict[tuple[str, int], bool | None] = {}
    for folder, task in sources:
        out.update(((task, seed), v) for seed, v in _outcomes(_runs([folder], task, strategy), task).items())
    return out


def _pooled_2_5() -> list[str]:
    order = ["none", "B1", "B2", "B3", "native", "A1-fixed", "A1", "A1-free"]
    tasks = ["task1", "rev", "long", "big"]
    results = {strategy: _paired(strategy) for strategy in order}

    def cell(values: list) -> str:
        return f"{sum(bool(v) for v in values)}/{len(values)}" if values else "–"

    lines = [
        "## Phases 2–5 — pooled and paired",
        "",
        "Exploratory. One row per strategy over the same (task, seed) scenarios: task 1 from phase 3 (phase 2 "
        "for none and B1, which phase 3 did not rerun), the edge cases from phase 4, and every native run "
        "from phase 5. B1 and A1-fixed ran on task 1 only, so their totals cover 5 runs, not 20.",
        "",
        "| strategy | task1 | rev | long | big | rev + long | all |",
        "|---|---|---|---|---|---|---|",
    ]
    for strategy in order:
        r = results[strategy]
        cells = [cell([v for (t, _), v in r.items() if t == task]) for task in tasks]
        cells += [cell([v for (t, _), v in r.items() if t in {"rev", "long"}]), cell(list(r.values()))]
        lines.append(f"| `{strategy}` | {' | '.join(cells)} |")
    lines += [
        "",
        "Paired exact McNemar on the same (task, seed) scenarios:",
        "",
        "| left | right | pairs | left only | right only | p one-sided | p two-sided | difference, points (95% CI) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    comparisons = [("A1-free", s) for s in ("none", "B2", "B3", "native", "A1")] + [("A1", "B3"), ("A1", "native")]
    for scope, kept in (("all", None), ("rev+long", {"rev", "long"})):
        for left, right in comparisons:
            a, b = ({k: v for k, v in results[s].items() if kept is None or k[0] in kept} for s in (left, right))
            n, x, y, one, two, diff = _mcnemar(a, b)
            lines.append(f"| {left} | {right} ({scope}) | {n} | {x} | {y} | {one:.4f} | {two:.4f} | {diff} |")
    lines += ["", "Unpaired one-sided Fisher exact (ignores the pairing):", ""]
    passes = {s: [bool(v) for v in results[s].values()] for s in order}
    for left, right in [("A1-free", "none"), ("A1-free", "B2"), ("A1-free", "B3"), ("A1-free", "native")]:
        a, b = passes[left], passes[right]
        lines.append(f"- {left} vs {right}: p = {_fisher_greater(sum(a), len(a), sum(b), len(b)):.4f}")
    fork, stateless = passes["A1"] + passes["A1-free"], passes["B2"] + passes["B3"]
    p = _fisher_greater(sum(fork), len(fork), sum(stateless), len(stateless))
    lines.append(f"- fork (A1 + A1-free) {sum(fork)}/{len(fork)} vs stateless (B2 + B3) {sum(stateless)}/{len(stateless)}: p = {p:.2e}")
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
    lines = ["# Results — phases 1–10", "", "Generated by `agent_compaction/summarize.py` from `records/`; do not edit by hand.", ""]
    lines += legend.key(SETUP, STRATEGIES, TASKS, COLUMNS)
    lines += _cache_probe()
    lines += _table(
        "Phase 2 — task 1 baselines",
        "Exploratory: the first comparison. Seeds 1–5. Records: `records/phase2_task1_baselines/`.",
        ["phase2_task1_baselines"], ["task1"], ["none", "B1", "B2", "A1"],
    )
    lines += _table(
        "Phase 3 — task 1 ablation",
        "Exploratory: task 1 again, to separate the fork's ingredients, the summary schema (A1 vs A1-free) and "
        "who chooses what stays (A1 vs A1-fixed), next to the stateless summaries. Seeds 1–5. Records: "
        "`records/phase3_task1_ablation/`.",
        ["phase3_task1_ablation"], ["task1"], ["B2", "B3", "A1-fixed", "A1", "A1-free"],
    )
    lines += _table(
        "Phase 4 — edge cases",
        "Exploratory: tasks built to break the fork. Seeds 1–5. Records: `records/phase4_edge_cases/`.",
        ["phase4_edge_cases"], ["rev", "long", "big"], ["none", "B2", "B3", "A1", "A1-free"],
    )
    lines += _table(
        "Phase 5 — provider (native) compaction",
        "Exploratory. The harness attached OpenAI's compaction capability directly (`legacy_native`), before "
        "Kedi's native path took over in phase 6. Seeds 1–5. Records: `records/phase5_native/`.",
        ["phase5_native"], ["task1", "rev", "long", "big"], ["native"],
    )
    lines += _pooled_2_5()
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
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
