# Kedi on Terminal-Bench 2.1: Daytona Standard-Task Run

This directory preserves a single-revision Kedi evaluation over 19 selected
Terminal-Bench 2.1 standard tasks. It records Harbor-authoritative grades,
sanitized execution evidence, and an independently replayable Autobench record.

## Result

The run produced **11 successful rewards from 18 scored trials (61.1%)**. One
additional trial failed during Daytona agent installation and never received a
reward, so the raw attempted-task ratio is **11/19 (57.9%)**.

The provider reported **$4.37852572** across the 14 trials whose Kedi usage
records survived collection. Those measured trials consumed 44,370,227 input
tokens, including 26,459,136 cache-read tokens (**59.63%**), and 222,604 output
tokens. Five trials lack usage records, so this is a partial cost total and must
not be presented as the cost of the complete 19-task batch.

The host computer slept while the remote run was active. Daytona continued and
all 19 trials reached a terminal Harbor state, but the interruption affected
network-dependent setup, remote log collection, and wall-clock duration. The
task-level classifications in [RESULTS.md](RESULTS.md) distinguish clean model
outcomes from infrastructure-contaminated evidence.

This is not a full-dataset result, a five-trial estimate, or an official
leaderboard submission.

## Configuration

- Model: `codex/gpt-5.6-luna`
- Effort: `high`
- Adapter: Pydantic AI
- Environment: Daytona
- Concurrency: 2
- Trials per task: 1
- Kedi revision: `aa0dee26824da60476dd1464412045ce4e82f15b`
- Dataset: `terminal-bench/terminal-bench-2-1`, version 6

## Layout

- `environment/` installs pinned source revisions and recreates the task set.
- `manifests/` contains the immutable manifest used by the run.
- `evidence/harbor/` contains sanitized Harbor-authoritative evidence.
- `evidence/autobench/` contains a checksummed record regenerated from the
  sanitized Harbor tree under a neutral staging path.
- `evidence/index.json` declares the 18 scored trials and one unscored
  infrastructure failure.
- `AUTOBENCH_REPORT.md` is the checked-in Autobench audit report.
- `sources.lock.json` pins source revisions and distribution hashes.
- `scripts/prepare_publication.py` produces a sanitized evidence copy without
  mutating the private source records.
- `scripts/validate_publication.py` replays and audits the public bundle.

## Reproduce A New Run

Install the pinned Kedi, Kedi Autobench, and Autobench revisions:

```bash
./environment/setup.sh
```

Configure the Daytona credential and the Codex authentication expected by Kedi,
then create a fresh manifest and run it:

```bash
MANIFEST="$PWD/.work/manifests/daytona-standard-19.json"
./environment/create-manifest.sh "$MANIFEST"

KEDI_WHEEL="$(find .work/dist -name 'kedi-*.whl' -print -quit)"
./environment/run-with-autobench.sh \
  "$MANIFEST" \
  codex-luna-high-daytona-standard19-reproduction \
  "$KEDI_WHEEL"
```

The scripts never embed credentials. `KEDI_DAYTONA_API_KEY` and model
authentication must be supplied by the caller's environment.

## Install Autobench

Install the exact Autobench revision used to generate this record:

```bash
uv tool install \
  "autobench @ git+https://github.com/vcoderun/autobench.git@415c2e6100e85b5671f9f045ca6dc4e4c78f081c"
```

## Replay And Report

Set the record path after cloning `kedi-lang/benchmarks`:

```bash
RECORD="terminal-bench-2-1/2026-09-03-codex-luna-high-daytona-standard-19/evidence/autobench/codex-luna-high-daytona-2026-09-03-standard19-sdist-aa0dee2-c2-logfire"
```

Replay is offline and does not execute Harbor, Kedi, Daytona, or the model:

```bash
autobench replay "$RECORD"
```

Render an interactive terminal report:

```bash
autobench report "$RECORD"
```

Or write a Markdown audit report:

```bash
autobench report "$RECORD" \
  --format markdown \
  --profile audit \
  --layout single \
  --output autobench-audit-report.md
```

Validate replay, fixed aggregates, evidence size, secrets, and personal paths:

```bash
uv run \
  --with "autobench @ git+https://github.com/vcoderun/autobench.git@415c2e6100e85b5671f9f045ca6dc4e4c78f081c" \
  python \
  terminal-bench-2-1/2026-09-03-codex-luna-high-daytona-standard-19/scripts/validate_publication.py
```

## Evidence Boundary

Harbor is authoritative for task grading. Autobench's `passed` and `failed`
statuses describe Kedi execution lifecycle outcomes and therefore do not always
match reward success. For example, a verifier can award `1.0` after Kedi reaches
its budget boundary, while a normally completed agent can still receive `0.0`.

Publication copies replace known dotenv values, credential-shaped values,
secret-keyed JSON fields, private-key blocks, and personal host paths. Symlinks
are not followed. The public Autobench record is a semantically equivalent
import of sanitized Harbor evidence, not a byte-for-byte copy of the private
record.
