# Terminal-Bench 2.1 Dogfood Result

Date: 2026-08-31

## Configuration

| Setting | Value |
| --- | --- |
| Dataset | `terminal-bench/terminal-bench-2-1` version `6` |
| Model | `codex/gpt-5.6-luna` |
| Adapter | Pydantic AI |
| Effort | `high` |
| Environment | Docker |
| Concurrency | `2` |
| Kedi capabilities | History, prefix cache, and tool artifacts enabled |
| Telemetry | Logfire and Pydantic AI instrumentation enabled |

## Aggregate

| Metric | Value |
| --- | ---: |
| Official reward | 6 / 9 (66.7%) |
| Harness-completed accepted trials | 9 / 9 |
| Harness exceptions in accepted trials | 0 |
| Total provider cost | $0.32662052 |
| Cost per task | $0.03629117 |
| Requests | 193 |
| Tool calls | 335 |
| Input tokens | 3,731,773 |
| Cache-read tokens | 2,681,216 |
| Uncached input tokens | 1,050,557 |
| Output tokens | 52,404 |
| Cache-read ratio | 71.85% |

## Accepted Trials

| Task | Reward | Cost | Requests | Tool calls | Input | Cache read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `build-cython-ext` | 1 | $0.11584596 | 55 | 91 | 1,773,531 | 1,405,568 |
| `cancel-async-tasks` | 0 | $0.00942680 | 9 | 8 | 41,734 | 14,720 |
| `fix-git` | 1 | $0.03451856 | 18 | 55 | 273,754 | 139,008 |
| `large-scale-text-editing` | 1 | $0.04425216 | 33 | 58 | 454,074 | 323,968 |
| `log-summary-date-ranges` | 1 | $0.00741828 | 7 | 8 | 51,189 | 27,264 |
| `polyglot-c-py` | 1 | $0.01109540 | 8 | 13 | 42,661 | 15,360 |
| `pypi-server` | 0 | $0.01381168 | 14 | 27 | 83,018 | 38,144 |
| `qemu-startup` | 0 | $0.07987672 | 40 | 64 | 965,162 | 695,296 |
| `sqlite-db-truncate` | 1 | $0.01037496 | 9 | 11 | 46,650 | 21,888 |

## Harness Findings

The dogfood sequence exposed and validated fixes for four execution boundaries:

1. Old task images now bootstrap a managed Python 3.11 environment with seeded
   packaging tools.
2. Terminal failures become retryable tool errors instead of terminating the
   agent run.
3. Pydantic AI and Kedi host request budgets use one aligned request limit.
4. Kedi's cumulative host budget counts uncached input rather than charging
   cache reads as new input.

The final `build-cython-ext` trial directly exercised the cache-aware budget
fix. It completed with 1,773,531 input tokens, including 1,405,568 cache-read
tokens and 367,963 uncached tokens, and received an official reward of 1.0.

## Interpretation Boundary

The aggregate is useful harness dogfood evidence, but it is not a controlled
single-revision benchmark. Kedi revisions `e82d540`, `c7c3fc9`, and `69ad944`
contributed accepted trials. A leaderboard-quality result must rerun all nine
tasks from one immutable Kedi revision without selective continuation.
