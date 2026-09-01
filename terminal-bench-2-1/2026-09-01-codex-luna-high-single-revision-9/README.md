# Kedi on Terminal-Bench 2.1: Single-Revision Nine-Task Run

This directory contains the reproducible environment, immutable manifest,
sanitized Harbor evidence, and replayable Autobench record for a nine-task
Terminal-Bench 2.1 evaluation of Kedi.

## Result

The nine valid trials scored **8/9 (88.9%)** at a provider-reported total cost
of **$0.41832972**, or **$0.04648108 per task**. The model was
`codex/gpt-5.6-luna` at high effort, with the Pydantic AI adapter, Docker, and
concurrency 2. See [RESULTS.md](RESULTS.md) for task-level metrics.

All nine Harbor trials completed without a harness exception or retry. The sole
zero-reward trial, `cancel-async-tasks`, was a task-solution failure: five of six
verifier tests passed, while cleanup was not awaited when cancellation occurred
with one task still queued.

This is a single-revision run over nine selected tasks. It is not a full-dataset
score, an official leaderboard submission, or a statistically representative
estimate of Kedi's full Terminal-Bench 2.1 performance.

## Layout

- `environment/` installs exact source revisions and recreates the nine-task run.
- `manifests/` contains the immutable manifest used by the recorded run.
- `evidence/harbor/` contains sanitized Harbor-authoritative job evidence,
  excluding four oversized duplicate terminal payloads listed by path, size,
  and SHA-256 in `evidence/sanitization-report.json`.
- `evidence/autobench/` contains a checksummed Autobench record regenerated from
  the sanitized Harbor tree.
- `evidence/index.json` defines the exact accepted trial boundary.
- `AUTOBENCH_REPORT.md` is the checked-in audit report rendered from the public
  immutable record.
- `sources.lock.json` pins Kedi, kedi-autobench, Autobench, Harbor, and grammar
  revisions.
- `scripts/prepare_publication.py` creates a privacy-preserving evidence copy
  without modifying source records.

## Reproduce A New Run

Prerequisites are Git, `uv`, Docker, and a locally authenticated Codex account.
Credentials are runtime-only inputs and must not be placed in this repository.
Set `LOGFIRE_TOKEN` in the invoking environment only when remote trace export is
desired; the run script never persists it.

```bash
terminal-bench-2-1/2026-09-01-codex-luna-high-single-revision-9/environment/setup.sh
terminal-bench-2-1/2026-09-01-codex-luna-high-single-revision-9/environment/create-manifest.sh
terminal-bench-2-1/2026-09-01-codex-luna-high-single-revision-9/environment/run-with-autobench.sh \
  terminal-bench-2-1/2026-09-01-codex-luna-high-single-revision-9/.work/manifests/single-revision-9.json \
  kedi-tb21-single-revision-9 \
  terminal-bench-2-1/2026-09-01-codex-luna-high-single-revision-9/.work/dist/kedi-0.4.0-py3-none-any.whl
```

The historical manifest preserves the original wheel digest. The wheel binary
is intentionally not published; rebuilding produces a new immutable manifest
and experiment identity.

The runner called `logfire.configure()` and enabled Pydantic AI
instrumentation. `LOGFIRE_TOKEN` was intentionally absent from this historical
run, so no traces were exported to a remote Logfire project.

## Install Autobench

The reproduction setup above installs the exact Autobench revision used for
this record into `.work/kedi-autobench/.venv`. To inspect the published record
without recreating the benchmark environment, install that revision directly:

```bash
uv tool install \
  "autobench @ git+https://github.com/vcoderun/autobench.git@3887433ecd95deb5eba60d172ec08330e456c5a6"
```

The commands below need neither model credentials nor Docker. They operate only
on the immutable evidence already stored in this directory.

## Replay And Report

Set the record path once after cloning `kedi-lang/benchmarks`:

```bash
RECORD="terminal-bench-2-1/2026-09-01-codex-luna-high-single-revision-9/evidence/autobench/codex-luna-high-full9-docker-e61ba24-c2-instrumented-r1"
```

Replay is offline and does not execute Harbor, Kedi, or the model:

```bash
autobench replay "$RECORD"
```

Render an interactive terminal report:

```bash
autobench report "$RECORD"
```

Or write a durable Markdown audit report:

```bash
autobench report "$RECORD" \
  --format markdown \
  --profile audit \
  --layout single \
  --output autobench-audit-report.md
```

Validate replay, aggregates, evidence size, secrets, and personal paths:

```bash
uv run \
  --with "autobench @ git+https://github.com/vcoderun/autobench.git@3887433ecd95deb5eba60d172ec08330e456c5a6" \
  python \
  terminal-bench-2-1/2026-09-01-codex-luna-high-single-revision-9/scripts/validate_publication.py
```

When using the environment installed by `environment/setup.sh`, replace
`autobench` and the `uv run ... python` prefix in these commands with
`terminal-bench-2-1/2026-09-01-codex-luna-high-single-revision-9/.work/kedi-autobench/.venv/bin/autobench`
and
`terminal-bench-2-1/2026-09-01-codex-luna-high-single-revision-9/.work/kedi-autobench/.venv/bin/python`,
respectively.

## Privacy And Evidence Integrity

Harbor remains authoritative for execution and grading. Publication copies are
generated before upload: known dotenv values, credential-shaped values,
secret-keyed JSON fields, private-key blocks, and personal host paths are
removed or replaced. Symlinks are not followed. Binary evidence is copied only
when it does not use a sensitive filename and is at most 20 MB. Four duplicated
terminal output payloads exceeded that publication boundary; their identities
and hashes remain in the sanitization report.

Autobench records are not edited after recording. The public record is generated
from the sanitized Harbor tree under a neutral staging path, then replayed and
scanned. It is a semantically equivalent import of public Harbor evidence, not a
byte-for-byte copy of the private local record.
