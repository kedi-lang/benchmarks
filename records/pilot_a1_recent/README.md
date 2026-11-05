# Pilot — A1-recent (2026-11-05, not pre-registered)

Purpose: before pre-registering a test of `A1-recent` (the fork returns how many of the latest groups stay
verbatim, instead of naming them) against `A1-free`, check that the fork returns a valid count and look for
a ceiling. Seeds 501–503 are reserved for this pilot and will not be test seeds.

Setup: `gpt-6-luna`, effort medium, threshold 18K, tasks `override` and `long`, both arms on every seed.
Harness 20b52f3, Kedi 3b90c18 (workspace, editable). Launched as four streams, one per records file.

| task | strategy | strict passes | compactions | fallbacks | median input incl. fork |
|---|---|---|---|---|---|
| override | A1-recent | 3/3 | 12 | 1 | 169K |
| override | A1-free | 3/3 | 11 | 0 | 159K |
| long | A1-recent | 3/3 | 36 | 1 | 415K |
| long | A1-free | 3/3 | 37 | 1 | 429K |

Readings:
- The count was valid in every compaction whose reply parsed. The two fallbacks are JSON parse errors
  (text after the JSON object; an empty reply), the same path `A1-free` uses; earlier `A1-free` runs fell back
  in 53 of 1279 compactions.
- The fork chose `keep_recent` = 0 in 34 of 46 parsed compactions, 1 in 9, and 2, 3 and 4 once each, the 4 in
  the first override compaction of seed 501. Given a count, it mostly keeps no raw exchange beyond the ones the
  runtime keeps anyway (the task prompt, earlier summaries, the current exchange).
- `A1-free`'s kept counts follow the same pattern, rising by one per compaction as summaries accumulate,
  so it too mostly keeps nothing extra; the records count kept groups, not their ids, so this is a reading,
  not a measurement.
- Both arms passed every run. With `A1-free` at 26/30 (held-out) and 15/15 (`long`) in the tests, and the
  two arms choosing alike, a paired test on these tasks would likely sit at a ceiling.
