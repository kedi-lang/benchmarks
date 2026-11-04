# Agent-led compaction experiment

Can an agent compact its own conversation history better than no compaction, truncation, an external
summarizer or the provider's own compaction? This folder holds everything for that experiment: code, raw
records, generated results, the narrative report, the pre-registrations and the original plan.

- `FINDINGS.md` — current conclusions (phases 1–10) in the research brief's format; start here.
- `REPORT.md` — phases 1–5 told in order: hypothesis, design, every phase, numbers, dead ends, framework
  findings, caveats. Source for the blog post.
- `results/RESULTS.md` (phases 2–5, `summarize.py`) and `results/PHASES_6_8.md` (phases 6–10 despite the
  name, `summarize_6_8.py`) — tables generated from `records/`. Do not edit by hand.
- `PREREGISTRATION.md` (phase 6), `PREREGISTRATION_PHASE9.md`, `PREREGISTRATION_PHASE10.md` — the frozen
  protocols, each committed before its runs.
- `PLAN.md` — the working plan and lab notes as they were written during the experiment (copy of
  `plans/AGENT_COMPACTION_EXPERIMENT_PLAN.md` in the Kedi workspace).
- `environment.json` — models, library versions, and the Kedi and harness commits each phase ran with.
- `records/` — one JSON line per run attempt (answer, grade, usage, every compaction event, probe), grouped
  by phase. `records/pilot_deepseek/README.md` describes the phase 10 pilot.

## Code

| file | role |
|---|---|
| `normalizer.py` | deterministic layout: forced keeps, original order, block at the first dropped group |
| `test_normalizer.py` | unit tests for the normalizer |
| `compactor.py` | strategies as Kedi `> history: processor:` callables (fork A1/A1-free/A1-fixed, stateless B2/B3, truncation B1, resets) and the `RecordingModel` wrapper |
| `codex_model.py` | the Codex model builder and base instruction every run used (verbatim copy, see `environment.json`) |
| `loop_guard.py` | keeps a `codex_auth_helper` model usable across Kedi invocations on different event loops |
| `cache_probe.py` | phase 1: does a compaction fork read the prefix from the provider cache? |
| `task1.py` | task 1: rules in the prompt, eight noisy logs, one incident each |
| `task2.py` | edge cases: `rev` (UPDATE/RETRACT/mid-task POLICY CHANGE), `long` (20 logs), `big` (oversized log) |
| `task3.py` | held-out tasks: one instruction change (`override`, `format`, `scope`, their `-early` controls) and `override-inject` (phase 9 H6) |
| `state.py` | values the Kedi program's Python prelude reads (processor, condition, task, tool) |
| `run.py` | runs one strategy on one task for a list of seeds and appends records |
| `summarize.py`, `summarize_6_8.py` | rebuild `results/RESULTS.md` and `results/PHASES_6_8.md` |

## Reproduce

**Setup.** Clone Kedi (`kedi-lang/kedi`) and check out the commit `environment.json` lists for the phase.
Put this folder at `benchmarks/agent_compaction` inside the checkout: the code imports itself as
`benchmarks.agent_compaction`. From the checkout root, install with `uv sync --group dev` (Python 3.12;
the lock pins the versions in `environment.json`). For an exact rerun, also check out this repository at
the phase's harness commit from `environment.json`. Harness commits older than the one that added
`codex_model.py` import that code from `benchmarks.subagent_comparison.common`, which is not part of this
repository; cherry-pick that commit onto them.

**Model access.**
- `gpt-6-luna`, `gpt-6.1-terra` and native compaction use OpenAI Responses through `codex-auth-helper`,
  which reads the Codex CLI login in `~/.codex/auth.json` (a Codex subscription).
- `openrouter:<model>` reads its key from `OPENROUTER_API_KEY`.
- Hosted models and the Codex backend can change without notice, so a rerun measures the models as they are
  on that day. Native compaction runs on the provider's servers.
- Cost: the Codex-backed phases ran on the subscription's usage quota. Phase 10 cost about $3.4 of
  OpenRouter credit, its pilot about $0.2.

**Run.** One command per strategy and task. Seeds run in order, and each appends one JSON line to
`records/<task>_t18k_<strategy>.jsonl` (`task1_…` for `t1`). Move a finished batch into its phase folder,
then regenerate the tables:

```bash
.venv/bin/python -m benchmarks.agent_compaction.run --strategy A1-free --task long --seeds 201 202 203
.venv/bin/python -m benchmarks.agent_compaction.summarize_6_8   # phases 6–10
.venv/bin/python -m benchmarks.agent_compaction.summarize       # phases 2–5
uv run --extra snapshots --group dev python -m pytest benchmarks/agent_compaction/test_normalizer.py -o addopts="" --no-cov
```

Defaults: `--model gpt-6-luna --effort medium --threshold 18000`. What each phase ran:

| phase | tasks (`--task`) | strategies (`--strategy`) | model | seeds |
|---|---|---|---|---|
| 1 | `cache_probe`, with and without `--grow` | – | luna | – |
| 2 | `t1` | `A1 B1 B2 none` | luna | 1–5 |
| 3 | `t1` | `A1 A1-fixed A1-free B2 B3` | luna | 1–5 |
| 4 | `rev long big` | `A1 A1-free B2 B3 none` | luna | 1–5 |
| 5 | `t1 rev long big` | `native`, attached directly: `run_one(..., legacy_native=True)` (no CLI flag) | luna | 1–5 |
| 6 | `override format scope`, each also `-early` | `A1-free native B3 none` | luna | 101–115 |
| 6b | `scope` | `A1-free native B3 none` | luna | 101–115 |
| 7 | `rev long` | `A1-free native native+reassert none reset-det reset-fork` | luna | 1–5 |
| 8 | `rev long` | `A1-free native native+reassert none reset-det` | luna | 6–15 |
| 9 H4 | `long` | `A1-free native native+reassert` | luna | 201–215 |
| 9 H5 | `override format` | `A1-free native` | `--model gpt-6.1-terra --effort low` | 101–115 |
| 9 H6 | `override-inject` | `A1-free native none` | luna | 101–115 |
| 10 | `long` | `A1-free B3 none` | `--model openrouter:deepseek/deepseek-v4.1-flash` | 401–415 |

Infrastructure failures got one rerun with the same seed. `summarize_6_8.py` counts these as
infrastructure: rate limit, timeout, usage limit, connection error and HTTP 503. Its summary counts the last
attempt per seed and reports failures that remain after the rerun as missing. Request-limit and budget
failures count against the strategy.

## Preservation

This folder is outside the Kedi repository's history (`/benchmarks` is ignored), so it is its own git
repository: commit after every batch. Records are append-only; never rewrite a published record.
