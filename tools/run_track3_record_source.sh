#!/usr/bin/env bash
set -euo pipefail

source_script="${TRACK3_SOURCE:?set TRACK3_SOURCE to a checked-in Track 3 record log or source script}"
generated_script="${TRACK3_GENERATED_SCRIPT:-/tmp/train_gpt_track3_record_source.py}"
train_steps="${TRACK3_TRAIN_STEPS:-}"
schedule_steps="${TRACK3_SCHEDULE_STEPS:-}"
val_every="${SCREEN_VAL_EVERY:-125}"
nproc="${NPROC_PER_NODE:-1}"
seed="${TRACK3_SEED:?set TRACK3_SEED to the source-script seed}"

args=(--source "${source_script}" --output "${generated_script}" --val-every "${val_every}")
if [[ -n "${train_steps}" ]]; then
  args+=(--train-steps "${train_steps}")
fi
if [[ -n "${schedule_steps}" ]]; then
  args+=(--schedule-steps "${schedule_steps}")
fi

python3 tools/make_track3_record_source.py "${args[@]}"
python3 -m py_compile "${generated_script}"

echo "track3_record_source_runner source=${source_script} generated=${generated_script} train_steps=${train_steps:-source} schedule_steps=${schedule_steps:-source} seed=${seed} nproc=${nproc} mbs=${TRACK3_MBS:-64} val_every=${val_every}"

if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
  echo "generated ${generated_script}"
  exit 0
fi

torchrun --standalone --nproc_per_node="${nproc}" "${generated_script}" --seed "${seed}"
