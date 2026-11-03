# Letting the agent compact its own context — experiment report

> Phases 6–8 (pre-registered held-out test, resets, more seeds) are in `FINDINGS.md`, which supersedes the conclusions below where they differ.

Status: 2026-11-01, phases 1–5 complete. Every number below comes from `records/` (tables regenerated in
`results/RESULTS.md`) or, for phase 1, from the probe output recorded in `PLAN.md` §10.

## 1. Question

Long agent runs outgrow their context. The usual fix is *stateless* compaction: when the history gets
long, a separate summarizer turns the old part into a short text and the run continues from it. The
summarizer does not know the task, the rules, or where the work stands.

Hypothesis: the agent that owns the history should compact it — as a continuation of its own
conversation, deciding what to keep verbatim and what to summarize. Expected effects:

1. it loses less of what it still needs,
2. it costs less, because the compaction request reuses the conversation's cached prefix and its output is
   short (ids and summaries, not a rewrite).

This is the first piece of a broader "meta-harness" idea for Kedi: profiles get tools that let the agent
manage its own runtime (history, incremental execution, generated capabilities).

## 2. Design

### Strategies

| id | who compacts | sees | output | what stays verbatim |
|---|---|---|---|---|
| none | — | — | — | everything |
| B1 | Kedi | — | — | last 2 groups (`keep_recent_groups(2)`) |
| B2 | separate request | transcript of the dropped part | free-text summary | last 2 groups |
| B3 | separate request | transcript of the dropped part | JSON: rules, facts, pending, summaries | last 2 groups |
| A1 | the agent (fork) | its full context | JSON: keep ids, rules, facts, pending, summaries | groups the agent lists |
| A1-free | the agent (fork) | its full context | JSON: keep ids + free-text summary | groups the agent lists |
| A1-fixed | the agent (fork) | its full context | JSON: rules, facts, pending, summaries | last 2 groups |

**The fork.** The compaction request is the conversation's own next request with one extra user part
appended to the last message: same model, same instructions, same tool definitions, same cache key. Tools
stay declared but `tool_choice` is `none`, and text output is allowed, so the reply is the JSON proposal.

**Kedi decides the layout, not the model** (`normalizer.py`): unknown ids are rejected; protected,
unfinished and current groups are always kept; kept groups go back to their original order; the
compaction block is inserted at the first dropped group, so everything before it is byte-identical. The
result passes Kedi's history-rewrite validation (atomic tool exchanges, protected entries, exact tail). A
malformed proposal falls back to `keep_recent_groups(4)`; the run never fails because of compaction.

**Integration.** Every strategy is an ordinary Kedi `> history: processor:` with a
`processor_condition` of `estimated_tokens >= 18000`. A `RecordingModel` wrapper adds a stable
`prompt_cache_key`, turns off parallel tool calls and records the last request's parameters for the fork.

### Tasks

All tasks: one Kedi template call; the agent reads logs one `read_log` call at a time (~6.7K tokens each,
routine noise lines plus planted lines) and returns `Report(incidents: list[str], owner: str)`. Rules in the
prompt: ignore service `legacy`; report ids in uppercase, ids only; owner = owner of the reported incident
with the highest current severity.

| task | logs | twist |
|---|---|---|
| t1 | 8 | none |
| rev | 8 | an UPDATE promotes an early incident to severity 10; a RETRACT in the last log withdraws one; a mid-task POLICY CHANGE ("also ignore `search`, including incidents already read") that is **not** in the protected prompt |
| long | 20 | as `rev`, ~135K tokens total, many compactions |
| big | 8 | one log of ~34K tokens, larger than the threshold |

Grading is deterministic. Strict: exact id set, ids only, uppercase, correct owner. Lenient: ids extracted
from the answer, format ignored. Diagnostics: missing incidents, retracted incident reported, policy
violations. Every compaction also records how many incident ids seen so far are still in the context after
it, and whether the rule phrases are still present.

### Setup

`gpt-6-luna`, reasoning effort medium, OpenAI Responses through the Codex subscription backend
(`store=false`), Pydantic AI 2.64, Kedi at `dafe680`. Seeds 1–5, paired across strategies. Details in
`environment.json`.

## 3. Phase 1 — does the fork keep the cache? (cache probe)

