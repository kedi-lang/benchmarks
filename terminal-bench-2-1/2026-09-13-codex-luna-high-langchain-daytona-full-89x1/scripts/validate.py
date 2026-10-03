"""Validate published evidence and the single offline Autobench record."""

import argparse
import importlib.util
import json
import re
from decimal import Decimal
from pathlib import Path

from autobench import replay_experiment

ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT.parent / '2026-09-12-codex-luna-high-daytona-full-89x1'
spec = importlib.util.spec_from_file_location('public_checks', PREVIOUS / 'scripts/validate_publication.py')
checks = importlib.util.module_from_spec(spec)
spec.loader.exec_module(checks)
checks.FORBIDDEN_PATTERNS += (
    re.compile(rb"\bhf_[A-Za-z0-9]{20,}\b"),
    re.compile(rb"\bAIza[A-Za-z0-9_-]{30,}\b"),
)


def validate(dotenv):
    metrics = json.loads((ROOT / 'evidence/metrics.json').read_text())
    index = json.loads((ROOT / 'evidence/index.json').read_text())
    totals = metrics['totals']
    assert (totals['trials'], totals['passed'], totals['failed'], totals['unscored']) == (89, 68, 20, 1)
    assert totals['cost_usd'] == '5.05064428'
    experiment = replay_experiment(ROOT / 'evidence/autobench/full89')
    assert len(experiment.runs) == 89
    trials = {row['trial_id']: row for row in metrics['tasks']}
    assert len(trials) == len({row['task_name'] for row in metrics['tasks']}) == 89
    assert set(trials) == {row['trial_id'] for row in index['trials']}
    seen = set()
    total_cost = Decimal(0)
    for run in experiment.runs:
        output = run.task_result.output
        name = output['trial_name']
        assert name not in seen
        seen.add(name)
        expected = trials[name]
        reward = checks.metric(run, 'terminal_bench.reward.reward')
        assert reward == expected['reward'], name
        assert Decimal(str(checks.metric(run, 'kedi.cost_usd'))) == Decimal(expected['cost_usd'])
        for field in ('input_tokens', 'cache_read_tokens', 'output_tokens', 'requests', 'tool_calls'):
            assert checks.metric(run, f'kedi.{field}') == expected[field]
        reference = output['evidence_reference']
        trial = ROOT / reference['trial_root']
        assert checks.digest(trial / 'result.json') == reference['result_sha256']
        assert checks.digest(trial / 'agent/kedi-result.json') == reference['kedi_result_sha256']
        total_cost += Decimal(expected['cost_usd'])
    assert seen == set(trials)
    assert total_cost == Decimal(totals['cost_usd'])
    declared = {line.split('  ',1)[1]: line.split('  ',1)[0]
                for line in (ROOT / 'checksums.sha256').read_text().splitlines()}
    actual = {p.relative_to(ROOT).as_posix(): p for p in ROOT.rglob('*')
              if p.is_file() and p.name != 'checksums.sha256' and '__pycache__' not in p.parts}
    assert set(declared) == set(actual), 'Checksum membership mismatch'
    secrets = checks.known_secrets(dotenv)
    for name, path in actual.items():
        assert not path.is_symlink(), name
        assert path.name.lower() not in checks.SENSITIVE_FILENAMES, name
        assert not path.name.lower().startswith('.env.'), name
        assert checks.digest(path) == declared[name], name
        data = path.read_bytes()
        assert len(data) <= 20_000_000, name
        assert not any(pattern.search(data) for pattern in checks.FORBIDDEN_PATTERNS), name
        assert not any(secret in data for secret in secrets), name
    print(f'PASS: {len(seen)} trials; 68 passed, 20 failed, 1 unscored; ${total_cost}; {len(actual)} files; replay, hashes, secrets checked.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--dotenv', type=Path)
    validate(parser.parse_args().dotenv)
