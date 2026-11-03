# Pilot — DeepSeek V4.1 Flash (2026-11-03, not pre-registered)

Purpose: before pre-registering a second-model test, check that the model applies an instruction change
delivered in tool output. `gpt-6.1-terra` declined such changes, so phase 9 H5 could not separate the
strategies (see `FINDINGS.md`). Pilot seeds 301–302 are reserved for this pilot and will not be test seeds.

Setup: `openrouter:deepseek/deepseek-v4.1-flash`, effort medium, task `override`, threshold 18K, through
`run.py`'s OpenAI-compatible model (Chat Completions, same base instruction as the Codex models). Native
compaction is not available on this model.

Result: 4/4 strict passes (A1-free 2/2, none 2/2). The change was applied in every run, and the probe
names it as in force. Without compaction the model also passes, so the short `override` task may sit near
a ceiling for this model. A test should use the longer `long` task. Cost: about $0.11 for the 4 runs.

## Vercel AI Gateway attempt (2026-11-03)

`long_t18k_A1-free.jsonl` and `long_t18k_none.jsonl`, seed 303: the gateway refused the model before any
token was spent (`403 RestrictedModelsError`: free-tier credits have no access to `deepseek-v4.1-flash`;
of the DeepSeek models tried, only `deepseek-v3.1` is open on the free tier). `run.py` gained the
`vercel:<id>` prefix for this.
