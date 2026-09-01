#!/usr/bin/env bash
set -euo pipefail

EXPERIMENT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_ROOT="${KEDI_BENCH_WORKDIR:-$EXPERIMENT_ROOT/.work}"
KEDI_ROOT="$WORK_ROOT/kedi"
TASK_FILE="$EXPERIMENT_ROOT/environment/tasks.txt"
DIST_DIR="$WORK_ROOT/dist"
MANIFEST_DIR="$WORK_ROOT/manifests"
MANIFEST_PATH="${1:-$MANIFEST_DIR/single-revision-9.json}"
HARBOR_REV="41a50d62d7f35677cc34ba3a0c36f042a4fef68c"

if [[ ! -x "$KEDI_ROOT/.venv/bin/kedi-terminal-bench" ]]; then
  printf 'runtime missing; run environment/setup.sh first\n' >&2
  exit 69
fi

mkdir -p "$DIST_DIR" "$MANIFEST_DIR" "$(dirname "$MANIFEST_PATH")"
uv build --project "$KEDI_ROOT" --wheel --out-dir "$DIST_DIR"

shopt -s nullglob
wheels=("$DIST_DIR"/kedi-*.whl)
if [[ ${#wheels[@]} -ne 1 ]]; then
  printf 'expected one Kedi wheel in %s, found %s\n' "$DIST_DIR" "${#wheels[@]}" >&2
  exit 70
fi

command=(
  "$KEDI_ROOT/.venv/bin/kedi-terminal-bench" manifest
  --output "$MANIFEST_PATH"
  --harbor-revision "$HARBOR_REV"
  --model codex/gpt-5.6-luna
  --kedi-wheel "${wheels[0]}"
  --kedi-root "$KEDI_ROOT"
  --environment docker
  --adapter pydantic
  --effort high
  --concurrency 2
  --attempts 1
  --agent-setup-timeout-multiplier 3
  --max-retries 1
  --retry-include NonZeroAgentExitCodeError
  --retained-process-timeout-seconds 3600
)
while IFS= read -r task; do
  [[ -n "$task" ]] && command+=(--task "$task")
done < "$TASK_FILE"

"${command[@]}"
printf 'Kedi wheel: %s\n' "${wheels[0]}"
