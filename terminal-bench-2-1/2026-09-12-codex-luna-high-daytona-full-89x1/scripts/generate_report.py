#!/usr/bin/env python3
"""Generate the human-readable result report from the immutable public record."""

from __future__ import annotations

import argparse
import json
import math
import statistics
from datetime import datetime
from pathlib import Path
from typing import Any

from autobench import replay_experiment


FAILURE_OBSERVATIONS = {
    "cancel-async-tasks": "5/6 verifier tests passed; queued-task cleanup messages were missing.",
    "chess-best-move": "The answer returned one winning move where the verifier required both.",
    "configure-git-webserver": "The verifier received HTTP 000 and found no usable deployment.",
    "count-dataset-tokens": "The command returned 63,841 tokens instead of 79,586.",
    "db-wal-recovery": "The WAL update was not recovered; 5/7 tests passed.",
    "dna-assembly": "The required BsaI site was absent from the produced primers.",
    "extract-elf": "The output format passed, but none of the expected values matched.",
    "gcode-to-text": "The reconstructed phrase did not match the target flag.",
    "install-windows-3.11": "Keyboard input produced no qualifying visual change; 3/4 tests passed.",
    "make-doom-for-mips": "The expected graphics initialization output was absent; 2/3 tests passed.",
    "model-extraction-relu-logits": "Nine rows of the extracted matrix did not match.",
    "mteb-retrieve": "The package check passed, but the retrieved document was incorrect.",
    "protein-assembly": "The required donor sequence was absent from the assembled gBlock.",
    "query-optimize": "Correctness passed, but runtime exceeded the limit by about 27 ms.",
    "raman-fitting": "The fitted peak centers were far from the required values.",
    "regex-chess": "Three valid-position game tests were missing legal moves.",
    "train-fasttext": "Accuracy was 0.618 against the required 0.620.",
    "video-processing": "Both reported event frames were five frames outside accepted ranges.",
    "winning-avg-corewars": "The warrior scored 7% against snake.red; 33% was required.",
    "filter-js-from-html": "Unsafe cases survived and five benign files were modified.",
    "torch-pipeline-parallelism": "Backward gradients mismatched for rank 1, microbatch 0; 2/3 tests passed.",
}


def metric(run: Any, name: str) -> Any:
    for observation in run.task_result.observations:
        if observation.name == name:
            return observation.value
    return None


def percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    position = (len(ordered) - 1) * fraction
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (position - lower)


def wilson(successes: int, total: int) -> tuple[float, float]:
    z = 1.959963984540054
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return center - margin, center + margin


