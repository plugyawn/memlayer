#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

run_label="${RUN_LABEL:-locom-muonupdate-3000sched-stop1600-seed${TRACK3_SEED:-0}-$(date +%Y%m%d-%H%M%S)}"
output_dir="${OUTPUT_DIR:-.opencode/locom_muonupdate_1600}"
checkpoint_dir="${TRACK3_CHECKPOINT_DIR:-checkpoints/track3_locom}"
checkpoint_prefix="${TRACK3_CHECKPOINT_PREFIX:-$run_label}"
prepare_data_chunks="${PREPARE_DATA_CHUNKS:-9}"

python3 tools/run_locom_clean_matrix.py \
  --preset ms \
  --rows-json-file tools/locom_muonupdate_1600_rows.json \
  --run-label "$run_label" \
  --output-dir "$output_dir" \
  --train-steps 3000 \
  --schedule-steps 3000 \
  --stop-step 1600 \
  --cooldown-frac 0.7 \
  --log-steps "0,1,2,10,50,125,250,375,500,750,1000,1250,1500,1600" \
  --seed "${TRACK3_SEED:-0}" \
  --checkpoint-steps 1600 \
  --checkpoint-dir "$checkpoint_dir" \
  --checkpoint-prefix "$checkpoint_prefix" \
  --prepare-data-chunks "$prepare_data_chunks"
