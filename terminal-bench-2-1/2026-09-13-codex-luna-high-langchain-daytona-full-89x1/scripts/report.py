"""Render the report from published trial metrics, without model calls."""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
data = json.loads((ROOT / 'evidence/metrics.json').read_text())
total, tasks = data['totals'], data['tasks']
cost = float(total['cost_usd'])
lines = [
    '# LangChain Full89 Results', '',
    'One trial per task, 89 distinct Terminal-Bench 2.1 tasks. This is not best-of-N.', '',
    '| Metric | Value |', '|---|---:|',
    f'| Solved | {total["passed"]}/89 (76.40%) |',
    f'| Verifier reward 0 | {total["failed"]} |',
    f'| Unscored, verifier timeout | {total["unscored"]} |',
    f'| Estimated API-equivalent cost | ${cost:.8f} |',
    f'| Cost per task | {cost / 89 * 100:.4f} cents |',
    f'| Cost per solved task | {cost / total["passed"] * 100:.4f} cents |',
    f'| Token-weighted cache-read rate | {total["cache_read_ratio"] * 100:.4f}% |',
    f'| Input tokens (including cache) | {total["input_tokens"]:,} |',
    f'| Cache-read tokens | {total["cache_read_tokens"]:,} |',
    f'| Output tokens | {total["output_tokens"]:,} |',
    f'| Completed model requests | {total["requests"]:,} |',
    f'| Tool calls | {total["tool_calls"]:,} |',
    f'| First trial start to last trial finish | {total["elapsed_seconds"] / 3600:.3f} hours |',
    f'| Largest single request input | {total["max_request_input_tokens"]:,} tokens |', '',
    '## Interpretation', '',
    '`model-extraction-relu-logits` has no verifier reward: Harbor reports a '
    '`VerifierTimeoutError` after 900 seconds. It is not silently converted to a reward-zero '
    'trial. The full-sample success denominator remains 89. The six-hour agent timeout '
    'does not extend this separate verifier timeout.', '',
    'Prices are offline OpenAI API-equivalent estimates from `genai-prices`, not '
    'Codex subscription charges or an API invoice. Each completed request is priced '
    'individually at its recorded timestamp, preserving cached-token accounting and '
    'request-level pricing tiers. Original Harbor/Kedi cost fields remain unchanged. '
    'Request token totals and request counts match each task\'s captured usage.', '',
    'The Pydantic comparison run also solved 68/89, at a published estimate of '
    '$4.93781512 and 94.48% cache reads. LangChain is about 2.29% more expensive here. '
    'One sample per task does not establish adapter equivalence or explain causality; '
    'model sampling, transport, sandbox, and verifier timing can all affect outcomes.', '',
    '## Distributions', '',
    'Percentiles use linear interpolation (inclusive method). Duration includes the '
    'whole Harbor trial, not only model latency. Aggregate trial time is not wall time.', '',
    '| Metric | Mean | Median / p50 | p95 | Maximum |', '|---|---:|---:|---:|---:|',
]
for name, unit in [('duration_seconds', 'Duration (s)'), ('cost_usd', 'Cost (USD)'),
                   ('input_tokens','Input tokens'), ('output_tokens','Output tokens'),
                   ('requests','Model requests'), ('tool_calls','Tool calls')]:
    values = total[name + '_distribution']
    lines.append(f'| {unit} | ' + ' | '.join(f'{values[k]:,.5f}' for k in ('mean','median','p95','max')) + ' |')
lines.extend(['', '## Per-Task Evidence', '',
              '| Task | Reward | Cost (USD) | Duration (s) | Requests | Tool calls | Cache read |',
              '|---|---:|---:|---:|---:|---:|---:|'])
index = json.loads((ROOT / 'evidence/index.json').read_text())
for row in sorted(tasks, key=lambda x: x['task_name']):
    link = f'evidence/harbor/{index["batches"][row["batch"]]}/{row["trial_id"]}/result.json'
    reward = 'unscored' if row['reward'] is None else str(row['reward'])
    ratio = row['cache_read_tokens'] / row['input_tokens'] if row['input_tokens'] else 0
    lines.append(f'| [{row["task_name"]}]({link}) | {reward} | {float(row["cost_usd"]):.8f} | '
                 f'{row["duration_seconds"]:.2f} | {row["requests"]} | {row["tool_calls"]} | {ratio:.2%} |')
(ROOT / 'RESULTS.md').write_text('\n'.join(lines) + '\n')
