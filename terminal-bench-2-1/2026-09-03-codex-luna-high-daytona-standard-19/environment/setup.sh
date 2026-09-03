#!/usr/bin/env bash
set -euo pipefail

EXPERIMENT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_ROOT="${KEDI_BENCH_WORKDIR:-$EXPERIMENT_ROOT/.work}"
KEDI_ROOT="$WORK_ROOT/kedi"
CAPTURE_ROOT="$WORK_ROOT/kedi-autobench"
AUTOBENCH_ROOT="$WORK_ROOT/autobench"
KEDI_REV="aa0dee26824da60476dd1464412045ce4e82f15b"
CAPTURE_REV="6d054c0ab5127267bdd297efd3c41dceb7d974c2"
AUTOBENCH_REV="415c2e6100e85b5671f9f045ca6dc4e4c78f081c"

checkout() {
  local url="$1"
  local revision="$2"
  local destination="$3"

  if [[ ! -d "$destination/.git" ]]; then
    git clone --filter=blob:none "$url" "$destination"
  fi
  git -C "$destination" fetch --prune origin
  git -C "$destination" checkout --detach "$revision"
}

mkdir -p "$WORK_ROOT"
checkout "https://github.com/kedi-lang/kedi.git" "$KEDI_REV" "$KEDI_ROOT"
git -C "$KEDI_ROOT" submodule sync --recursive
git -C "$KEDI_ROOT" submodule update --init --recursive

checkout \
  "https://github.com/kedi-lang/kedi-autobench.git" \
  "$CAPTURE_REV" \
  "$CAPTURE_ROOT"
checkout \
  "https://github.com/vcoderun/autobench.git" \
  "$AUTOBENCH_REV" \
  "$AUTOBENCH_ROOT"

uv sync \
  --project "$KEDI_ROOT" \
  --locked \
  --no-dev \
  --extra terminal-bench \
  --python 3.12
uv sync --project "$CAPTURE_ROOT" --locked --all-extras --python 3.11
uv pip install \
  --python "$CAPTURE_ROOT/.venv/bin/python" \
  --reinstall \
  --no-deps \
  "$AUTOBENCH_ROOT"

printf 'Harbor runtime: %s\n' "$KEDI_ROOT/.venv/bin/kedi-terminal-bench"
printf 'Autobench capture: %s\n' \
  "$CAPTURE_ROOT/.venv/bin/kedi-autobench-terminal-bench"
printf 'Autobench CLI: %s\n' "$CAPTURE_ROOT/.venv/bin/autobench"
