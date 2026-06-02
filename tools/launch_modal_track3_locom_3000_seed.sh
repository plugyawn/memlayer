#!/usr/bin/env bash
set -euo pipefail

steps="${TRACK3_TRAIN_STEPS:-3000}"
seed_offset="${TRACK3_SEED_OFFSET:?set TRACK3_SEED_OFFSET, e.g. 900}"
run_name="${MODAL_RUN_NAME:-track3-simple-locom-${steps}-h100-seed${seed_offset}-$(date -u +%Y%m%d%H%M%S)}"

extra_env_json="$(python3 - <<PY
import json
import os

steps = "${steps}"
seed_offset = "${seed_offset}"
cooldown_frac = "${TRACK3_COOLDOWN_FRAC:-0.7}"
lr_schedule = "${TRACK3_LR_SCHEDULE:-linear}"
lr_power = "${TRACK3_LR_POWER:-1.0}"
lr_schedule_steps = "${TRACK3_LR_SCHEDULE_STEPS:-0}"
lr_min_eta = "${TRACK3_LR_MIN_ETA:-0.0}"
lr_switch_step = "${TRACK3_LR_SWITCH_STEP:--1}"
lr_after_switch = "${TRACK3_LR_AFTER_SWITCH:-}"
lr_after_switch_power = "${TRACK3_LR_AFTER_SWITCH_POWER:-${TRACK3_LR_POWER:-1.0}}"
lr_after_switch_steps = "${TRACK3_LR_AFTER_SWITCH_STEPS:-0}"
soft_muon = "${TRACK3_SOFT_MUON:-0}"
soft_muon_blend = "${TRACK3_SOFT_MUON_BLEND:-1.0}"
soft_muon_norm_restore = "${TRACK3_SOFT_MUON_NORM_RESTORE:-1}"
extra = {
    "TRACK3_TRAIN_STEPS": steps,
    "TRACK3_NUM_TRIALS": "1",
    "TRACK3_TARGET_LOSS": "3.28",
    "TRACK3_SOURCE": "records/track_3_optimization/train_gpt_simple.py",
    "TRACK3_MBS": "16",
    "TRACK3_SEED_BASE": "0",
    "TRACK3_SEED_OFFSET": seed_offset,
    "TRACK3_COOLDOWN_FRAC": cooldown_frac,
    "TRACK3_LR_SCHEDULE": lr_schedule,
    "TRACK3_LR_POWER": lr_power,
    "TRACK3_LR_SCHEDULE_STEPS": lr_schedule_steps,
    "TRACK3_LR_MIN_ETA": lr_min_eta,
    "TRACK3_LR_SWITCH_STEP": lr_switch_step,
    "TRACK3_LR_AFTER_SWITCH": lr_after_switch,
    "TRACK3_LR_AFTER_SWITCH_POWER": lr_after_switch_power,
    "TRACK3_LR_AFTER_SWITCH_STEPS": lr_after_switch_steps,
    "TRACK3_SOFT_MUON": soft_muon,
    "TRACK3_SOFT_MUON_BLEND": soft_muon_blend,
    "TRACK3_SOFT_MUON_NORM_RESTORE": soft_muon_norm_restore,
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
for key in (
    "TRACK3_SOURCE",
    "TRACK3_PASS_TRIAL_ARG",
    "TRACK3_TRIAL_ARG_MODE",
    "TRACK3_MBS",
    "TRACK3_SEED_BASE",
    "TRACK3_CHECKPOINT_STEPS",
    "TRACK3_CHECKPOINT_DIR",
    "TRACK3_CHECKPOINT_PREFIX",
    "TRACK3_CHECKPOINT_EXIT_AFTER",
    "TRACK3_RESUME_CHECKPOINT",
    "TRACK3_RESUME_ADVANCE_DATA",
    "TRACK3_RESUME_RESTORE_RNG",
    "TRACK3_TARGET_LOSS",
    "TRACK3_LOCOM_ENABLED",
    "TRACK3_LOCOM_LAYERS",
    "TRACK3_LOCOM_STEPS",
    "TRACK3_LOCOM_SAMPLE_TOKENS",
    "TRACK3_LOCOM_INNER_LR",
    "TRACK3_LOCOM_TARGET_GAMMA",
    "TRACK3_LOCOM_PROX",
    "TRACK3_LOCOM_ALPHA",
    "TRACK3_LOCOM_START_STEP",
    "TRACK3_LOCOM_END_STEP",
    "TRACK3_LOCOM_ACTIVE_WINDOWS",
    "TRACK3_LOCOM_NORM_TO_BASE",
    "TRACK3_LOCOM_NORM_TARGET",
    "TRACK3_LOCOM_NORM_CAP",
    "TRACK3_LOCOM_NORM_CAP_WINDOWS",
    "TRACK3_LOCOM_INTERVAL",
    "TRACK3_LOCOM_GATHER_SAMPLES",
    "TRACK3_LOCOM_ACCUM_SAMPLES",
    "TRACK3_LOCOM_MICRO_SAMPLE_TOKENS",
    "TRACK3_LOCOM_LOCAL_OPT",
    "TRACK3_LOCOM_LOCAL_LR_DECAY",
    "TRACK3_LOCOM_RMS_BETA1",
    "TRACK3_LOCOM_RMS_BETA2",
    "TRACK3_LOCOM_RMS_EPS",
    "TRACK3_LOCOM_RMS_RESET_EACH_STEP",
    "TRACK3_LOCOM_REQUIRE_LOSS_DECREASE",
    "TRACK3_LOCOM_MIN_COS_DESC",
    "TRACK3_LOCOM_LOG_STEPS",
    "TRACK3_ADAM_EMBED_POWER_C",
    "TRACK3_ADAM_PROJ_POWER_C",
    "TRACK3_ADAM_OTHER_POWER_C",
    "TRACK3_MUON_POWER_C",
    "TRACK3_LR_MIN_ETA",
    "TRACK3_LR_SWITCH_STEP",
    "TRACK3_LR_AFTER_SWITCH",
    "TRACK3_LR_AFTER_SWITCH_POWER",
    "TRACK3_LR_AFTER_SWITCH_STEPS",
):
    if key in os.environ:
        extra[key] = os.environ[key]
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
