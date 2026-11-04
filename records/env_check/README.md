# Environment checks (2026-11-04, not part of any phase)

Runs made to check the reproduction environment in `README.md`. Each ran in a fresh venv with Kedi installed
from git at `833ce44` and every package at the version the runs used (then pinned by `constraints.txt`, now
by `uv.lock`). No summary or test reads this folder.

| file | harness layout (commit) | run | result |
|---|---|---|---|
| `override_t18k_native.jsonl` | files at the top level (`e17ec87`) | `native`, `override`, seed 101, `gpt-6-luna` | strict pass, 2 provider compactions, 10 requests, 47 s |
| `override_t18k_A1-free.jsonl` | `agent_compaction/` package (`29fa071`), from a clean clone following `README.md` | `A1-free`, `override`, seed 101, `gpt-6-luna` | strict pass, 3 fork compactions, 10 requests, 46 s |
