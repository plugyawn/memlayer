#!/usr/bin/env bash
set -euo pipefail

MAX_ROWS="${MAX_ROWS:-2}"
RUN_LABEL="${RUN_LABEL:-prime-a100sxm-locom-softmerge-suffix-$(date +%Y%m%d-%H%M%S)}"
OUTPUT_DIR="${OUTPUT_DIR:-/home/ubuntu/track3_softmerge_logs}"
CHECKPOINT_DIR="${CHECKPOINT_DIR:-/home/ubuntu/track3_softmerge_checkpoints}"
CHECKPOINT_PREFIX="${CHECKPOINT_PREFIX:-prime_a100sxm_locom_softmerge}"

python3 tools/run_locom_clean_matrix.py \
  --preset ms \
  --rows-json-file tools/locom_softmerge_suffix_rows.json \
  --max-rows "${MAX_ROWS}" \
  --run-label "${RUN_LABEL}" \
  --output-dir "${OUTPUT_DIR}" \
  --train-steps 3000 \
  --schedule-steps 3000 \
  --stop-step 3000 \
  --cooldown-frac 0.7 \
  --log-steps "1600,1750,1875,2000,2125,2250,2375,2400,2500,2625,2750,2875,2900,2925,2950,2975,3000" \
  --seed 0 \
  --checkpoint-steps "${CHECKPOINT_STEPS:-2400,3000}" \
  --checkpoint-dir "${CHECKPOINT_DIR}" \
  --checkpoint-prefix "${CHECKPOINT_PREFIX}" \
  --prepare-data-chunks 0 \
  --continue-on-error
