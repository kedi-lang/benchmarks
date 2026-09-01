#!/usr/bin/env bash
set -euo pipefail

EXPERIMENT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_ROOT="${KEDI_BENCH_WORKDIR:-$EXPERIMENT_ROOT/.work}"
KEDI_ROOT="$WORK_ROOT/kedi"
CAPTURE_ROOT="$WORK_ROOT/kedi-autobench"
KEDI_REV="e61ba24224fbf96f29a502f9e27d663659025872"
CAPTURE_REV="055bc6a78f4285ec5fdf077896f4920c4a24d84e"

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

uv sync \
  --project "$KEDI_ROOT" \
  --locked \
  --no-dev \
  --extra terminal-bench \
  --python 3.12
uv sync --project "$CAPTURE_ROOT" --locked --all-extras --python 3.11

printf 'Harbor runtime: %s\n' "$KEDI_ROOT/.venv/bin/kedi-terminal-bench"
printf 'Autobench capture: %s\n' \
  "$CAPTURE_ROOT/.venv/bin/kedi-autobench-terminal-bench"
