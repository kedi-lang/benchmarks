# Agent-led compaction — experiment plan

Status: plan (2026-11-01). Meta-harness idea #1: the agent that owns the history compacts it.

## 1. Hypothesis

Compaction is a reset either way, so the baseline is a stateless summary, not the uncompacted history.
An agent that compacts its *own* history, as a continuation of the same conversation, should:

1. **Lose less**: it knows which facts, rules and results it still needs; a stateless summarizer guesses.
2. **Cost less**: the compaction request reuses the conversation prefix (cache read), and the output is short
   (ids + summaries + rules), not a rewrite of the history.
3. **Keep part of the cache after compaction**: verbatim kept groups stay at the front in original order, so the
   next request reads the cache up to the first dropped group; only the new summary block is written.

Success = equal or better task success and probe recall than the stateless baseline, at equal or lower total
input cost (cache read + cache write + uncached input) over the whole run.

## 2. What already exists (no new framework needed for the prototype)

- `> history: processor: / processor_condition:` (Pydantic AI, LangChain). The processor receives
  `HistoryProcessorContext`: native `messages`, `entries`, atomic `groups` (`closed`, `protected`,
  `origins`), `estimated_tokens`, `request_index`, `cache_epoch` — `src/kedi/agent_adapter/history_processing.py`.
- Rewrite validation already enforces what the agent must not break: atomic groups (tool call/return pairs),
  protected entries/barriers, new-entry rules — `_validate_atomic_groups`, `_validate_protected_*`,
  `_validate_new_entries` in the same file.
- Track A Kedi compaction primitives (snapshot → plan → checkpoint with `durable_facts`, `decisions`,
  `constraints`, `pending_work`, `errors_and_lessons`, anchors) — `src/kedi/agent_adapter/compaction/`.
  It is a single contiguous window and "deliberately does not summarize or auto-run"; no adapter sets
  `history_replace`, so it is unwired. Reuse its checkpoint vocabulary, not its single-window planner.
- Archive of dropped history to artifacts — `compaction/pydantic_archive.py`, `langchain_archive.py`.
- Usage accounting incl. cache read/write — `CompactionUsage`, adapter telemetry.

So phase 1 is a **processor callable**, not a language change.

## 3. Design

### 3.1 Trigger
`processor_condition`: `state.estimated_tokens >= threshold` (default: ~70% of the model window). A no-op
result preserves native identity and cache generation, so non-triggering requests cost nothing.

### 3.2 The compaction call is a fork of the conversation
- Same model, same system/instructions, same tool definitions, same message list, plus one appended user
  message with the compaction instruction. Anything that changes the prefix (an extra output tool, a different
  tool order, a structured-output schema if the provider caches it) costs the cache — measure it (§6, Q1).
- Output is requested as prompted JSON in that final message, not via a new output tool.
- The fork is a direct model request, not a run of the profile: no tools executed, no history processing
  (no recursion), counted against the run's request budget.

### 3.3 Output contract (from the model)
```json
{
  "keep":      ["g12", "g13", "g20"],            // group ids, any order
  "summaries": [{"text": "...", "covers": ["g3", "g4"]}],   // priority order
  "rules":     ["..."],                          // durable constraints, priority order
  "facts":     ["..."],                          // durable facts / decisions
  "pending":   ["..."]                           // open work
}
```
Group ids, not message ids: groups are the unit the validator already treats as atomic.

### 3.4 Deterministic normalizer (Kedi, never the model)
1. Unknown ids → rejected (one retry with the error, then fall back to §3.6).
2. Forced keep: protected groups, unclosed groups, the current-request group, the system/instruction prefix.
3. Kept verbatim groups are re-sorted into **original order** (the model's order for old groups is advisory;
   report when it disagreed). The model's priority order applies only to the new block.
4. Layout: `[longest unchanged kept prefix][compaction block][remaining kept groups, original order][tail]`.
   The block sits at the first dropped group, so chronology stays readable and everything before it stays cached.
5. Compaction block = one message: rules, facts, pending, summaries (priority order) + an archive reference
   for the dropped groups so the agent can ask for them later.
6. `covers` must reference dropped groups only; uncovered dropped groups are listed as "archived, not summarized".
7. Result goes through the existing rewrite validation; a validation failure falls back (§3.6).

