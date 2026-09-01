#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 3 ]]; then
  printf 'usage: %s MANIFEST JOB_NAME KEDI_WHEEL\n' "$0" >&2
  exit 64
fi

EXPERIMENT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WORK_ROOT="${KEDI_BENCH_WORKDIR:-$EXPERIMENT_ROOT/.work}"
KEDI_ROOT="$WORK_ROOT/kedi"
CAPTURE_ROOT="$WORK_ROOT/kedi-autobench"
MANIFEST="$1"
JOB_NAME="$2"
KEDI_WHEEL="$3"
JOBS_DIR="$EXPERIMENT_ROOT/jobs"
RECORDS_DIR="$EXPERIMENT_ROOT/records"
JOB_DIR="$JOBS_DIR/$JOB_NAME"
RECORD_DIR="$RECORDS_DIR/$JOB_NAME"
KEDI_TB="$KEDI_ROOT/.venv/bin/kedi-terminal-bench"
HARBOR="$KEDI_ROOT/.venv/bin/harbor"
CAPTURE="$CAPTURE_ROOT/.venv/bin/kedi-autobench-terminal-bench"

for executable in "$KEDI_TB" "$HARBOR" "$CAPTURE"; do
  if [[ ! -x "$executable" ]]; then
    printf 'runtime missing: %s; run environment/setup.sh first\n' "$executable" >&2
    exit 69
  fi
done
for file in "$MANIFEST" "$KEDI_WHEEL"; do
  if [[ ! -f "$file" ]]; then
    printf 'required file missing: %s\n' "$file" >&2
    exit 66
  fi
done
if [[ -e "$JOB_DIR" || -e "$RECORD_DIR" ]]; then
  printf 'job or record already exists for %s\n' "$JOB_NAME" >&2
  exit 73
fi

mkdir -p "$JOBS_DIR" "$RECORDS_DIR"
export KEDI_HARBOR_LOGFIRE=1
exec "$CAPTURE" run \
  --job-dir "$JOB_DIR" \
  --record-dir "$RECORD_DIR" \
  -- \
  "$KEDI_TB" run "$MANIFEST" \
  --harbor-command "$HARBOR" \
  --jobs-dir "$JOBS_DIR" \
  --job-name "$JOB_NAME" \
  --kedi-wheel "$KEDI_WHEEL"