Toy history of 3 turns (~26K tokens), two tools, per-run cache key. Six runs per request kind:

| request | cache read |
|---|---|
| normal follow-up on the same prefix | noisy (0%, 33%, 99%) |
| **fork: same prefix + one appended message, JSON reply** | **~99% in 5 of 6 runs** |
| fork with an extra output tool | 0% in 6 of 6 |
| after compaction: kept first turn + block | 0% in 6 of 6 |

- The fork design works: appending one message keeps the prefix cached. Adding an output tool always
  breaks it, because tool definitions are part of the prefix. Hence prompted JSON.
- Without `prompt_cache_key`, hits were rare (1 of 6).
- Cache-preserving layout after compaction did not pay off on this backend; explicit cache breakpoints are
  rejected by this model (`prompt_cache_breakpoint is not supported on this model`). The cost benefit has
  to come from smaller contexts, not cache reuse after compaction.
- Side finding: Pydantic AI 2.57 reported `cache_read_tokens = 0` for this backend while the raw response
  had `cached_tokens`; 2.64 reports it correctly. Kedi moved to 2.64 (`9374d1f`).

> **Correction (2026-11-02).** The phase-1 numbers above were never saved as raw records (only these notes).
> A rerun with raw output (`records/phase1_cache_probe/probe_runs.jsonl`, 6 runs per request kind) did **not**
> reproduce them: the fork hit the cache in 2/6 runs (not 5/6) and the fork with an extra output tool hit it
> once (99.5%), so "an output tool always breaks the cache" is not supported. Cache hits on this backend are
> too noisy to support any cache claim; none of the accuracy or input-token results depend on it.

## 4. Phase 1b — the framework said no (and why)

The first real Kedi runs compacted nothing. Kedi's history classification grouped the *whole* running turn
(prompt plus every tool call and result) as one protected group, `incomplete-response-cycle`, until a final
text answer arrived. A long tool loop — the main reason to compact — could never be trimmed while it ran.
The built-in history archive already replaced closed tool runs inside the current turn, so the protection
was broader than any provider rule required.

Fix in Kedi (`dafe680`, "let history processors trim a running tool loop"): an unfinished turn is now its
protected prompt plus one closed, droppable group per tool exchange that answers every call it makes; open
or orphaned exchanges stay protected. Track A compaction keeps the whole latest cycle as before.

Other framework findings recorded for later (`PLAN.md` §12):
- **1b**: entries with signed or encrypted reasoning are `provider_required` and can never be removed, so
  on reasoning models nothing is trimmed yet. Removing a whole closed exchange is valid for OpenAI and
  Anthropic; planned.
- **2**: typed-output turns end with an output-tool call whose return shares a message with the next
  prompt, so earlier turns of typed-output programs never close. Planned codec-level fix.
- **3**: `Event loop is closed` in a multi-turn prototype run; likely the prototype's raw model call.
- **4**: inserted summary blocks are user messages, so each becomes a protected prompt and old blocks pile
  up; user processors cannot emit replaceable checkpoint entries.

Prototype lessons: Kedi copies wrapper models (record state in a shared dict); the fork needs
`tool_choice: none` or the model calls a tool instead of answering.

## 5. Phase 2 — first comparison (task 1)

| strategy | strict | lenient | median total input | calls |
|---|---|---|---|---|
| none | 3/5 | 3/5 | 212K | 9 |
| B1 truncation | 0/5 | 0/5 | 610K | 63–97 |
| B2 stateless | 1/5 | 3/5 | 182K | 15–97 |
| A1 fork | 5/5 | 5/5 | 134K | 12–13 |

- Truncation drops tool results the agent still needs; it re-reads logs until the 50-request limit.
- No compaction is not the accuracy ceiling: in a ~55K context it missed incidents or picked the wrong
  owner in 2 of 5 runs. Removing noise helped correctness.
- A1's `facts` list carried the incident lines across compactions; fork calls are included in its total.

## 6. Phase 3 — why does the fork win? (ablation, task 1)

| strategy | schema | context | selection | strict | median total input |
|---|---|---|---|---|---|
| A1 | structured | full | agent | 5/5 | 134K |
| A1-free | free text | full | agent | 5/5 | 132K |
| A1-fixed | structured | full | last 2 | 5/5 | 276K |
| B3 | structured | transcript | last 2 | 4/5 | 158K |
| B2 | free text | transcript | last 2 | 1/5 | 157K |