### 3.5 Recall
Dropped groups are archived as artifacts (existing archive code); the block names the artifact so the agent can
read it back with the artifact tools. Measured as recall rate in §5.

### 3.6 Fallback
On malformed output twice or validation failure: `keep_recent_groups(n)` + telemetry event. Never fail the run.

## 4. Baselines

| id | strategy |
|----|----------|
| B0 | no compaction (only where the task fits the window; upper bound on recall) |
| B1 | `keep_recent_groups(n)` (truncation) |
| B2 | stateless summary: separate request, summarizer prompt over the dropped window, Track A checkpoint fields |
| A1 | agent-led fork (this plan) |
| A2 | A1 without cache-preserving layout (block first) — isolates the layout's cache effect |

Same model and effort for all (default `gpt-6-luna`, `medium`, via the subscription helper as in the subagent
benchmark), paired seeds, n ≥ 5 per cell.

## 5. Tasks and probes

Long-horizon tasks that force ≥ 2 compactions at the chosen threshold:

1. **Rules early, work late.** Constraints given in the first turns (naming rule, forbidden path, output format),
   then many noisy tool results (large file reads/searches), then work that must obey the rules.
2. **Facts buried in tool output.** A value appears once in a large tool result and is needed much later.
3. **Evolving plan.** Decisions revised mid-run; the final answer must use the *latest* decision (tests whether
   summaries keep superseded vs current state).
4. **Recall path.** A needed detail is intentionally too large to summarize; success requires reading the archive.

Probes: after the last compaction, ask fixed questions about planted facts/rules (graded exactly); plus task
success graded by a deterministic checker.

## 6. Metrics

- Task success; probe accuracy (facts, rules, latest decisions).
- Per compaction: input / cache-read / cache-write / output tokens of the fork; latency.
- Next request after compaction: cache-read ratio; kept-prefix length.
- Whole run: total cost proxy = uncached input + cache write + α·cache read + output.
- Normalizer stats: unknown ids, reorder disagreements, forced keeps, fallbacks, archive reads.

Open measurement questions:
- Q1: does prompted JSON in the appended message keep the full prefix cached on each provider? (vs. schema)
- Q2: how often does the model drop something it later needs (probe failure with no archive read)?
- Q3: does priority ordering of the block matter vs chronological?

## 7. Phases

1. **Prototype (benchmark only, no repo change).** Processor callable + normalizer in
   `benchmarks/agent_compaction/`; Pydantic adapter only. Unit tests for the normalizer on synthetic group lists.
   Deliverable: one task end to end with telemetry.
2. **Benchmark.** Tasks 1–4, baselines B1, B2, A1, A2 (B0 where it fits). Results + findings in this file.
3. **Decision.** If A1 wins: productize as a stdlib processor (e.g. `kedi.history.agent_compactor(...)`) usable
   via `> history: processor:`; later, a `compaction: mode: agent` that wires Track A's `history_replace`.
   If it loses: record why (cost, recall) and stop.

## 8. Risks

- Fork prefix mismatch silently kills the cache advantage → Q1 measured first in phase 1.
- Model over-drops: mitigated by forced keeps, `covers`, archive recall; measured by probes.
- Superseded decisions kept as facts: task 3 targets it; block separates `facts` from `pending`.
- Adapter scope: Codex/A2A manage history natively (no processor) → out of scope.
- Budget: fork requests count against request budgets; threshold too low → many forks.

## 9. Decisions needed

1. Threshold default for the benchmark (proposal: 70% of window, plus a small-window variant to force more
   compactions cheaply).
2. Whether B2 uses the same model or a cheaper one (proposal: same, to isolate strategy).
3. Phase 1 limited to Pydantic AI (proposal: yes).

## 10. Phase 1 findings (2026-11-01, gpt-6-luna via Codex backend, medium)

Code: `benchmarks/agent_compaction/` — `normalizer.py` (+6 unit tests, passing), `cache_probe.py`.
History: 3 turns, ~8.8K tokens each (26.4K total), 2 function tools, `openai_prompt_cache_key` per run.

| request | runs | cache read |
|---|---|---|
| R2 normal follow-up (same prefix) | 6 | 0%, 99%, 33%, 33%, … (noisy) |
| **R3 fork + prompted JSON** | 6 | **99% in 5/6** (0% once) |
| R4 fork + extra output tool | 6 | **0% in 6/6** |
| R5 kept first turn + block | 6 | 0% in 6/6 |
| R6 block only | 6 | 0% (103 tokens, irrelevant) |

