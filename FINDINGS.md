# Findings — who should manage an agent's context?

Native compaction, agent forks, resets and policy changes in Kedi. Status 2026-11-02, phases 1–9 (phase 9 partly; see below).
`REPORT.md` (phases 1–5, the exploratory story) is preserved unchanged in substance; this file follows the
research brief's reporting format and covers everything, with phases 6–8 as the main evidence. Tables:
`results/RESULTS.md` (phases 2–5) and `results/PHASES_6_8.md` (phases 6–8), both generated from `records/`.

## 1. Executive result (qualified)

One model (`gpt-6-luna`, effort medium, Codex subscription backend), synthetic log-audit tasks, compaction
triggered at an 18K-token estimate (the model never chooses *when*). Outcome unit: one task/seed run, strict
grading. Primary statistic: exact paired McNemar.

- **Pre-registered held-out test (phase 6):** when an instruction changes after the first compaction, the
  agent-side fork (A1-free) passed 26/30 vs provider compaction (native) 19/30 on `override` + `format`:
  9 vs 2 discordant pairs, one-sided p = 0.033 (two-sided 0.065). The third pre-registered task (`scope`) was
  lost to provider rate limits; its later supplement points the same way (13/15 vs 11/15, not significant).
- **Mechanism, not loss:** every failed native run named the changed instruction correctly when asked
  afterwards (11/11 pre-registered, 4/4 supplement). Native compaction keeps the instruction; the model then
  does not apply it. "Native deletes the policy" is **not** supported.
- **Short tasks: simple methods suffice.** On `rev` (8 logs, 14 seeds) a deterministic runtime checkpoint
  ("reset on policy") passed 13/14 at the lowest cost (84K median input); A1-free 12/14, native+reassert 12/14,
  native 11/14, no compaction 12/14. No meaningful differences.
- **Long horizon, confirmed (phase 9, pre-registered, new seeds 201–215):** A1-free 15/15 vs native 8/15 on
  `long`, 7 vs 0 discordant pairs, one-sided p = 0.0078 (two-sided 0.016), below the Holm threshold for
  phase 9's three hypotheses. Native's failures were again policy violations (13).
- **Long tasks (exploratory phases 7–8): the fork is the most robust.** On `long` (20 logs, 15 seeds): A1-free 12/15,
  native+reassert 9/14, native 8/15, no compaction 6/15, deterministic reset 4/15. A1-free vs reset p = 0.011,
  vs no compaction p = 0.035, vs native p = 0.14, vs native+reassert p = 0.25 (2 vs 0).
- **Restating the policy fixes most of native's violations** (11 → 4 on `long`, 8 → 0 on `rev`) at no extra
  cost, but on `long` it does not lift native's accuracy to the fork's.
- **Cost:** native is the cheapest compactor (~30–40% less input than A1-free); the deterministic reset is
  cheapest on short tasks and among the most expensive on long ones (it loops).

## 2. Protocol and implementation

- Experiment repo: this folder (own git history). Kedi `stable` at `22931a1`; relevant Kedi changes:
  `9374d1f` (Pydantic AI 2.64), `dafe680` (running tool loops trimmable), `8c6e7e8` + `22931a1` (native
  compaction under an active run budget, with a regression test on the adapter path sessions use).
- Model and settings: `environment.json`. Pydantic AI 2.64, codex-auth-helper 1.10.1, `store=false`,
  `parallel_tool_calls=false`, per-run `prompt_cache_key`.
