# Pre-registration — phase 10 (written and committed before any phase-10 test run)

## H7 — the fork against a stateless summary on a second model family

On `long` (20 logs, UPDATE / RETRACT / mid-task POLICY CHANGE), with `deepseek/deepseek-v4.1-flash`
(through OpenRouter, Chat Completions, effort medium), the agent-side fork **A1-free** passes more often
than the stateless structured summary **B3**. Seeds **401–415** (new). Threshold 18K, same harness and
grading as phase 9 (`run.py` at the commit of this file).

- **Primary:** A1-free vs B3, strict pass, exact paired McNemar, one-sided, α = 0.05. A single primary, so
  no multiplicity correction.
- **Secondary (descriptive):** **none** (no compaction) on the same seeds, as a reference. It shows whether
  compacting at all costs accuracy on a model with a 1M-token context. Also reported: policy violations,
  missing / retracted incidents, compactions, cost.
- **Not tested:** native (provider) compaction. Kedi offers it only for OpenAI Responses and Anthropic,
  so the phase 6 / 9 claim against native is not tested on this model.

## Pilot, disclosed

`records/pilot_deepseek/` holds the runs made before this file, on pilot seeds 301–303, which are never test seeds:
- override: A1-free 2/2, none 2/2; the model applies the in-log change, unlike `gpt-6.1-terra` in H5.
- long, seed 303: A1-free and none both pass.

Because none also passes, the primary compares the fork with a stateless summary instead of with none.
The pilot informed only the choice of comparison and task, not the seeds, grading or analysis.

## Infra and budget rule

As before, a rate limit, timeout, connection error or 5xx gets one rerun with the same seed. Failures that
remain after that are reported as missing. Request-limit and budget failures inside a run count against
the strategy.

The run budget is the OpenRouter credit (about $4.9 at registration). Seeds run in ascending order, with
the three strategies of a seed together, and launching stops when the credit is exhausted. Seeds not run
for that reason are reported as missing, and the analysis uses the completed pairs.
