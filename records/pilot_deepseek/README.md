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