1. **Q1 answered: the fork design works.** Appending one message keeps the whole prefix cached; adding an output
   tool always breaks it (tools sit in the prefix). Keep prompted JSON.
2. **Without `prompt_cache_key` hits are rare** (first run: only one hit in 6). The prototype must set a stable
   key per conversation.
3. **Cache hits land on earlier requests' turn boundaries** (hits of 8704 / 17408 / 26240 = turn ends). Growing
   the conversation turn by turn creates them; sending the history at once does not.
4. **The partial-prefix benefit after compaction (R5) did not show up** (0/6), although the same boundary served R2.
   Explicit breakpoints (`CachePoint`) are rejected by this model (`prompt_cache_breakpoint is not supported`).
   So for this provider, plan to count on the fork's cache read, not on cache reuse after compaction; keep A2
   (layout ablation) to measure whether the layout helps at all here.
5. **Pydantic AI 2.57 reports `cache_read_tokens=0` for this backend** while the raw response has
   `input_tokens_details.cached_tokens`. The probe reads raw usage. Kedi's compaction/usage telemetry on this
   adapter would under-report cache reads; check 2.64 before trusting `CompactionUsage` numbers.
6. Fork output quality on the toy history: valid JSON on every run, rules and the planted fact (port 8123)
   extracted; it dropped everything (logs were noise), which is the intended behavior.

Next: prototype processor in a real Kedi run (Pydantic adapter, growing conversation, stable cache key), task 1,
A1 vs B2, n=5.

## 11. Phase 1b — first Kedi runs (2026-11-01, Pydantic AI 2.64)

Prototype: `compactor.py` (RecordingModel, A1/B2/B1 processors), `task1.py`, `state.py`, `run.py`.
Prototype fixes on the way: Kedi copies wrapper models (`vars` copy) so recorded request params live in
a shared dict; `WrapperModel._settings` shadows a method of that name; the fork needs
`tool_choice: "none"` + `allow_text_output=True` or the model calls a tool instead of answering.
Pydantic AI 2.64 reports Codex cache reads in Kedi's invocation usage (finding #5 is fixed by 2.64).

**Blocking finding: Kedi's history groups leave nothing a processor may drop in these runs.**

1. *Inside one invocation's tool loop* the whole cycle (user prompt + every tool call/return) is a single
   protected group (`incomplete-response-cycle`) until a final assistant text arrives. A long agent loop —
   the main reason to compact — can never be compacted while it runs.
2. *Across Kedi invocations with typed outputs* every turn ends with the output tool call/return, never an
   assistant text, so `has_terminal_response` is false and no group ever closes. Worse, the next user prompt
   is sent in the same `ModelRequest` as the previous output-tool return (`tool-return,user-prompt`), so the
   group boundary falls inside that message: the previous group gets `open-lifecycle`, the next one
   `orphan-lifecycle-result`. Observed for all 4–5 groups of an 8-turn run.
