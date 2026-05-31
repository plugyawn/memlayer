#!/usr/bin/env bash
set -euo pipefail

steps="${WR_TRAIN_STEPS:-${SCREEN_STEPS:-500}}"
source_script="${WR_LOCOM_SOURCE:-train_gpt.py}"
generated_script="${WR_LOCOM_GENERATED_SCRIPT:-/tmp/train_gpt_wr_locoprop_m_${steps}.py}"
nproc="${NPROC_PER_NODE:-8}"

python3 tools/make_wr_locoprop_m.py \
  --source "${source_script}" \
  --output "${generated_script}" \
  --steps "${steps}"

python3 -m py_compile "${generated_script}"

if [[ "${WR_LOCOM_DRY_RUN:-0}" == "1" ]]; then
  echo "generated ${generated_script}"
  exit 0
fi

torchrun --standalone --nproc_per_node="${nproc}" "${generated_script}"
