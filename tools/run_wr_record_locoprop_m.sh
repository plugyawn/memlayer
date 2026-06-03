#!/usr/bin/env bash
set -euo pipefail

steps="${WR_TRAIN_STEPS:-${SCREEN_STEPS:-3040}}"
schedule_steps="${WR_SCHEDULE_STEPS:-3105}"
source_script="${WR_LOCOM_SOURCE:-records/track_3_optimization/results/20260509_contra_soft_muon/03c36e81-e2e5-4916-bf16-0141999b1dbb.txt}"
generated_script="${WR_LOCOM_GENERATED_SCRIPT:-/tmp/train_gpt_wr_record_locoprop_m_${steps}.py}"
nproc="${NPROC_PER_NODE:-1}"
seed="${WR_SEED:-0}"

python3 tools/make_wr_record_locoprop_m.py \
  --source "${source_script}" \
  --output "${generated_script}" \
  --steps "${steps}" \
  --schedule-steps "${schedule_steps}"

python3 -m py_compile "${generated_script}"

source_sha="$(sha256sum "${source_script}" | awk '{print $1}')"
generator_sha="$(sha256sum tools/make_wr_record_locoprop_m.py | awk '{print $1}')"
generated_sha="$(sha256sum "${generated_script}" | awk '{print $1}')"

echo "wr_record_locom_runner source=${source_script} generated=${generated_script} steps=${steps} schedule_steps=${schedule_steps} nproc=${nproc} seed=${seed}"
echo "wr_record_locom_source_sha source=${source_sha} generator=${generator_sha} generated=${generated_sha}"

if [[ "${WR_LOCOM_DRY_RUN:-0}" == "1" ]]; then
  echo "generated ${generated_script}"
  exit 0
fi

torchrun --standalone --nproc_per_node="${nproc}" "${generated_script}" --seed "${seed}"