def fmt_int(value: int | float | None) -> str:
    return "-" if value is None else f"{int(value):,}"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    options = parser.parse_args()
    root = options.root.expanduser().resolve()
    index = json.loads((root / "evidence" / "index.json").read_text(encoding="utf-8"))
    entries = {entry["trial_id"]: entry for entry in index["trials"]}
    experiment = replay_experiment(root / "evidence" / "autobench" / "full89")
    rows = []
    for run in experiment.runs:
        output = run.task_result.output
        trial_id = output["trial_name"]
        entry = entries[trial_id]
        input_tokens = int(metric(run, "kedi.input_tokens") or 0)
        cache_tokens = int(metric(run, "kedi.cache_read_tokens") or 0)
        rows.append(
            {
                "task": entry["task_name"],
                "trial": trial_id,
                "batch": entry["batch"],
                "reward": float(metric(run, "terminal_bench.reward.reward") or 0),
                "duration": float(metric(run, "terminal_bench.duration") or 0),
                "cost": float(metric(run, "kedi.cost_usd") or 0),
                "input": input_tokens,
                "cache": cache_tokens,
                "cache_rate": cache_tokens / input_tokens if input_tokens else 0,
                "output": int(metric(run, "kedi.output_tokens") or 0),
                "requests": int(metric(run, "kedi.requests") or 0),
                "tools": int(metric(run, "kedi.tool_calls") or 0),
            }
        )
    rows.sort(key=lambda row: row["task"])
    solved = sum(row["reward"] == 1 for row in rows)
    total_cost = sum(row["cost"] for row in rows)
    input_tokens = sum(row["input"] for row in rows)
    cache_tokens = sum(row["cache"] for row in rows)
    output_tokens = sum(row["output"] for row in rows)
    durations = [row["duration"] for row in rows]
    costs = [row["cost"] for row in rows]
    starts = [datetime.fromisoformat(entry["started_at"].replace("Z", "+00:00")) for entry in index["trials"]]
    finishes = [datetime.fromisoformat(entry["finished_at"].replace("Z", "+00:00")) for entry in index["trials"]]
    wall_seconds = (max(finishes) - min(starts)).total_seconds()
    ci_low, ci_high = wilson(solved, len(rows))
    standard = [row for row in rows if row["batch"] == "standard81-c2"]
    high = [row for row in rows if row["batch"] == "high-memory8-c1"]

    lines = [
        "# Results",
        "",
        "## Summary",
        "",
        "This immutable run covers all 89 Terminal-Bench 2.1 tasks exactly once. Harbor's official verifier awarded reward 1 to "
        f"**{solved}/89 tasks ({solved / 89:.2%})**. The Wilson 95% interval for this single-trial pass proportion is "
        f"**{ci_low:.2%}-{ci_high:.2%}**; it describes sampling uncertainty, not five-trial leaderboard accuracy.",
        "",
        "| Metric | Result |",
        "| --- | ---: |",
        f"| Official reward | {solved}/89 ({solved / 89:.2%}) |",
        f"| Provider-reported total cost | ${total_cost:.8f} |",
        f"| Cost per attempted task | ${total_cost / 89:.8f} ({total_cost / 89 * 100:.3f} cents) |",
        f"| Cost per solved task | ${total_cost / solved:.8f} ({total_cost / solved * 100:.3f} cents) |",
        f"| Input tokens | {input_tokens:,} |",
        f"| Cache-read input tokens | {cache_tokens:,} ({cache_tokens / input_tokens:.2%}) |",
        f"| Uncached input tokens | {input_tokens - cache_tokens:,} |",
        f"| Output tokens | {output_tokens:,} |",
        f"| Model requests | {sum(row['requests'] for row in rows):,} |",
        f"| Tool calls | {sum(row['tools'] for row in rows):,} |",
        f"| Observed wall span | {wall_seconds / 3600:.2f} hours |",
        f"| Sum of per-task durations | {sum(durations) / 3600:.2f} hours |",
        "",
        "## Configuration",
        "",
        "- Model: `codex/gpt-5.6-luna`, high effort.",
        "- Adapter: Kedi Pydantic adapter; CodeMode disabled; artifacts and history enabled; compaction disabled.",
        "- Transport: WebSocket first with HTTP fallback; Logfire disabled.",
        "- Execution: 81 standard tasks at concurrency 2, followed by 8 high-memory tasks at concurrency 1.",
        "- Timeout: six hours per agent; one attempt per task and no automatic trial retries.",
        "- Environment: Daytona sandboxes; Harbor 0.22.0; Kedi 0.4.0; codex-auth-helper 1.8.0.",
        "- Dataset: Terminal-Bench 2.1, with the `evalstate` infrastructure-only QEMU fixes for `qemu-alpine-ssh` and `qemu-startup`.",
        "",
        "## Distribution",
        "",
        "| Metric | Median | Mean | P90 | P95 | Maximum |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
        f"| Cost (USD) | ${statistics.median(costs):.5f} | ${statistics.mean(costs):.5f} | ${percentile(costs, .90):.5f} | ${percentile(costs, .95):.5f} | ${max(costs):.5f} |",
        f"| Duration (s) | {statistics.median(durations):.1f} | {statistics.mean(durations):.1f} | {percentile(durations, .90):.1f} | {percentile(durations, .95):.1f} | {max(durations):.1f} |",
        f"| Input tokens | {fmt_int(statistics.median(row['input'] for row in rows))} | {fmt_int(statistics.mean(row['input'] for row in rows))} | {fmt_int(percentile([row['input'] for row in rows], .90))} | {fmt_int(percentile([row['input'] for row in rows], .95))} | {fmt_int(max(row['input'] for row in rows))} |",
        f"| Output tokens | {fmt_int(statistics.median(row['output'] for row in rows))} | {fmt_int(statistics.mean(row['output'] for row in rows))} | {fmt_int(percentile([row['output'] for row in rows], .90))} | {fmt_int(percentile([row['output'] for row in rows], .95))} | {fmt_int(max(row['output'] for row in rows))} |",
        f"| Model requests | {fmt_int(statistics.median(row['requests'] for row in rows))} | {statistics.mean(row['requests'] for row in rows):.1f} | {percentile([row['requests'] for row in rows], .90):.1f} | {percentile([row['requests'] for row in rows], .95):.1f} | {max(row['requests'] for row in rows)} |",
        f"| Tool calls | {fmt_int(statistics.median(row['tools'] for row in rows))} | {statistics.mean(row['tools'] for row in rows):.1f} | {percentile([row['tools'] for row in rows], .90):.1f} | {percentile([row['tools'] for row in rows], .95):.1f} | {max(row['tools'] for row in rows)} |",
        "",
        "## Batch Breakdown",
        "",
        "| Batch | Tasks | Solved | Score | Cost | Cache-read ratio |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for label, subset in (("Standard C2", standard), ("High-memory C1", high)):
        subset_input = sum(row["input"] for row in subset)
        subset_cache = sum(row["cache"] for row in subset)
        subset_solved = sum(row["reward"] == 1 for row in subset)
        lines.append(
            f"| {label} | {len(subset)} | {subset_solved} | {subset_solved / len(subset):.2%} | "
            f"${sum(row['cost'] for row in subset):.8f} | {subset_cache / subset_input:.2%} |"
        )

    lines.extend(
        [
            "",
            "## Reward-Zero Tasks",
            "",
            "All 21 tasks below reached Harbor grading and received reward 0. None ended with a Harbor exception. The observation column is post-run diagnosis and does not alter the official score.",
            "",
            "| Task | Observed verifier failure | Cost | Duration |",
            "| --- | --- | ---: | ---: |",
        ]
    )
    for row in (row for row in rows if row["reward"] == 0):
        job = index["batches"][row["batch"]]
        link = f"evidence/harbor/{job}/{row['trial']}/result.json"
        lines.append(
            f"| [{row['task']}]({link}) | {FAILURE_OBSERVATIONS[row['task']]} | "
            f"${row['cost']:.5f} | {row['duration']:.1f}s |"
        )

    lines.extend(
        [
            "",
            "## Per-Task Results",
            "",
            "| Task | Reward | Batch | Duration | Cost | Input | Cache read | Cache ratio | Output | Requests | Tools |",
            "| --- | ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for row in rows:
        job = index["batches"][row["batch"]]
        link = f"evidence/harbor/{job}/{row['trial']}/result.json"
        lines.append(
            f"| [{row['task']}]({link}) | {row['reward']:.0f} | {row['batch']} | {row['duration']:.1f}s | "
            f"${row['cost']:.5f} | {row['input']:,} | {row['cache']:,} | {row['cache_rate']:.1%} | "
            f"{row['output']:,} | {row['requests']} | {row['tools']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation And Limits",
            "",
            "The aggregate is a complete one-trial measurement of this frozen harness configuration, not a stable estimate of model accuracy. Task outcomes are stochastic; the intended production-style Terminal-Bench aggregate uses five trials per task. Cost is provider-reported and includes cached input pricing as returned by the runtime.",
            "",
            "The 21 failures cost $1.70943164 in total, or $0.08140 per failed task, compared with $0.04748 per solved task. Expensive failures therefore materially raise the overall mean even though the median task cost is only $0.02364. This run records 119.97M cumulative input tokens, but 94.48% were cache reads; uncached input was 6.62M tokens.",
            "",
            "The two QEMU tasks use an unreleased infrastructure repair from `evalstate/terminal-bench-2-1` commit `75f5a2e66b2dfd9d7eba3065a9d919c1f9da5c5e`. Their rewards are retained as engineering evidence, but this makes the aggregate ineligible for direct official leaderboard submission. No comparison in this repository should treat this single run as causal evidence for Kedi-specific improvements.",
            "",
            "The historical Kedi wheel was built from a dirty but fully hashed source tree. Its wheel SHA256 and per-source hashes are preserved in `manifests/experiment-contract.json` and `manifests/expected-sources.json`; the wheel and credentials are intentionally not published. Consequently the record is replayable and auditable, while byte-identical subject re-execution requires the privately retained wheel.",
            "",
        ]
    )
    (root / "RESULTS.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
