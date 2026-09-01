# Terminal-Bench 2.1 Lifecycle Validation Result

Date: 2026-09-01

## Configuration

| Setting | Value |
| --- | --- |
| Dataset | `terminal-bench/terminal-bench-2-1` version `6` |
| Model | `codex/gpt-5.6-luna` |
| Adapter | Pydantic AI |
| Effort | `high` |
| Environment | Docker |
| Concurrency | `2` |
| Kedi revision | `e61ba24224fbf96f29a502f9e27d663659025872` |
| Kedi capabilities | History, prefix cache, and tool artifacts enabled |
| Compaction | Disabled |
| Retained-process timeout | 3,600 seconds |
| Telemetry | Logfire and Pydantic AI instrumentation enabled |

## Aggregate

| Metric | Value |
| --- | ---: |
| Official reward | 2 / 3 (66.7%) |
| Harness-completed trials | 3 / 3 |
| Harness exceptions | 0 |
| Total provider cost | $0.18051228 |
| Cost per task | $0.06017076 |
| Requests | 100 |
| Tool calls | 165 |
| Input tokens | 2,617,971 |
| Cache-read tokens | 2,041,984 |
| Uncached input tokens | 575,987 |
| Output tokens | 20,396 |
| Cache-read ratio | 78.00% |

## Trials

| Task | Reward | Cost | Requests | Tool calls | Input | Cache read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `pypi-server` | 1 | $0.02038196 | 16 | 37 | 128,533 | 58,368 |
| `qemu-startup` | 1 | $0.15057756 | 75 | 119 | 2,447,001 | 1,966,848 |
| `cancel-async-tasks` | 0 | $0.00955276 | 9 | 9 | 42,437 | 16,768 |

## Lifecycle Finding

The two server tasks validate the general retained-process behavior introduced
after the pilot. Each task handed one tracked background process to the runtime,
the process remained alive through agent completion, and cleanup occurred only
after Harbor verification. Both tasks received reward 1.0.

`cancel-async-tasks` completed its Kedi and Harbor lifecycle normally and had no
harness exception. Its reward 0.0 is therefore a task-solution failure rather
than an infrastructure failure.

## Interpretation Boundary

This run answers a narrow regression question: whether the three previously
failed tasks execute correctly on one fixed Kedi revision after retained-process
lifecycle support. It is not a full Terminal-Bench 2.1 score and should not be
compared directly with full-dataset leaderboard results.