3. Separately, turn 2 of the multi-turn run failed with `RuntimeError: Event loop is closed` (not yet
   isolated: the fork calls the raw model, whose client may be bound to the previous invocation's loop).

Seed 1, single-invocation variant (before the fork fix): A1 still answered correctly (7/7, rules and owner)
because nothing was ever removed — it is not a compaction result.

Decision needed (framework): classify an output-tool call/return as a terminal response, and split tool
cycles inside a running response cycle into atomic call/return groups (keeping the prompt and the open call
protected), subject to provider rules (e.g. Anthropic thinking blocks within the current turn).

## 12. Framework work items (decided 2026-11-01)

### 1 — Split unfinished cycles (DONE, see commit)
`compaction/classification.py`: a cycle with a user prompt and no terminal response is grouped as its
protected prompt (`incomplete-response-cycle`) plus one group per run of units that opens and answers every
tool call; such an exchange is closed and droppable, one without any call gets `incomplete-exchange`, open
or orphaned ones keep `open-lifecycle` / `orphan-lifecycle-result`. `selection.py`: Track A's
`latest-cycle` now covers every group from the latest prompt on, so its windows are unchanged.
Evidence it is safe: the built-in history archive (`archive.py::_select_window`) already replaces closed
call/return runs *inside the current turn* and Harbor runs depend on it.
Spec follow-up (blocked on unrelated uncommitted edits to `docs/KEDI_DSL.md` and its mirrors): state in the
`keep_recent_groups` paragraph that a running tool loop is its prompt plus one group per finished exchange.

### 1b — Whole-exchange removal with provider replay data
`pydantic_codec.py` marks every entry with signed/encrypted reasoning (`ThinkingPart.signature/id`,
`encrypted_content`, …) `provider_required`, and `_validate_protected_entries` refuses to remove it. The stated
reason (`_contains_provider_replay_data`: "must remain byte-for-byte replayable") is about *modifying* an entry;
removing a whole closed exchange (reasoning + call + returns) is accepted by OpenAI Responses and by Anthropic
for every assistant message but the last. With reasoning on, every tool-call response carries such data, so
item 1 alone trims nothing on reasoning models.
Plan:
1. Split the meaning: `provider_required` → keep byte-identical *if kept*; new `replay_pinned` only for entries
   that must never be removed (mixed system prompt, tool-availability deltas, capability load parts).
2. Validator: a provider-replay entry may be removed only together with its whole closed group; partial
   removal or modification still fails.
3. Keep the last assistant response of the running cycle pinned (Anthropic: thinking of the latest assistant
   turn must be replayed; Gemini thought signatures for current-turn calls) — already guaranteed by the tail
   and open-lifecycle rules; add an explicit test per provider codec.
4. Tests: reasoning-bearing tool loop trimmed by `keep_recent_groups`; refusal when a processor keeps the call
   but drops its reasoning; live smoke on gpt-6-luna with reasoning `high` (encrypted reasoning included).
Risk: provider-specific replay rules not covered by tests (Bedrock, Gemini) — gate behind the codec
(Pydantic codec first), LangChain keeps today's behavior until verified.

### 2 — Typed-output turns never close
Cause: a Kedi turn with a typed output ends with the output tool call and its return (`Final result
processed.`); Pydantic AI then appends the next prompt to that same `ModelRequest`
(`tool-return,user-prompt`). The previous cycle keeps an open lifecycle, the next starts with an orphan
result, and neither is ever closed — so no processor can drop any earlier turn of a typed-output program.
Options considered:
- (a) Treat an output-tool call as the terminal response and let the closing return live in the next group
  → dropping the previous group leaves an orphan `tool-return` in the kept message; providers reject it.
- (b) Codec splits a `ModelRequest` carrying `[output-tool returns…, user prompt]` into two logical entries
  for grouping, and the processor runner re-merges on assembly → touches every validator that matches
  entries by fingerprint; high risk.
- (c) **Chosen:** when a processor drops the group that owns an output-tool call, Kedi strips that call's
  return parts from the next kept message and re-emits it as a new user-text message (allowed: new entries
  may be complete user text). Classification marks such a pair `output-cycle` so the previous turn counts as
  closed only through this path.
Steps:
1. Codec: know the output tool names (from the run's `ModelRequestParameters.output_tools`, recorded per
   request by the Pydantic adapter) and tag output-tool lifecycle ids.
2. Classification: a cycle whose only unresolved ids are output-tool calls answered in the next entry is
   closed; the next group's orphan results for those ids are not orphans.
3. Runner: after the user processor returns, if an output-cycle group was dropped, rewrite the next kept
   message without the returns; validate as today.
4. Tests: multi-turn typed-output program trimmed by `keep_recent_groups(1)`; provider mapping of the
   rewritten message (OpenAI, Anthropic); LangChain unaffected (no merged messages — verify).
Open question: whether Kedi should instead stop leaving the output-tool exchange in history (store the
validated output as assistant text). Rejected for now: it changes provider-native history and caching.

### 3 — `Event loop is closed` in multi-turn runs (benchmark-side first)
Observed on turn 2 of the 8-turn A1 run. Hypothesis: the fork calls the raw model (`model.wrapped`),
whose HTTP client was created on turn 1's event loop; Kedi refreshes the client it uses through its own
wrapper copy (`_refresh_http_client`) but the fork bypasses it.
Steps:
1. Reproduce with B1 (no fork) and A1 on 2 turns. If B1 passes, it is the prototype: send the fork through
   the copied wrapper's model (record `self` in the shared dict) or call `_refresh_http_client()` first.
2. If B1 also fails, it is Kedi: bisect between `InteractiveSession` turns with history enabled and a
   processor active; add a regression test with an async processor that awaits a model call.

## 13. Phase 2 — Task 1 results (2026-11-01, after item 1; gpt-6-luna medium, threshold 18K, n=5)

Single invocation, 8 sequential `read_log` calls (~6.7K tokens each), rules in the prompt.

| strategy | strict pass | lenient pass¹ | main input | fork input | total input | requests | compactions | failures |
|---|---|---|---|---|---|---|---|---|
| none (B0) | 3/5 | 3/5 | 213K | – | 213K | 9 | 0 | missed 2 incidents; wrong owner |
| B1 truncation (keep 2) | 0/5 | 0/5 | 712K | – | 712K | 46.6 | 30–47 | 4× request limit (re-reads dropped logs) |
| B2 stateless summary | 1/5 | 3/5 | 322K | 77K | 399K | 17.6 | 6–47 | ids annotated against rule; 1× request limit |
| **A1 agent fork** | **5/5** | **5/5** | **79K** | **61K** | **140K** | **9** | **3–4** | 1 fallback (malformed JSON), recovered |

¹ incident ids extracted from the answer, ignoring the format rule.

Readings:
- A1 is the only strategy that kept every fact *and* every rule: 5/5, with the same 9 requests as no
  compaction and 34% less total input. Its `facts` list accumulated the incident lines verbatim across
  compactions, and the rules list carried "report ids only, uppercase".
- No compaction (B0) lost accuracy in a 55K-token context (2/5 wrong), so compaction here is not only a
  cost tool: dropping noise helped correctness.
- B1 truncation drops the tool results the model still needs, so it re-reads logs until the request limit.
- B2's summaries kept the incidents but not the output-format rule strictly (ids annotated with service and
  severity in 3 of 4 answers) and it is re-triggered more often because its summary is longer.
