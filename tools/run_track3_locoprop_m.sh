#!/usr/bin/env bash
set -euo pipefail

steps="${TRACK3_TRAIN_STEPS:-${SCREEN_STEPS:-500}}"
trials="${TRACK3_NUM_TRIALS:-1}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"
generated_script="${TRACK3_GENERATED_SCRIPT:-/tmp/train_gpt_simple_locoprop_m_${steps}.py}"
nproc="${NPROC_PER_NODE:-1}"

python3 tools/make_track3_locoprop_m.py \
  --source "${source_script}" \
  --output "${generated_script}" \
  --steps "${steps}"

python3 -m py_compile "${generated_script}"

if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
  echo "generated ${generated_script}"
  exit 0
fi

torchrun --standalone --nproc_per_node="${nproc}" "${generated_script}" "${trials}"
