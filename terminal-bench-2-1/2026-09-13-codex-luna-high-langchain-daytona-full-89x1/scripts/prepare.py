"""Publish an offline, sanitized derivative; never modify source evidence."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import statistics
import tarfile
import tempfile
from datetime import datetime
from decimal import Decimal
from importlib.metadata import version
from pathlib import Path, PurePosixPath

import genai_prices


ROOT = Path(__file__).resolve().parents[1]
PREVIOUS = ROOT.parent / "2026-09-12-codex-luna-high-daytona-full-89x1"
spec = importlib.util.spec_from_file_location(
    "publication_sanitizer", PREVIOUS / "scripts/prepare_publication.py"
)
sanitization = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sanitization)
sanitization.TOKEN_PATTERNS += (
    re.compile(rb"\bhf_[A-Za-z0-9]{20,}\b"),
    re.compile(rb"\bAIza[A-Za-z0-9_-]{30,}\b"),
)
sanitization.SECRET_KEY = re.compile(
    sanitization.SECRET_KEY.pattern + r"|(?:^|[_-])token(?:$|[_-])", re.I
)


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True, default=str) + "\n")


def elapsed(start, end):
    return (datetime.fromisoformat(end) - datetime.fromisoformat(start)).total_seconds()


def prepare(source, dotenv):
    archive = source / "daytona-evidence.tar.gz"
    evidence = ROOT / "evidence"
    if evidence.exists():
        raise FileExistsError(evidence)
    sanitizer = sanitization.Sanitizer(source, dotenv)
    omitted = []
    source_hashes = {}
    with tempfile.TemporaryDirectory() as temporary, tarfile.open(archive) as tar:
        for member in tar:
            relative = PurePosixPath(member.name)
            if not relative.parts or relative.parts[0] != "jobs":
                continue
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError("Unsafe archive member")
            if member.isdir():
                continue
            if not member.isfile():
                omitted.append({"path": str(relative), "reason": "non-regular file"})
                continue
            raw = Path(temporary) / relative.name
            payload = tar.extractfile(member).read()
            import hashlib

            digest = hashlib.sha256(payload).hexdigest()
            source_hashes[str(relative)] = digest
            if not sanitization.looks_like_text(payload):
                omitted.append({"path": str(relative), "reason": "binary payload",
                                "bytes": len(payload), "sha256": digest})
                continue
            raw.write_bytes(payload)
            target = evidence / "harbor" / Path(*relative.parts[1:])
            if sanitizer.copy_file(raw, target, display_path=str(relative)):
                text = target.read_text()
                if target.suffix == ".jsonl":
                    text = "\n".join(json.dumps(sanitizer.json_value(json.loads(line)))
                                     for line in text.splitlines() if line.strip()) + "\n"
                text = re.sub(r"/" + r"Users/[^/\s\"']+", "<HOME>", text)
                target.write_text(text)
            raw.unlink()

    for name in (*sanitization.MANIFEST_FILES, "runtime-constraints.txt", "controller-constraints.txt"):
        sanitizer.copy_file(source / name, ROOT / "manifests" / name, display_path=name)
    batches = {"standard81-c2": "daytona-luna-high-full89-c2-c1-langchain-20260913-standard81-c2",
               "high-memory8-c1": "daytona-luna-high-full89-c2-c1-langchain-20260913-high-memory8-c1"}
    trials = []
    for batch, job in batches.items():
        for result in sorted((evidence / "harbor" / job).glob("*/result.json")):
            trials.append(sanitization.trial_entry(batch, result.parent))
    assert len(trials) == len({x['task_name'] for x in trials}) == 89
    write_json(evidence / "index.json", {"schema_version": 1, "batches": batches,
               "experiment_id": "daytona-luna-high-full89-c2-c1-langchain-20260913", "trials": trials})
    write_json(evidence / "sanitization-report.json", {
        "archive_sha256": sanitization.sha256(archive), "source_file_sha256": source_hashes,
        "redactions": sanitizer.replacement_count, "omitted_binary_or_special": omitted,
        "omitted_sensitive": sanitizer.skipped_sensitive_files,
        "omitted_oversized": sanitizer.skipped_oversized_files,
        "source_unchanged": True,
    })


def metrics():
    index = json.loads((ROOT / "evidence/index.json").read_text())
    rows = []
    pricing = None
    max_input = 0
    for entry in index['trials']:
        trial = ROOT / "evidence/harbor" / index['batches'][entry['batch']] / entry['trial_id']
        kedi = json.loads((trial / "agent/kedi-result.json").read_text())
        requests = [json.loads(line) for line in (trial / 'agent/model-requests.jsonl').read_text().splitlines() if line.strip()]
        completed = [x for x in requests if x.get('event') == 'model_request_completed']
        cost = Decimal(0)
        sums = {key: 0 for key in ('input_tokens', 'cache_read_tokens', 'output_tokens')}
        prices = []
        for request in completed:
            usage = request['response']['usage']
            for key in sums:
                sums[key] += usage.get(key) or 0
            max_input = max(max_input, usage['input_tokens'])
            timestamp = datetime.fromisoformat(request['recorded_at'].replace('Z', '+00:00'))
            price = genai_prices.calc_price(genai_prices.Usage(**{key: usage.get(key) or 0 for key in
                ('input_tokens', 'output_tokens', 'cache_read_tokens', 'cache_write_tokens')}),
                model_ref='gpt-5.6-luna', provider_id='openai', genai_request_timestamp=timestamp)
            cost += price.total_price
            pricing = price.model_price
            prices.append({'sequence': request['sequence'], 'cost_usd': str(price.total_price)})
        for key in sums:
            assert sums[key] == kedi['usage'][key], (entry['task_name'], key, sums[key], kedi['usage'][key])
        assert len(completed) == kedi['usage']['requests']
        row = {**entry, **kedi['usage'], 'cost_usd': str(cost), 'request_prices': prices,
               'duration_seconds': elapsed(entry['started_at'], entry['finished_at'])}
        rows.append(row)
    totals = {key: sum(row[key] for row in rows) for key in
              ('input_tokens','cache_read_tokens','output_tokens','requests','tool_calls')}
    totals['cost_usd'] = str(sum(Decimal(row['cost_usd']) for row in rows))
    totals['passed'] = sum(row['reward'] == 1 for row in rows)
    totals['failed'] = sum(row['reward'] == 0 for row in rows)
    totals['unscored'] = sum(row['reward'] is None for row in rows)
    totals['trials'] = len(rows)
    totals['max_request_input_tokens'] = max_input
    totals['cache_read_ratio'] = totals['cache_read_tokens'] / totals['input_tokens']
    totals['elapsed_seconds'] = elapsed(min(row['started_at'] for row in rows), max(row['finished_at'] for row in rows))
    for key in ('duration_seconds','input_tokens','output_tokens','requests','tool_calls','cost_usd'):
        values = sorted(float(row[key]) for row in rows)
        totals[key + '_distribution'] = {'mean': statistics.mean(values), 'median': statistics.median(values),
                                        'p95': statistics.quantiles(values, n=100, method='inclusive')[94], 'max': max(values)}
    write_json(ROOT / 'evidence/metrics.json', {'totals': totals, 'tasks': rows})
    write_json(ROOT / 'evidence/pricing.json', {
        'library': 'genai-prices', 'version': version('genai-prices'), 'provider': 'openai',
        'model': 'gpt-5.6-luna', 'rates': vars(pricing),
        'method': 'Sum calc_price per completed request at recorded timestamp; input includes cached tokens.',
        'provider_billed_cost': False, 'original_cost_fields': 'unchanged (null)',
    })
    print(json.dumps(totals, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', type=Path)
    parser.add_argument('--dotenv', type=Path)
    args = parser.parse_args()
    if args.source:
        prepare(args.source.resolve(), args.dotenv)
    metrics()
