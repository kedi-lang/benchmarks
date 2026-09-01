# Kedi on Terminal-Bench 2.1: Lifecycle Validation Rerun

This directory contains the reproducible environment, immutable manifest,
sanitized Harbor evidence, and replayable Autobench record for a targeted
three-task validation of Kedi's retained-process lifecycle.

## Result

The three valid trials scored **2/3 (66.7%)** at a provider-reported total cost
of **$0.18051228**, or **$0.06017076 per task**. The model was
`codex/gpt-5.6-luna` at high effort, with Docker and concurrency 2. See
[RESULTS.md](RESULTS.md) for task-level metrics.

This is a single-revision validation run, but it is not an official leaderboard
submission or a representative full-dataset score. It reruns the three tasks
that failed in the earlier pilot. `pypi-server` and `qemu-startup` now pass with
their background processes retained through verification. `cancel-async-tasks`
completed without a harness exception but failed its task verifier.

## Layout

- `environment/` installs exact source revisions and recreates the three-task run.
- `manifests/` contains the immutable manifest used by the recorded run.
- `evidence/harbor/` contains sanitized Harbor-authoritative job evidence.
- `evidence/autobench/` contains a checksummed Autobench record regenerated from
  the sanitized Harbor tree.
- `evidence/index.json` defines the exact accepted trial boundary.
- `sources.lock.json` pins Kedi, kedi-autobench, Autobench, Harbor, and grammar
  revisions.
- `scripts/prepare_publication.py` creates a privacy-preserving evidence copy
  without modifying source records.

## Reproduce A New Run

Prerequisites are Git, `uv`, Docker, and a locally authenticated Codex account.
Credentials are runtime-only inputs and must not be placed in this repository.

```bash
terminal-bench-2-1/2026-09-01-codex-luna-high-lifecycle-rerun-3/environment/setup.sh
terminal-bench-2-1/2026-09-01-codex-luna-high-lifecycle-rerun-3/environment/create-manifest.sh
terminal-bench-2-1/2026-09-01-codex-luna-high-lifecycle-rerun-3/environment/run-with-autobench.sh \
  terminal-bench-2-1/2026-09-01-codex-luna-high-lifecycle-rerun-3/.work/manifests/lifecycle-rerun-3.json \
  kedi-tb21-lifecycle-rerun-3 \
  terminal-bench-2-1/2026-09-01-codex-luna-high-lifecycle-rerun-3/.work/dist/kedi-0.4.0-py3-none-any.whl
```

The historical manifest preserves the original wheel digest. The wheel binary
is intentionally not published; rebuilding produces a new immutable manifest
and experiment identity.

## Replay And Validate

Replay is offline and does not execute Harbor, Kedi, or the model:

```bash
terminal-bench-2-1/2026-09-01-codex-luna-high-lifecycle-rerun-3/.work/kedi-autobench/.venv/bin/autobench replay \
  terminal-bench-2-1/2026-09-01-codex-luna-high-lifecycle-rerun-3/evidence/autobench/codex-luna-high-failed3-docker-e61ba24-c2-logfire
```

Validate replay, aggregates, evidence size, secrets, and personal paths:

```bash
terminal-bench-2-1/2026-09-01-codex-luna-high-lifecycle-rerun-3/.work/kedi-autobench/.venv/bin/python \
  terminal-bench-2-1/2026-09-01-codex-luna-high-lifecycle-rerun-3/scripts/validate_publication.py
```

## Privacy And Evidence Integrity

Harbor remains authoritative for execution and grading. Publication copies are
generated before upload: known dotenv values, credential-shaped values,
secret-keyed JSON fields, private-key blocks, and personal host paths are
removed or replaced. Symlinks are not followed. Binary evidence is copied only
when it does not use a sensitive filename.

Autobench records are not edited after recording. The public record is generated
from the sanitized Harbor tree under a neutral staging path, then replayed and
scanned. It is a semantically equivalent import of public Harbor evidence, not
a byte-for-byte copy of the private local record.
