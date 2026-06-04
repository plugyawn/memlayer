#!/usr/bin/env bash
set -euo pipefail

steps="${WR_TRAIN_STEPS:-${SCREEN_STEPS:-3040}}"
schedule_steps="${WR_SCHEDULE_STEPS:-3105}"
source_script="${WR_LOCOM_SOURCE:-records/track_3_optimization/results/20260509_contra_soft_muon/03c36e81-e2e5-4916-bf16-0141999b1dbb.txt}"
generator_kind="${WR_LOCOM_GENERATOR:-aux}"
case "${generator_kind}" in
  aux)
    generator_script="tools/make_wr_record_locoprop_m_aux.py"
    default_generated="/tmp/train_gpt_wr_record_locoprop_m_aux_${steps}.py"
    ;;
  hook)
    generator_script="tools/make_wr_record_locoprop_m.py"
    default_generated="/tmp/train_gpt_wr_record_locoprop_m_${steps}.py"
    ;;
  *)
    echo "unsupported WR_LOCOM_GENERATOR=${generator_kind}; use aux or hook" >&2
    exit 2
    ;;
esac
generated_script="${WR_LOCOM_GENERATED_SCRIPT:-${default_generated}}"
nproc="${NPROC_PER_NODE:-1}"
seed="${WR_SEED:-0}"
if [[ "${generator_kind}" == "aux" ]]; then
  export WR_LOCOM_BATCHED_PREP="${WR_LOCOM_BATCHED_PREP:-1}"
fi

python3 "${generator_script}" \
  --source "${source_script}" \
  --output "${generated_script}" \
  --steps "${steps}" \
  --schedule-steps "${schedule_steps}"

python3 -m py_compile "${generated_script}"

source_sha="$(sha256sum "${source_script}" | awk '{print $1}')"
generator_sha="$(sha256sum "${generator_script}" | awk '{print $1}')"
generated_sha="$(sha256sum "${generated_script}" | awk '{print $1}')"

echo "wr_record_locom_runner source=${source_script} generated=${generated_script} generator=${generator_kind} steps=${steps} schedule_steps=${schedule_steps} nproc=${nproc} seed=${seed}"
echo "wr_record_locom_source_sha source=${source_sha} generator_script=${generator_script} generator=${generator_sha} generated=${generated_sha}"

if [[ "${WR_LOCOM_DRY_RUN:-0}" == "1" ]]; then
  echo "generated ${generated_script}"
  exit 0
fi

torchrun --standalone --nproc_per_node="${nproc}" "${generated_script}" --seed "${seed}"