- Native: OpenAI server-side compaction (`context_management`) through Kedi's `> history: compaction_mode:
  native` (phases 6–8; phase 5 attached the identical capability directly, before the Kedi fix).
  `/responses/compact` returns 404 on this backend; not tested.
- Instruction changes are delivered inside tool output (log lines), not at a privileged authority level.
  This is a property of the task family and a limitation (§6).
- "Reset" = same-session replacement through a Kedi history processor: protected prompt + runtime checkpoint
  + current exchange. Not a fresh provider conversation. Native + reset is **not implementable** in Kedi
  today: the opaque native compaction item is a protected checkpoint the processor may not remove.
- Held-out set: `PREREGISTRATION.md` (committed `8217739` before any phase-6 run); harness committed
  `b17e3a0` before results were read. Seeds 101–115.
- Infra rule: rate-limit / timeout failures rerun once with the same seed; failures remaining after that are
  reported as missing. Request-limit and budget failures count against the strategy.

## 3. Raw-results index

`records/<phase>/<task>_t18k_<strategy>.jsonl`, one JSON line per attempt (answer, grade, usage incl.
compaction calls, every compaction event, probe). Phases: `phase2_task1_baselines`, `phase3_task1_ablation`,
`phase4_edge_cases`, `phase5_native`, `phase6_heldout` (includes the rate-limited first attempts),
`phase6b_scope_supplement`, `phase7_reset_reassert`, `phase8_more_seeds`.

## 4. Main tables

See `results/PHASES_6_8.md` (pass, infra-missing, policy violations, change applied, median total input incl.
compaction calls, median output incl. compaction output, median calls incl. fork calls) and
`results/RESULTS.md` for phases 2–5.

## 5. Paired comparisons (A1-free vs …; exact McNemar)

| set | vs native | vs native+reassert | vs reset-det | vs B3 | vs none |
|---|---|---|---|---|---|
| phase 6 held-out k=5 (30 pairs) | 9–2, p=0.033 | – | – | 15–2, p=0.001 | 15–1, p=0.0003 |
| phase 6 control k=2 (45) | 10–4, p=0.090 | – | – | 15–2, p=0.001 | 19–2, p=0.0001 |
| phases 7+8 rev+long (28–29) | 9–4, p=0.133 | 3–1, p=0.31 | 10–3, p=0.046 | – | 8–2, p=0.055 |
| phases 7+8 long (14–15) | 6–2, p=0.14 | 2–0, p=0.25 | 9–1, p=0.011 | – | 7–1, p=0.035 |
| **phase 9 H4 long, new seeds (15)** | **7–0, p=0.0078** | 0–0 (4 pairs) | – | – | – |

Confirmatory (pre-registered): phase 6 k=5 vs native and phase 9 H4 vs native. Everything else is exploratory;
many comparisons were made, so treat p ≈ 0.03–0.06 values outside phase 6 as suggestive, not as findings.

## 6. Mechanism

Observed:
- Native's failures are instruction-application failures with the instruction still recallable (15/15
  probes across phases 6 and 6b). Restating the instruction right before the current exchange removes most
  violations.
- Without compaction, failed runs could not even name the change (0/27 probes), consistent with attention
  loss in a long context rather than a compaction effect.
- A deterministic checkpoint of raw evidence lines plus progress is enough for 8 logs and breaks down over
  20 (wrong owner after many resets, early stop, request limit): carrying facts is not the same as carrying a
  usable working state.
- The fork writes an exact next step and folds updates/retractions into its summary; resetting it on every
  policy change (reset-fork) did not help.

Hypotheses, not established:
- The fork's advantage on long tasks comes from re-expressing state (latest values, superseded facts,
  progress) rather than listing evidence. Not isolated: the pending/progress ablations (brief P2) were not run.
- Recency explains most of native's policy problem; it does not explain the long-task accuracy gap.

Confounders: instructions arrive in tool output; one model; synthetic tasks with unambiguous evidence lines;
summary blocks accumulate as protected messages for all processor strategies.

## 7. Falsifying cases (where A1-free was not better)

- `rev` (14 seeds): reset-det 13/14 beats A1-free 12/14 at about half the input; native+reassert ties it at
  two thirds of the input.
- `format-early` control: native 11/15 vs A1-free 10/15.
- Phase-6 k=5: native won 2 pairs; long: native 2, reset-det 1, none 1 pairs.
- A1-free is never the cheapest: 30–60% more input than native on every task, and more calls (one fork call
  per compaction).
- Fallbacks: malformed fork JSON occurred and fell back to truncation (recorded per event as `fallback`).

## 8. Decision matrix (from these tasks only)

| situation | choose | why |
|---|---|---|
| short sessions, few compactions | deterministic checkpoint or native | as accurate, cheapest |
| instructions change mid-session, cost matters | native + restated instructions | removes most violations at native cost |
| long sessions with evolving state | agent fork (A1-free) | most robust; costs more |
| no compaction | not recommended past ~50K | slower, expensive, worse instruction following |
A hybrid (native + restatement, fork only on long horizons) is a proposal, not tested.

## 8b. Cache claims withdrawn

Phase 1's cache probe was only written down as notes. Its rerun with raw records
(`records/phase1_cache_probe/`) did not reproduce it (fork cache hit 2/6, not 5/6; output-tool fork hit 1/6,
not 0/6). No cache claim is made; accuracy and token results do not depend on caching.

## 9. Kedi issues and patches

- Fixed: history processors could not trim a running tool loop (`dafe680`).
- Fixed: `compaction_mode: native` failed whenever a run budget was active (`8c6e7e8`, test `22931a1`).
- Found, not fixed in Kedi: codex-auth-helper passes Pydantic AI a ready-made client that is never refreshed,
  so dependent templates on a new event loop fail with "Event loop is closed"; worked around by
  `loop_guard.py`. Fix belongs in codex-auth-helper (client factory) or a single session loop in Kedi.
- Open: signed-reasoning entries cannot be removed (1b); typed-output turns never close (2); summary blocks
  accumulate as protected prompts and user processors cannot emit replaceable checkpoints (4); the native
  compaction item cannot be dropped by a processor (blocks native + reset).

## 10. Blog-ready claims

1. In a pre-registered test, letting the agent compact its own context made it follow instructions that
   changed mid-task more reliably than OpenAI's native compaction (26/30 vs 19/30, paired p = 0.03), at
   ~35% higher input cost.
2. Native compaction did not forget those instructions — the model could still state them — it failed to
   apply them; restating the instruction fixes most of that cheaply.
3. On short tasks a simple runtime checkpoint is as good and cheaper; the agent-managed approach pays off on
   long, state-changing sessions.

Limitations to state with them: one model and backend, synthetic tasks, instructions delivered through tool
output, reasoning off, n = 14–30 per comparison.

Suggested title: **Who Should Manage an Agent's Context? Native Compaction, Agent Forks, and Policy Changes
in Kedi.**

## Phase 9 status

`PREREGISTRATION_PHASE9.md` (committed `fb1d0e7` before any run). H4 complete (above). The subscription's
usage quota ran out during the run (`usage_limit_reached`): H4's secondary arm native+reassert has 4/15 runs
(4/4 pass), H5 (second model `gpt-6.1-terra`, effort low) has only 7 A1-free runs (1/7 pass) and no native runs,
H6 (fake instruction in tool output) has none. Per the pre-registration the missing runs are rerun once with
the same seeds when the quota resets; until then H5 and H6 are **not tested**.

## Not done (brief items), with commands

- P2 progress ablations (A1 without `pending`, B3 + runtime progress line) — strategies not implemented yet.
- Timing ablation (policy just before/after a compaction, or with no later compaction) — not run.
- Long-horizon 150K+ threshold sweep, second model, reasoning-on (needs 1b), real coding/research tasks,
  adversarial fake policy in tool output, replaceable checkpoint prototype — not run.
- Rerun any phase: `.venv/bin/python -m benchmarks.agent_compaction.run --strategy <s> --task <t> --seeds …`,
  then move records into a phase folder and run `summarize.py` / `summarize_6_8.py`.
