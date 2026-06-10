#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

run_label="${RUN_LABEL:-locom-ms-followup-$(date +%Y%m%d-%H%M%S)}"
output_dir="${OUTPUT_DIR:-.opencode/locom_ms_followup}"
train_steps="${TRACK3_TRAIN_STEPS:-500}"
cooldown_frac="${TRACK3_COOLDOWN_FRAC:-0.7}"
prepare_data_chunks="${PREPARE_DATA_CHUNKS:-3}"
rows_json_file="${LOCOM_ROWS_JSON_FILE:-tools/locom_ms_source_gate_rows.json}"

python3 tools/run_locom_clean_matrix.py \
  --preset ms \
  --rows-json-file "$rows_json_file" \
  --run-label "$run_label" \
  --output-dir "$output_dir" \
  --train-steps "$train_steps" \
  --cooldown-frac "$cooldown_frac" \
  --prepare-data-chunks "$prepare_data_chunks"
