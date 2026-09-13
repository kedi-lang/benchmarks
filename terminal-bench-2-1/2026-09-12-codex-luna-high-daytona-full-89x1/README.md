# Kedi on Terminal-Bench 2.1: Full 89-Task Single-Trial Run

This directory publishes one complete 89-task Terminal-Bench 2.1 run as a single immutable experiment. Every task was attempted exactly once with Codex Luna at high effort through Kedi's Pydantic adapter.

## Result

Harbor awarded reward 1 to **68/89 tasks (76.40%)**. Provider-reported cost was **$4.93781512 total**, **$0.05548107 per attempted task**, and **$0.07261493 per solved task**. The run consumed 119,974,598 cumulative input tokens, of which 113,355,776 were cache reads (**94.48%**), plus 1,122,446 output tokens.

See [RESULTS.md](RESULTS.md) for distributions, the standard/high-memory breakdown, all 21 reward-zero diagnoses, and all 89 task-level rows.

This is a full-dataset one-trial engineering result, not a five-trial estimate or an official leaderboard submission. The two QEMU tasks use an unreleased infrastructure-only fix and make the aggregate ineligible for direct official leaderboard comparison.

## Layout

- `evidence/autobench/full89/` is the single replayable Autobench experiment record with 89 runs.
- `evidence/harbor/` contains the sanitized Harbor-authoritative trial evidence referenced by the record.
- `evidence/index.json` defines the exact trial and batch boundary.
- `evidence/sanitization-report.json` records redactions and intentionally omitted oversized files.
- `manifests/` preserves the frozen experiment contract, task configs, package hashes, source hashes, and revisions.
- `scripts/` contains deterministic publication, record construction, report generation, checksum, and validation tools.
- `environment/setup-replay.sh` creates an isolated replay/validation environment; after its one-time dependency installation, record replay itself is offline.
- `checksums.sha256` covers every published file except itself.

## Replay And Validate

Install the pinned replay toolchain after cloning the repository:

```bash
terminal-bench-2-1/2026-09-12-codex-luna-high-daytona-full-89x1/environment/setup-replay.sh
```

Replay and render the record without executing Harbor, Kedi, or the model:

```bash
ROOT="terminal-bench-2-1/2026-09-12-codex-luna-high-daytona-full-89x1"
"$ROOT/.venv-replay/bin/autobench" replay "$ROOT/evidence/autobench/full89"
"$ROOT/.venv-replay/bin/autobench" report "$ROOT/evidence/autobench/full89"
```

Validate the 89-run boundary, exact aggregates, checksums, evidence limits, secrets, and personal paths:

```bash
ROOT="terminal-bench-2-1/2026-09-12-codex-luna-high-daytona-full-89x1"
"$ROOT/.venv-replay/bin/python" "$ROOT/scripts/validate_publication.py" "$ROOT"
```

## Evidence Integrity And Privacy

The private source record remains immutable. The publication tree was generated from it with structured JSON redaction, known-secret replacement, credential-pattern scanning, personal/remote-private path replacement, symlink rejection, and a 20 MB per-file publication limit.

Two identical 71,892,511-byte QEMU terminal payloads exceeded that limit and are omitted. Their source SHA256 values remain in `evidence/sanitization-report.json`; the remaining QEMU result, verifier, command, and model evidence is present. No credential file, known dotenv secret, bearer token, API key, private key, personal host path, or private runtime path is published.

The historical Kedi wheel was built from a dirty source tree. The wheel itself and all credentials are intentionally excluded. Its SHA256 and per-source hashes are retained, making the result auditable while requiring the privately retained wheel for byte-identical subject re-execution.
