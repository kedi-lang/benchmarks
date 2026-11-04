# Environment check (2026-11-04, not part of any phase)

One run made to check the reproduction environment in `README.md`: a fresh venv with Kedi installed from git
at `833ce44` and every package at its `constraints.txt` version. `native` on `override`, seed 101, `gpt-6-luna`:
strict pass, 2 provider compactions, 10 requests, 47 s. No summary or test reads this folder.