- Cache: reads stayed low for all strategies in this backend (A1 fork 7.5K of 61K, main 6K); the cost win
  comes from smaller context, not from cache reuse. Matches phase-1 R5.

Caveats: one task, n=5, one model; the threshold forces compaction roughly every 2–3 logs. Next: tasks 2–4
(buried fact, evolving decision, archive recall), and a reasoning-on run once item 1b lands.

## 14. Ablation (2026-11-01, same task/model/threshold, seeds 1–5 paired; records in records/, run 1 in records/run1/)

| strategy | schema | context | selection | strict | lenient | median total input | calls (main+fork) | compactions |
|---|---|---|---|---|---|---|---|---|
| A1 | structured | full (fork) | dynamic | 5/5 | 5/5 | 134K | 12–13 | 3–4 |
| A1-free | free text | full (fork) | dynamic | 5/5 | 5/5 | 132K | 12–13 | 3–4 |
| A1-fixed | structured | full (fork) | last 2 groups | 5/5 | 5/5 | 277K | 15 | 6 |
| B3 | structured | transcript | last 2 groups | 4/5 | 5/5 | 158K | 15, 15, 15, 49, 47 | 6–23 |
| B2 | free text | transcript | last 2 groups | 1/5 | 4/5 | 158K | 15–17 | 6–7 |

Retention probe: in all 158 compactions no planted incident seen so far was missing from the post-compaction
context, and all three rule phrases stayed (the task prompt is protected). Failures are not fact or rule *loss*.

Readings:
- **Schema is not what makes the fork win**: A1-free = A1 on accuracy and cost.
- **Dynamic selection is what makes it cheap**: A1-fixed keeps the same accuracy at 2.1× the input and twice
  the compactions (keeping two raw logs keeps the context near the threshold).
- **For stateless summaries the schema matters a lot**: B3 4/5 vs B2 1/5 strict. B2's free-text summary lists
  incidents with service/severity and the agent copies that format into the answer, against the rule.
- **Progress state**: the stateless summarizer never writes `pending` (empty in every B3 compaction — it does not
  know where the task stands); the fork writes an exact one ("read log_6, then log_7, then log_8"). B3's two
  runs at 47–49 calls had no stale pending; they had none. Candidate mechanism for the fork's advantage:
  it records *where the work is*, not only what was learned. Not yet isolated (needs a B3 + injected progress
  cell, or a fork with `pending` removed).
