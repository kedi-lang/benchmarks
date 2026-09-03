# Terminal-Bench 2.1 Experiments

Each directory below is a self-contained Kedi experiment with its environment,
immutable manifests, Harbor evidence, Autobench records, and validation tools.

- [2026-09-03 Codex Luna high Daytona standard-task run (19 tasks)](2026-09-03-codex-luna-high-daytona-standard-19/README.md)
  - Harbor-scored reward: **11/18 (61.1%)**; one additional trial was unscored after a Daytona connection reset
  - Provider usage is available for 14 trials; the **$4.37852572** recorded cost is intentionally reported as incomplete
  - Host sleep contaminated latency and four infrastructure/capture outcomes; task-level evidence remains published
- [2026-09-01 Codex Luna high single-revision run (9 tasks)](2026-09-01-codex-luna-high-single-revision-9/README.md)
  - Official reward: **8/9 (88.9%)**
  - Provider-reported cost: **$0.41832972 total**, **$0.04648108 per task**
  - Includes a checked-in Autobench audit report and documented offline replay
- [2026-09-01 Codex Luna high lifecycle validation (3 tasks)](2026-09-01-codex-luna-high-lifecycle-rerun-3/README.md)
  - Official reward: **2/3 (66.7%)**
  - Provider-reported cost: **$0.18051228 total**, **$0.06017076 per task**
  - Targeted rerun of the three failures from the initial pilot
- [2026-08-31 Codex Luna high Docker pilot (9 tasks)](2026-08-31-codex-luna-high-docker-pilot-9/README.md)
  - Official reward: **6/9 (66.7%)**
  - Provider-reported cost: **$0.32662052 total**, **$0.03629117 per task**
  - Status: harness dogfood evidence; not an official leaderboard submission
