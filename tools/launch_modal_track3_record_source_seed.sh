#!/usr/bin/env bash
set -euo pipefail

source_script="${TRACK3_SOURCE:?set TRACK3_SOURCE to a checked-in Track 3 record log or source script}"
seed="${TRACK3_SEED:?set TRACK3_SEED to the seed used by the source script}"
train_steps="${TRACK3_TRAIN_STEPS:-3000}"
schedule_steps="${TRACK3_SCHEDULE_STEPS:-${train_steps}}"
val_every="${SCREEN_VAL_EVERY:-125}"
mbs="${TRACK3_MBS:-64}"
source_slug="$(basename "${source_script}" | tr -c '[:alnum:]' '-')"
run_name="${MODAL_RUN_NAME:-track3-record-t${train_steps}-h${schedule_steps}-seed${seed}-${source_slug}-$(date -u +%Y%m%d%H%M%S)}"

extra_env_json="$(python3 - <<PY
import json

extra = {
    "TRACK3_SOURCE": "${source_script}",
    "TRACK3_GENERATED_SCRIPT": "/tmp/train_gpt_record_seed${seed}_t${train_steps}_h${schedule_steps}.py",
    "TRACK3_TRAIN_STEPS": "${train_steps}",
    "TRACK3_SCHEDULE_STEPS": "${schedule_steps}",
    "TRACK3_SEED": "${seed}",
    "TRACK3_MBS": "${mbs}",
}
print(json.dumps(extra, separators=(",", ":")))
PY
)"

export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="${PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION:-python}"
export NANOGPT_MODAL_GPU="${NANOGPT_MODAL_GPU:-H100}"
export MODAL_GPU="${MODAL_GPU:-${NANOGPT_MODAL_GPU}}"
export MODAL_NANOGPT_GPU="${MODAL_NANOGPT_GPU:-${NANOGPT_MODAL_GPU}}"
export MODAL_DETACH="${MODAL_DETACH:-1}"
export MODAL_ENTRYPOINT="${MODAL_ENTRYPOINT:-run_spawn}"
export MODAL_RUN_NAME="${run_name}"
export MODAL_RUNNER="tools/run_track3_record_source.sh"
export MODAL_DATA_CHUNKS="${MODAL_DATA_CHUNKS:-20}"
export SCREEN_STEPS="${train_steps}"
export SCREEN_VAL_EVERY="${val_every}"
export NPROC_PER_NODE="${NPROC_PER_NODE:-1}"
export MODAL_EXTRA_ENV_JSON="${extra_env_json}"

exec bash tools/run_modal_newtonv_raw_gate.sh
