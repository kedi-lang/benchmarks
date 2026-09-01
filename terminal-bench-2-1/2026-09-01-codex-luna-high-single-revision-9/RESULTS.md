# Terminal-Bench 2.1 Nine-Task Result

Date: 2026-09-01

## Configuration

| Setting | Value |
| --- | --- |
| Dataset | `terminal-bench/terminal-bench-2-1` version `6` |
| Selected tasks | 9 |
| Model | `codex/gpt-5.6-luna` |
| Adapter | Pydantic AI |
| Effort | `high` |
| Environment | Docker |
| Concurrency | `2` |
| Kedi revision | `e61ba24224fbf96f29a502f9e27d663659025872` |
| Kedi capabilities | History, prefix cache, and tool artifacts enabled |
| Compaction | Disabled |
| Retained-process timeout | 3,600 seconds |
| Instrumentation | Local Logfire and Pydantic AI instrumentation; no remote export |

## Aggregate

| Metric | Value |
| --- | ---: |
| Official reward | 8 / 9 (88.9%) |
| Harness-completed trials | 9 / 9 |
| Harness exceptions | 0 |
| Harbor retries | 0 |
| Wall-clock runtime | 37m 3s |
| Total provider cost | $0.41832972 |
| Cost per task | $0.04648108 |
| Requests | 234 |
| Tool calls | 333 |
| Input tokens | 5,693,043 |
| Cache-read tokens | 4,369,536 |
| Uncached input tokens | 1,323,507 |
| Output tokens | 55,198 |
| Cache-read ratio | 76.75% |

## Trials

| Task | Reward | Cost | Requests | Tool calls | Input | Cache read | Trial duration |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `build-cython-ext` | 1 | $0.13215252 | 54 | 73 | 1,830,387 | 1,377,536 | 724.0s |
| `cancel-async-tasks` | 0 | $0.00723680 | 7 | 6 | 33,142 | 16,640 | 300.2s |
| `fix-git` | 1 | $0.01988704 | 14 | 31 | 149,150 | 70,912 | 295.6s |
| `large-scale-text-editing` | 1 | $0.03120232 | 24 | 38 | 254,642 | 152,576 | 592.8s |
| `log-summary-date-ranges` | 1 | $0.00814380 | 7 | 11 | 40,017 | 10,880 | 294.8s |
| `polyglot-c-py` | 1 | $0.01400128 | 10 | 14 | 54,548 | 15,104 | 309.2s |
| `pypi-server` | 1 | $0.01424772 | 17 | 24 | 98,343 | 45,696 | 343.2s |
| `qemu-startup` | 1 | $0.17704452 | 92 | 120 | 3,167,985 | 2,660,736 | 1,080.0s |
| `sqlite-db-truncate` | 1 | $0.01441372 | 9 | 16 | 64,829 | 19,456 | 308.3s |

## Findings

The retained-process lifecycle passed both server-oriented tasks:
`pypi-server` and `qemu-startup`. Tracked background processes remained alive
through verification and did not create Harbor exceptions or leaked run state.

Prefix caching materially reduced billed context rereads on the longest tasks.
`build-cython-ext` read 1,377,536 cached tokens and `qemu-startup` read 2,660,736.
Across all nine tasks, 76.75% of reported input tokens were cache reads.

The single failed task was `cancel-async-tasks`. The official verifier passed
five of six tests. The failing case started two tasks under a concurrency limit
of two, queued a third, sent SIGINT, and observed no `Cleaned up.` lines. This is
a task implementation defect in cancellation propagation and awaiting cleanup,
not a Kedi/Harbor lifecycle or infrastructure failure.

The public evidence bundle omits four duplicate terminal payload files above
20 MB. Their source paths, byte counts, and SHA-256 digests are preserved in
`evidence/sanitization-report.json`; this does not alter Harbor rewards or the
recorded usage metrics.

## Interpretation Boundary

This run validates one fixed Kedi revision on nine selected Terminal-Bench 2.1
tasks. The result is useful as a reproducible engineering checkpoint and cost
profile, but it must not be presented as a full-dataset leaderboard score.
