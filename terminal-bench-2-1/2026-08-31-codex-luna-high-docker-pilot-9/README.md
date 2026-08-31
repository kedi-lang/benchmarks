# Kedi on Terminal-Bench 2.1: Codex Luna High Docker Pilot

This directory contains the environment, manifests, Harbor evidence, and
replayable Autobench records for Kedi's first nine-task Terminal-Bench 2.1
dogfood run.

## Result

The accepted trials scored **6/9 (66.7%)** at a provider-reported total cost of
**$0.32662052**, or **$0.03629117 per task**. The model was
`codex/gpt-5.6-luna` at high effort, with Docker and concurrency 2. See
[RESULTS.md](RESULTS.md) for the complete metric table.

This is not an official leaderboard submission or a single-revision benchmark.
The run was deliberately stopped whenever a harness defect appeared, Kedi was
fixed, and only invalid or incomplete work was resumed. The nine accepted
trials therefore span three immutable Kedi revisions. The two invalid
`build-cython-ext` attempts are retained as rejected provenance and are not
included in the aggregate.

## Layout

- `environment/` installs exact source revisions and creates a clean,
  single-revision nine-task run.
- `manifests/` contains the three immutable manifests used by the dogfood run.
- `evidence/harbor/` contains sanitized Harbor-authoritative job trees.
- `evidence/autobench/` contains fresh, checksummed Autobench records generated
  from the sanitized Harbor trees.
- `evidence/index.json` is the canonical accepted/rejected trial boundary.
- `sources.lock.json` pins Kedi, kedi-autobench, Autobench, Harbor, and the Kedi
  grammar revisions.
- `scripts/prepare_publication.py` reproduces the privacy-preserving copy and
  index generation process without modifying the source evidence.

## Reproduce A New Run

Prerequisites are Git, `uv`, Docker, and a locally authenticated Codex account.
Credentials are runtime-only inputs. Do not place them in this repository.

```bash
terminal-bench-2-1/2026-08-31-codex-luna-high-docker-pilot-9/environment/setup.sh
terminal-bench-2-1/2026-08-31-codex-luna-high-docker-pilot-9/environment/create-manifest.sh
terminal-bench-2-1/2026-08-31-codex-luna-high-docker-pilot-9/environment/run-with-autobench.sh \
  terminal-bench-2-1/2026-08-31-codex-luna-high-docker-pilot-9/.work/manifests/pilot-9.json \
  kedi-tb21-pilot-9 \
  terminal-bench-2-1/2026-08-31-codex-luna-high-docker-pilot-9/.work/dist/kedi-0.4.0-py3-none-any.whl
```

The generated run uses Kedi revision `69ad944735b0`, the final revision in this
dogfood series. The historical manifests retain the exact wheel digests used by
the original trials, but the original wheel binaries are intentionally not
published. A rebuilt wheel creates a new immutable manifest and therefore a new
experiment identity.

## Replay Published Records

Replay is offline and does not execute Harbor, Kedi, or the model:

```bash
for record in terminal-bench-2-1/2026-08-31-codex-luna-high-docker-pilot-9/evidence/autobench/*; do
  terminal-bench-2-1/2026-08-31-codex-luna-high-docker-pilot-9/.work/kedi-autobench/.venv/bin/autobench replay "$record"
done
```

The three records contain all eleven observed attempts. Use
`evidence/index.json`, rather than directory count, to select the nine accepted
trials for aggregate reporting.

Validate replay, the accepted aggregate, record size, and privacy invariants:

```bash
terminal-bench-2-1/2026-08-31-codex-luna-high-docker-pilot-9/.work/kedi-autobench/.venv/bin/python \
  terminal-bench-2-1/2026-08-31-codex-luna-high-docker-pilot-9/scripts/validate_publication.py
```

## Privacy And Evidence Integrity

Harbor remains the authority for execution and grading. Publication copies are
generated before upload: known dotenv values, credential-shaped values,
secret-keyed JSON fields, private-key blocks, and personal host paths are
removed or replaced. Symlinks are not followed. Binary evidence is copied
unchanged only when it does not match a sensitive filename.

Autobench records are not edited after recording. They are regenerated from the
sanitized Harbor trees under a neutral staging path, then replayed and scanned.
This preserves Autobench manifests and content hashes while ensuring that
personal source paths never enter the published records. The resulting records
are semantically equivalent imports of the public Harbor evidence, not
byte-for-byte copies of the private local records.
