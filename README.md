# Agent-led compaction experiment

Can an agent compact its own conversation history better than no compaction, truncation, or an external
summarizer? This folder holds everything for that experiment: code, raw records, generated results, the
narrative report and the original plan.

- `FINDINGS.md` — current conclusions (phases 1–8) in the research brief's format; start here.
- `REPORT.md` — the full story in order: hypothesis, design, every phase, numbers, dead ends, framework
  findings, caveats. Source for the blog post.
- `results/RESULTS.md` (phases 2–5, `summarize.py`) and `results/PHASES_6_8.md` (`summarize_6_8.py`) — tables generated from `records/`. Do not edit by hand.
- `PREREGISTRATION.md` — the frozen phase-6 protocol.
- `PLAN.md` — the working plan and lab notes as they were written during the experiment (copy of
  `plans/AGENT_COMPACTION_EXPERIMENT_PLAN.md` in the Kedi workspace).
- `environment.json` — model, library versions and Kedi commits the records were produced with.
- `records/` — one JSON line per run (answer, grade, usage, every compaction event), grouped by phase.

## Code

| file | role |
|---|---|
| `normalizer.py` | deterministic layout: forced keeps, original order, block at the first dropped group |
| `test_normalizer.py` | unit tests for the normalizer |
| `compactor.py` | strategies as Kedi `> history: processor:` callables (fork A1/A1-free/A1-fixed, stateless B2/B3, truncation B1) and the `RecordingModel` wrapper |
| `cache_probe.py` | phase 1: does a compaction fork read the prefix from the provider cache? |
| `task1.py` | task 1: rules in the prompt, eight noisy logs, one incident each |
| `task2.py` | edge cases: `rev` (UPDATE/RETRACT/mid-task POLICY CHANGE), `long` (20 logs), `big` (oversized log) |
| `state.py` | values the Kedi program's Python prelude reads (processor, condition, task, tool) |
| `run.py` | runs one strategy on one task for a list of seeds and appends records |
| `summarize.py` | rebuilds `results/RESULTS.md` |

## Reproduce

From the Kedi workspace root, with its `.venv` (Kedi at the commits in `environment.json`):

```bash
.venv/bin/python -m benchmarks.agent_compaction.cache_probe --grow
.venv/bin/python -m benchmarks.agent_compaction.run --strategy A1-free --task rev --seeds 1 2 3 4 5
.venv/bin/python -m benchmarks.agent_compaction.summarize
uv run --extra snapshots --group dev python -m pytest benchmarks/agent_compaction/test_normalizer.py -o addopts="" --no-cov
```

`run.py` writes new records to `records/` (top level); move a finished batch into its phase folder before
running `summarize.py`. Strategies: `none B1 B2 B3 A1 A1-free A1-fixed native native-compact`; tasks: `t1 rev long big`;
`--threshold` (tokens, default 18000).

## Preservation

This folder is outside the Kedi repository's history (`/benchmarks` is ignored), so it is its own git
repository: commit after every batch. Records are append-only; never rewrite a published record.
