#!/usr/bin/env bash
set -euo pipefail

RUN_LABEL="${RUN_LABEL:-prime-a100sxm-locom-coldpulse-$(date +%Y%m%d-%H%M%S)}"
OUTPUT_DIR="${OUTPUT_DIR:-/home/ubuntu/track3_softmerge_logs}"
CHECKPOINT_DIR="${CHECKPOINT_DIR:-/home/ubuntu/track3_softmerge_checkpoints}"
CHECKPOINT_PREFIX="${CHECKPOINT_PREFIX:-prime_a100sxm_locom_coldpulse}"

python3 tools/run_locom_clean_matrix.py \
  --preset ms \
  --rows-json-file tools/locom_softmerge_coldpulse_rows.json \
  --run-label "${RUN_LABEL}" \
  --output-dir "${OUTPUT_DIR}" \
  --train-steps 3000 \
  --schedule-steps 3000 \
  --stop-step 3000 \
  --cooldown-frac 0.7 \
  --log-steps "2000,2125,2250,2375,2400,2500,2625,2750,2875,2900,2925,2950,2975,3000" \
  --seed 0 \
  --checkpoint-steps "${CHECKPOINT_STEPS:-2400,3000}" \
  --checkpoint-dir "${CHECKPOINT_DIR}" \
  --checkpoint-prefix "${CHECKPOINT_PREFIX}" \
  --prepare-data-chunks 0
