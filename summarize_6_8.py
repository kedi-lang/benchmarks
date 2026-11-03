"""Regenerate results/PHASES_6_8.md (held-out test, scope supplement, reset/reassert, more seeds).

    .venv/bin/python -m benchmarks.agent_compaction.summarize_6_8

The last attempt per (task, strategy, seed) counts; infrastructure failures (rate limit, timeout) that
remain after the single allowed rerun are reported as missing, not as strategy failures.
"""

from __future__ import annotations

import json
import statistics
from math import comb
from pathlib import Path

from . import task2, task3

ROOT = Path(__file__).parent
RECORDS = ROOT / "records"
OUT = ROOT / "results" / "PHASES_6_8.md"
# A 503 (server unavailable) is infrastructure like a connection error: the request was not served.
INFRA = ("RateLimit", "Timeout", "usage_limit_reached", "ModelConnectionError", "status_code: 503")


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


def _table(title: str, folders: list[str], tasks: list[str], strategies: list[str], left: str) -> list[str]:
    lines = [f"## {title}", "", "| task | strategy | pass | missing (infra) | policy viol. | change applied | median total input | median output | calls (median) |", "|---|---|---|---|---|---|---|---|---|"]
    pooled: dict[str, dict] = {}
    for task in tasks:
        for strategy in strategies:
            runs = _runs(folders, task, strategy)
            if not runs:
                continue
            outcomes = _outcomes(runs, task)
            pooled.setdefault(strategy, {}).update({(task, k): v for k, v in outcomes.items()})
            done = [v for v in outcomes.values() if v is not None]
            grades = [_grade(task, s, r["answer"]) for s, r in runs.items() if r["answer"]]
            viol = sum(g.get("policy_violations", 0) for g in grades)
            applied = sum(1 for g in grades if g.get("change_applied")) if task in task3.VARIANTS else "–"
            total_in = statistics.median(r["usage"]["input"] + (r["usage"].get("compaction_input") or 0) for r in runs.values())
            total_out = statistics.median(
                r["usage"]["output"] + sum((e.get("output") or 0) for e in r["compactions"]) for r in runs.values()
            )
            calls = statistics.median(
                r["usage"]["requests"]
                + sum(1 for e in r["compactions"] if e.get("strategy") in {"A1", "A1-free", "A1-fixed", "B2", "B3"})
                for r in runs.values()
            )
            lines.append(
                f"| {task} | {strategy} | {sum(done)}/{len(done)} | {len(outcomes) - len(done)} | {viol} | {applied} "
                f"| {int(total_in) // 1000}K | {int(total_out)} | {calls:g} |"
            )
    lines += ["", f"Paired exact McNemar, {left} vs each (pooled over the tasks above; pairs with an infra-missing side dropped):", "", "| comparison | pairs | left only | right only | p one-sided | p two-sided |", "|---|---|---|---|---|---|"]
    for strategy in strategies:
        if strategy != left and strategy in pooled and left in pooled:
            n, x, y, one, two = _mcnemar(pooled[left], pooled[strategy])
            lines.append(f"| {left} vs {strategy} | {n} | {x} | {y} | {one:.4f} | {two:.4f} |")
    return lines + [""]


def _probe(folders: list[str], tasks: list[str]) -> list[str]:
    lines = ["Rule-recall probe on failed runs (asked after the final report):", ""]
    for strategy in ("native", "A1-free", "B3", "none"):
        failed = recalled = 0
        for task in tasks:
            for seed, record in _runs(folders, task, strategy).items():
                if record["answer"] and not _grade(task, seed, record["answer"])["strict"] and record.get("probe"):
                    failed += 1
                    recalled += bool(record["probe"]["recalls_change"])
        lines.append(f"- {strategy}: {recalled}/{failed} failed runs named the changed instruction")
    return lines + [""]


def main() -> None:
    heldout = ["override", "format", "scope"]
    early = ["override-early", "format-early", "scope-early"]
    s6 = ["A1-free", "native", "B3", "none"]
    s7 = ["A1-free", "native", "native+reassert", "reset-det", "reset-fork", "none"]
    lines = ["# Phases 6–8 — results", "", "Generated by `summarize_6_8.py`; do not edit by hand. Strict pass unless noted.", ""]
    lines += _table("Phase 6 — pre-registered held-out, instruction change after the first compaction (k=5)", ["phase6_heldout"], heldout, s6, "A1-free")
    lines += _probe(["phase6_heldout"], heldout)
    lines += _table("Phase 6 — control, instruction change before the first compaction (k=2)", ["phase6_heldout"], early, s6, "A1-free")
    lines += _table("Phase 6b — scope k=5 supplement (outside the pre-registration)", ["phase6b_scope_supplement"], ["scope"], s6, "A1-free")
    lines += _probe(["phase6b_scope_supplement"], ["scope"])
    lines += _table("Phases 7 + 8 — reset / reassert, rev and long (seeds 1–15; rev seed 8 not generatable)", ["phase7_reset_reassert", "phase8_more_seeds"], ["rev", "long"], s7, "A1-free")
    lines += _table("Phases 7 + 8 — long only", ["phase7_reset_reassert", "phase8_more_seeds"], ["long"], s7, "A1-free")
    lines += _table("Phase 9 H4 — long, seeds 201–215 (pre-registered; gpt-6-luna medium)", ["phase9_prereg"], ["long"], ["A1-free", "native", "native+reassert"], "A1-free")
    lines += _table("Phase 9 H5 — second model gpt-6.1-terra, effort low (pre-registered)", ["phase9_prereg"], ["override", "format"], ["A1-free", "native"], "A1-free")
    lines += _table("Phase 9 H6 — untrusted fake instruction in tool output (pre-registered)", ["phase9_prereg"], ["override-inject"], ["A1-free", "native", "none"], "A1-free")
    lines += _table("Phase 10 H7 — long, deepseek-v4.1-flash via OpenRouter, seeds 401–415 (pre-registered; primary A1-free vs B3)", ["phase10_prereg"], ["long"], ["A1-free", "B3", "none"], "A1-free")
    OUT.write_text("\n".join(lines) + "\n")
    print(OUT)


if __name__ == "__main__":
    main()
