#!/usr/bin/env bash
set -euo pipefail

EXPERIMENT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
VENV_PATH="${KEDI_BENCH_REPLAY_VENV:-$EXPERIMENT_ROOT/.venv-replay}"
AUTOBENCH_REV="415c2e6100e85b5671f9f045ca6dc4e4c78f081c"
KEDI_AUTOBENCH_REV="6d054c0ab5127267bdd297efd3c41dceb7d974c2"

uv venv --python 3.11 "$VENV_PATH"
uv pip install --python "$VENV_PATH/bin/python" \
  "git+https://github.com/vcoderun/autobench.git@$AUTOBENCH_REV" \
  "git+https://github.com/kedi-lang/kedi-autobench.git@$KEDI_AUTOBENCH_REV"

printf 'Replay environment: %s\n' "$VENV_PATH"
printf 'Validate with: %s scripts/validate_publication.py\n' "$VENV_PATH/bin/python"
