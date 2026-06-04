#!/usr/bin/env bash
set -euo pipefail

steps="${WR_TRAIN_STEPS:-3040}"
schedule_steps="${WR_SCHEDULE_STEPS:-3105}"
source_script="${WR_RESUME_SOURCE:-records/track_3_optimization/results/20260509_contra_soft_muon/03c36e81-e2e5-4916-bf16-0141999b1dbb.txt}"
generated_script="${WR_RESUME_GENERATED_SCRIPT:-/tmp/train_gpt_wr_record_resume_${steps}.py}"
nproc="${NPROC_PER_NODE:-1}"
seed="${WR_SEED:-28}"

python3 tools/make_wr_record_resume.py \
  --source "${source_script}" \
  --output "${generated_script}" \
  --steps "${steps}" \
  --schedule-steps "${schedule_steps}"

python3 -m py_compile "${generated_script}"

source_sha="$(sha256sum "${source_script}" | awk '{print $1}')"
generator_sha="$(sha256sum tools/make_wr_record_resume.py | awk '{print $1}')"
generated_sha="$(sha256sum "${generated_script}" | awk '{print $1}')"

echo "wr_record_resume_runner source=${source_script} generated=${generated_script} steps=${steps} schedule_steps=${schedule_steps} nproc=${nproc} seed=${seed}"
echo "wr_record_resume_source_sha source=${source_sha} generator=${generator_sha} generated=${generated_sha}"
echo "wr_record_resume_checkpoint checkpoint=${WR_RESUME_CHECKPOINT:-<none>} load_adam=${WR_RESUME_LOAD_ADAM:-0} restore_rng=${WR_RESUME_RESTORE_RNG:-1} advance_data=${WR_RESUME_ADVANCE_DATA:-1} optimizer2_momentum_scale=${WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE:-1.0} optimizer2_soap_reset=${WR_RESUME_OPTIMIZER2_SOAP_RESET:-0} optimizer2_nor_reset=${WR_RESUME_OPTIMIZER2_NOR_RESET:-0}"

if [[ "${WR_RESUME_DRY_RUN:-0}" == "1" ]]; then
  echo "generated ${generated_script}"
  exit 0
fi

torchrun --standalone --nproc_per_node="${nproc}" "${generated_script}" --seed "${seed}"