- Framework note: inserted summary blocks are user messages, so classification makes each one the protected
  prompt of a new cycle; older blocks can never be dropped and accumulate. User processors cannot emit
  checkpoint entries (validator), so there is no replaceable summary slot. → new item 4 for the framework list.

Next cheapest ablations: A1 without `pending` (structured) and B3 + progress line computed by Kedi.

## 15. Edge cases (2026-11-01; tasks rev/long/big in `task2.py`, threshold 18K, seeds 1–5, gpt-6-luna medium)

`rev`: 8 logs, UPDATE (promotes an early incident to severity 10), RETRACT (false alarm in the last log), and a
mid-task POLICY CHANGE ("also ignore `search`, including incidents already read") that is *not* in the
protected prompt. `long`: same with 20 logs (~135K tokens). `big`: one log of ~34K tokens (> threshold).

Strict pass (ids only, uppercase, correct owner):

| strategy | t1 | rev | long | big | total | median total input rev / long / big |
|---|---|---|---|---|---|---|
| none | 3/5 | 3/5 | 2/5 | 5/5 | 13/20 | 213K / 1227K / 328K |
| **A1-free** (fork, free text, dynamic) | 5/5 | 5/5 | 5/5 | 5/5 | **20/20** | 161K / 411K / 203K |
| A1 (fork, structured, dynamic) | 5/5 | 5/5 | 4/5 | 5/5 | 19/20 | 135K / 470K / 237K |
| B3 (stateless, structured, last 2) | 4/5 | 4/5 | 3/5 | 5/5 | 16/20 | 158K / 624K / 578K |
| B2 (stateless, free text, last 2) | 1/5 | 0/5 | 2/5 | 3/5 | 6/20 | 182K / 487K / 543K |

Failure causes (rev + long): B2 reported the retracted incident 5× and broke the mid-task policy 12×; B3 broke
the policy 6× and missed 11 incidents; no compaction broke the policy 3× (attention in a 50–400K context, not
loss) and on `long` one run exceeded Kedi's 1M cumulative uncached-input budget. Fork variants: 0 policy
violations, 0 retracted incidents reported; A1's one failure is a premature final answer after 6 calls with
a correct `pending` ("read logs 6–20") — the same premature stop happened once to B2.

One-sided Fisher exact, strict pass over all 20 runs:
- A1-free vs none p = 0.004; vs B2 p < 0.0001; vs B3 p = 0.053; vs A1 p = 0.5 (no difference).
- Fork pooled (A1 + A1-free) 39/40 vs stateless pooled (B2 + B3) 22/40: p = 4e-6; vs none: p = 0.001.

Cost: a fork variant is the cheapest or second cheapest in every task; on `long` it uses a third of the input of
no compaction and two thirds of B3 (stateless loops when it loses track of progress: up to 79 calls).

Conclusion (scoped): on these four synthetic tasks with one model, compacting with the agent's own context is
significantly better than no compaction and than free-text external summaries, and at least as good as the
best structured external summary (borderline significance) while cheaper. The schema does not matter for the
fork. Not yet shown: other models, reasoning on (needs 1b), real tool-heavy/coding tasks, larger n vs B3.

## 16. Native (provider) compaction as a competitor (2026-11-01)

Two OpenAI compaction paths, both through Pydantic AI's `OpenAICompaction`, trigger at the same 18K estimate:
- `native` — stateful server-side compaction (`context_management` / `compact_threshold` on the normal
  `/responses` request). **Works on the Codex backend**: inline `compaction` items appear in responses.
- `native-compact` — stateless `/responses/compact` (Codex CLI's remote compaction endpoint for OpenAI):
  **404 on the Codex subscription backend** for gpt-6-luna (`{'detail': 'Not Found'}`), so not testable here.

**Kedi bug found:** `> history: compaction_mode: native` fails with "native compaction for Pydantic AI requires
OpenAIResponsesModel or AnthropicModel" whenever a run budget is active, because `run_config.py` checks
`effective_model(...)`, which under a budget is Kedi's own `BudgetedModel` wrapper (`budget.py`), not the
provider model. The Codex model *is* an `OpenAIResponsesModel`. Fix: unwrap `WrapperModel` before the
isinstance check (and test with a budget active). The benchmark attaches the identical capability through
`PydanticAdapter(capabilities=[OpenAICompaction(token_threshold=…)])` instead.