- **The schema is not what makes the fork win**: A1-free equals A1.
- **Agent-chosen retention is what makes it cheap**: A1-fixed is as accurate at 2.1× the input, because
  keeping two raw logs leaves the context at the threshold and triggers twice as many compactions.
- **For an external summarizer the schema matters a lot**: B3 4/5 vs B2 1/5. B2's prose lists incidents
  with service and severity, and the agent copies that format into its answer, against the rule.
- **Nothing was lost**: in all 158 compactions, every incident seen so far was still in the context
  afterwards, and the rule phrases stayed (the task prompt is protected). Failures came from format and
  from losing track of progress, not from missing facts.
- **Progress state** is a candidate mechanism: the stateless summarizer never filled `pending` (it does not
  know where the task stands); the fork always wrote an exact next step ("read log_6, then log_7, then
  log_8"). B3's two runs that took 47–49 calls had no progress state at all. Not yet isolated.

## 7. Phase 4 — edge cases built to break it

Strict pass, 5 seeds each:

| strategy | t1 | rev | long | big | total |
|---|---|---|---|---|---|
| none | 3/5 | 3/5 | 2/5 | 5/5 | 13/20 |
| **A1-free** | 5/5 | 5/5 | 5/5 | 5/5 | **20/20** |
| A1 | 5/5 | 5/5 | 4/5 | 5/5 | 19/20 |
| B3 | 4/5 | 4/5 | 3/5 | 5/5 | 16/20 |
| B2 | 1/5 | 0/5 | 2/5 | 3/5 | 6/20 |

(t1 column for A1, A1-free, B2, B3 from phase 3; for none from phase 2.)

Median total input — rev / long / big: none 213K / 1227K / 328K; A1-free 161K / 411K / 203K;
A1 135K / 470K / 237K; B3 158K / 624K / 578K; B2 182K / 487K / 543K.

What broke, `rev` + `long`:
- **Mid-task rule** (survives only through compaction): fork variants 0 violations; B2 12; B3 6; no
  compaction 3 (attention in a 50–400K context, not loss).
- **Retracted incident reported**: fork 0; B2 5; B3 2.
- **Missing incidents**: B2 11, B3 11, A1 10 (all in one run, below), A1-free 0.
- **Cost of no compaction on `long`**: 1.2M median input; one run exceeded Kedi's 1M cumulative
  uncached-input budget and failed.
- **A1's only failure**: a premature final answer after 6 calls, with a correct `pending` ("read logs
  6–20") in its last compaction; B2 stopped early once too. Not a compaction loss.
- **Stateless loops**: without progress state, B2/B3 sometimes re-read logs, up to 79 calls.

Statistics, paired on the same (task, seed), exact one-sided McNemar (primary; `results/RESULTS.md`):
- A1-free vs none p = 0.008 (7 vs 0 discordant); vs B2 p = 0.0001 (14 vs 0); vs B3 p = 0.0625 (4 vs 0);
  vs A1 p = 0.5.
- Unpaired Fisher (secondary): fork (A1 + A1-free) 39/40 vs stateless (B2 + B3) 22/40, p = 4·10⁻⁶.

## 7b. Phase 5 — against the provider's own compaction

The strongest real competitor is the provider's compaction. OpenAI's server-side compaction (the
`context_management` / `compact_threshold` mechanism, run inside the normal `/responses` request and
returning an opaque `compaction` item) works on the Codex backend; it was attached through Pydantic AI's
`OpenAICompaction(token_threshold=18000)`, same trigger point as the other strategies. The stateless
`/responses/compact` endpoint (Codex CLI's remote compaction) returns 404 on this backend and could not be
tested.

| task | native strict | A1-free strict | native median input | A1-free median input |
|---|---|---|---|---|
| t1 | 5/5 | 5/5 | 105K | 132K |
| rev | 3/5 | 5/5 | 106K | 161K |
| long | 3/5 | 5/5 | 269K | 411K |
| big | 5/5 | 5/5 | 129K | 203K |
| total | 16/20 | 20/20 | | |

- **Native is the cheapest strategy** — about 30–35% less input than the fork. Compaction runs inside a
  normal request: no extra round trip and a short opaque item instead of a text summary.
- **Native loses the mid-task rule**: all of its failures are policy violations (3 in `rev`, 4 in `long`) —
  it reported `search` incidents after the POLICY CHANGE; one `long` run also hit the request limit. It never
  reported a retracted incident and never missed one.
- On the tasks where a rule arrives mid-task (rev + long): A1-free 10/10, A1 9/10, B3 7/10, native 6/10,
  none 5/10, B2 2/10. A1-free vs native there: 4 discordant pairs, all favoring A1-free — exact one-sided McNemar p = 0.0625 (paired, primary); an unpaired Fisher test would give 0.043, but runs share seeds, so the paired test is the right one.
- Kedi bug found on the way: `> history: compaction_mode: native` fails whenever a run budget is active,
  because the model-type check runs on Kedi's budget wrapper instead of the provider model.

So the trade-off is explicit: provider compaction is cheaper; agent-led compaction keeps instructions that
arrive during the task. Neither dominates on both axes yet.

## 8. Conclusion — what is shown and what is not

Shown, on four synthetic tasks with one model:
- Compacting with the agent's own context (the fork) is significantly better than no compaction and than a
  free-text external summary, and at least as accurate as the best structured external summary and the
  provider's own compaction (paired McNemar p = 0.0625 for both over 20 runs: 4 discordant pairs each, all in its favor).
- Its specific advantage is **instructions that arrive during the task**: on the tasks with a mid-task rule
  it was 10/10 against 6/10 for provider compaction and 7/10 for the best external summary — not yet significant on a paired test (p = 0.0625); a held-out, pre-registered evaluation is set up in `PREREGISTRATION.md`.
- Provider compaction is the cheapest (~30–35% less input than the fork); the fork is the cheapest of the
  strategies that keep the mid-task rule.
- What matters for the fork is that the agent compacts with its full context and chooses what stays; its
  output schema does not matter. For an external summarizer the schema matters a lot.
- Compaction improves correctness, not only cost: an unmanaged 55–400K context made more mistakes than a
  managed one, including breaking a rule it could still see.
- It works in Kedi today as an ordinary history processor, after one framework fix.

Not shown yet:
- other models and providers; reasoning-on runs (blocked by item 1b);
- real coding / research / tool-heavy tasks instead of synthetic logs;
- a decisive margin over the structured external summary and over provider compaction (needs more seeds);
- the stateless `/responses/compact` endpoint (unavailable on the Codex backend);
- the progress-state mechanism in isolation.

## 9. Next steps (in order of evidence per cost)

1. More seeds for A1-free vs B3 and vs native (n ≈ 15), and more mid-task-rule tasks, to settle the borderline comparisons.
2. A second model.
3. Isolate the mechanism: A1 without `pending`; B3 with a Kedi-computed progress line.
4. Item 1b, then a reasoning-on run.
5. Longer contexts (150K+) with a threshold sweep (18K / 32K / 64K).
6. Real tasks: a coding task with many file reads, a multi-step research task.

## 10. Timeline

| when | what |
|---|---|
| phase 0 | plan written (`PLAN.md` §1–9) |
| phase 1 | normalizer + cache probe; fork keeps ~99% cache, output tool breaks it |
| Kedi `9374d1f` | move to Pydantic AI 2.64 (cache usage reported correctly; `kedi-typesafe` 0.3.2 and `kedi-decisions` 0.1.2 released) |
| phase 1b | first Kedi runs compact nothing; grouping limitation found |
| Kedi `dafe680` | running tool loops become trimmable |
| phase 2 | A1 5/5 vs none 3/5, B2 1/5, B1 0/5 |
| phase 3 | ablation: schema irrelevant for the fork; agent-chosen retention makes it cheap |
| phase 4 | edge cases: A1-free 20/20; fork 39/40 vs stateless 22/40 |
| phase 5 | provider compaction: 16/20, cheapest, loses mid-task rules (rev + long 6/10 vs fork 10/10) |
| phases 6–9 | held-out and pre-registered tests; see `FINDINGS.md`. Phase 9: long horizon confirmed (15/15 vs 8/15, p = 0.0078); second model at a floor (not confirmed); fake instruction obeyed by no strategy |
