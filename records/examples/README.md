# Illustration run (not part of any phase)

One run made on 2026-11-04 for the blog post, to show what a fork compaction writes. It belongs to no test,
phase or pre-registration, and `summarize.py` does not read this folder.

- `A1-free`, task `override`, seed 106, threshold 18000, `gpt-6-luna` at effort medium through the Codex
  backend, as in phase 6.
- Harness: this repository at `b6bd7d1`. Kedi: the workspace's editable install at stable `3b90c18`, which is
  `833ce44` plus a formatting commit and the fix that stops native compaction importing other providers' SDKs;
  neither touches history processors.
- Command, from the repository root:
  `KEDI_BENCH_TRAFFIC=<file> ../../.venv/bin/python -m agent_compaction.run --strategy A1-free --task override --seeds 106`

| file | content |
|---|---|
| `override_t18k_A1-free.jsonl` | the run's record, in the format of the phase records |
| `override_seed106_fork_replies.json` | the fork's four replies verbatim, each with the logs read so far and the groups it was offered |

The replies come from the HTTP traffic the run recorded (`KEDI_BENCH_TRAFFIC`). The traffic itself is not
published: the provider's responses carry an account identifier.

Outcome: the run failed. The report named `ece`, owner of the log 8 incident (severity 2); the right owner
is `baran` (log 7, severity 1). The fork's last summary before the report had named `baran`: "Under current
lowest-severity rule, owner among eligible reported incidents is baran (severity 1), assuming no later
severity-1 or lower reported incident in log 8." The probe named the change. In phase 6, `A1-free` passed
this seed and `native` failed it with the same wrong owner.
