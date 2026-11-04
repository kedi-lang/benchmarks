# Pre-registration — held-out evaluation (phase 6)

Written and committed **before** any phase-6 run. The commit timestamp is the record. Phases 1–5 were
exploratory; their tasks and seeds are not reused here.

## Hypotheses

- **H1 (primary).** On tasks where an instruction changes during the task, agent-led compaction (A1-free)
  passes strictly more often than provider compaction (native).
  Test: exact one-sided McNemar on paired (task, seed) runs over the three instruction-change tasks
  pooled, α = 0.05.
- **H2 (secondary).** A1-free is not worse than native on the same tasks when the instruction change comes
  *before* the first compaction (control): reported descriptively, paired.
- **H3 (secondary, mechanism).** When native fails an instruction-change task, the changed instruction is
  absent from what the model can recall afterwards (rule-recall probe), i.e. compaction lost it rather than
  the model ignoring it. Reported as counts; no significance claim.

## Strategies

Primary: `A1-free` (fork, free text, agent-chosen retention) and `native` (OpenAI server-side compaction).
Secondary, reported but not part of H1: `none`, `B3`.
`native` runs through Kedi's own `> history: compaction_mode: native` path once the run-budget bug is fixed
(identical capability to the phase-5 runs). Threshold 18000 for all; same trigger estimate.

## Tasks (new, held out)

All reuse the log-audit frame (one `read_log` call per log, 8 logs, one INCIDENT line each, protected
prompt with the three base rules), with exactly one mid-task instruction line placed in log `k`:

| task | instruction in log k | what the final answer must reflect |
|---|---|---|
| `override` | "OWNER RULE CHANGE: from now on `owner` is the owner of the reported incident with the LOWEST current severity." | owner by lowest severity |
| `format` | "FORMAT CHANGE: from now on report incident ids in lowercase, ids only." | lowercase ids (strict grader uses lowercase) |
| `scope` | "SCOPE CHANGE: from now on report only incidents from services `billing`, `auth` and `payments`, including ones already read." | only those services |

Placement: `k` = 5 (after the first compaction, which triggers after log 3 at this threshold) — the case
where only compaction can carry the instruction.

Timing control (H2): the same three tasks with the instruction in log `k` = 2 (before the first
compaction). Suffix `-early`.

## Seeds and size

Seeds 101–115 (n = 15 per task, strategy, timing) — never used before. Primary analysis: 3 tasks × 15 seeds
= 45 paired runs per strategy at `k` = 5.

## Metrics

Primary: strict pass. Also recorded per run: lenient pass, total input (main + compaction), output tokens,
calls, wall-clock seconds, compactions, and the rule-recall probe.

**Rule-recall probe (H3):** after the final report, one more turn in the same Kedi session asks
"List every instruction that is currently in force for this task, including any that changed during the
task." The answer is graded for the presence of the changed instruction (keyword match defined per task:
`lowest`, `lowercase`, `billing`+`auth`+`payments`). The probe runs after grading and cannot change it.

## Stopping and exclusions

All runs are reported. A run that fails for an infrastructure reason unrelated to the strategy (HTTP 5xx,
connection errors) is rerun once with the same seed and both attempts are recorded; request-limit and
budget failures count as failures of the strategy. No other exclusions. No additional seeds are added after
looking at results; if the result is inconclusive it is reported as such.
