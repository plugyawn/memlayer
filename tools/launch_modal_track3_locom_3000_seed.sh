#!/usr/bin/env bash
set -euo pipefail

steps="${TRACK3_TRAIN_STEPS:-3000}"
seed_offset="${TRACK3_SEED_OFFSET:?set TRACK3_SEED_OFFSET, e.g. 900}"
run_name="${MODAL_RUN_NAME:-track3-simple-locom-${steps}-h100-seed${seed_offset}-$(date -u +%Y%m%d%H%M%S)}"

extra_env_json="$(python3 - <<PY
import json

steps = "${steps}"
seed_offset = "${seed_offset}"
extra = {
    "TRACK3_TRAIN_STEPS": steps,
    "TRACK3_NUM_TRIALS": "1",
    "TRACK3_TARGET_LOSS": "3.28",
    "TRACK3_SOURCE": "records/track_3_optimization/train_gpt_simple.py",
    "TRACK3_MBS": "16",
    "TRACK3_SEED_BASE": "0",
    "TRACK3_SEED_OFFSET": seed_offset,
    "TRACK3_LOCOM_ENABLED": "1",
    "TRACK3_LOCOM_LAYERS": "all",
    "TRACK3_LOCOM_STEPS": "4",
    "TRACK3_LOCOM_SAMPLE_TOKENS": "1024",
    "TRACK3_LOCOM_INNER_LR": "0.1",
    "TRACK3_LOCOM_TARGET_GAMMA": "1.0",
    "TRACK3_LOCOM_PROX": "0.1",
    "TRACK3_LOCOM_ALPHA": "1.0",
    "TRACK3_LOCOM_NORM_CAP": "0.20",
    "TRACK3_LOCOM_INTERVAL": "1",
    "TRACK3_LOCOM_LOG_STEPS": "0,1,2,10,50,125,250,500,750,875,1000,1125,1250,1500,1750,2000,2250,2500,2750,2875,3000,3125,3250",
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
export MODAL_RUNNER="tools/run_track3_locoprop_m.sh"
export MODAL_DATA_CHUNKS="${MODAL_DATA_CHUNKS:-20}"
export SCREEN_STEPS="${steps}"
export SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-125}"
export NPROC_PER_NODE="${NPROC_PER_NODE:-1}"
export MODAL_EXTRA_ENV_JSON="${extra_env_json}"

exec bash tools/run_modal_newtonv_raw_gate.sh
