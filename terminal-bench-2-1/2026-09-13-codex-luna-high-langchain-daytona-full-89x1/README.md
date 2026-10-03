# Kedi / LangChain: Terminal-Bench 2.1, 89x1

Frozen September 13-14, 2026 Daytona run, published from the original local archive.
**68/89 solved (76.40%), $5.05064428 estimated cost, 93.6471% cache reads.**
There are 20 reward-zero trials and one unscored verifier timeout; see [RESULTS.md](RESULTS.md).

## Experiment

- Codex `gpt-5.6-luna`, high effort, LangChain adapter.
- Native WebSocket first with HTTP recovery/fallback; codex-auth-helper 1.8.0.
- 81 standard tasks at concurrency 2, eight high-memory tasks at concurrency 1.
- Daytona execution, independent of the local Mac controller or its network.
- Six-hour agent timeout; task-specific verifier timeouts remain separate.
- QEMU task fixes and frozen sources follow the recorded experiment contract.
- Same frozen Kedi/helper wheels, prompts, tools, artifact policy and task manifests
  as the [Pydantic control](../2026-09-12-codex-luna-high-daytona-full-89x1/).
- No Logfire instrumentation was added to this run.

[Exact runtime dependencies](manifests/runtime-constraints.txt),
[controller dependencies](manifests/controller-constraints.txt),
[source contract](manifests/experiment-contract.json), and
[source revisions](manifests/expected-sources.json) preserve the measured environment.
The publication tooling does not rerun tasks with today's Kedi sources.

## Evidence Layout

- `evidence/autobench/full89/`: **one** replayable derived Autobench record containing all 89 trials.
- `evidence/harbor/`: original batch/trial layout, with sanitized file contents.
- `evidence/index.json`: exact task and trial identities and original rewards.
- `evidence/metrics.json`: request-priced metrics, including per-request costs.
- `evidence/pricing.json`: estimator version and pricing method.
- `evidence/sanitization-report.json`: original archive/file hashes and every omission.
- `checksums.sha256`: integrity manifest for the complete publication.

Raw source records were not rewritten. Credentials, private local paths, and sensitive
JSON keys are redacted in the publication copy. Non-text binaries and oversized files
are omitted with hashes; references to omitted artifacts do not imply those bytes
are publicly available. No authentication files, environments, wheels, or raw archive
are distributed. Harbor failures are retained, not retried or replaced.

Original LangChain cost fields were `null`; costs were repaired **only in derived
metrics and the merged Autobench record**, using request-level `genai-prices` estimates.
They are not provider-reported charges. This is a capture/import operation, not a
second experiment. Capture timing in the merged record is not task execution time;
use the `terminal_bench.duration` observation and original timestamps.

## Replay

From this directory, use the same pinned Autobench environment as the control:

```bash
bash ../2026-09-12-codex-luna-high-daytona-full-89x1/environment/setup-replay.sh
../2026-09-12-codex-luna-high-daytona-full-89x1/.venv-replay/bin/python scripts/validate.py
```

Validation checks all 89 identities, rewards (including the unscored trial), usage,
estimated costs, source-reference hashes, checksums and secret patterns. It makes
no model calls and needs no API credentials. `scripts/prepare.py` requires the
private original archive and `genai-prices==0.1.7`; it refuses to replace an existing
publication. `scripts/report.py` renders the report from saved metrics.
