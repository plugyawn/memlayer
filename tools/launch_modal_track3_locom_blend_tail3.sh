#!/usr/bin/env bash
set -euo pipefail

checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
gpu="${NANOGPT_MODAL_GPU:-H100}"
stamp="${BLEND_STAMP:-$(date -u +%Y%m%d%H%M%S)}"

mkdir -p .opencode/active_launch_logs

launch_lane() {
  local name="$1"
  local blend_start="$2"
  local blend_end="$3"

  local run_name="track3-redckpt1600-${name}-wr3105p120-seed${seed_offset}-${stamp}"
  local log_path=".opencode/active_launch_logs/modal_${run_name}.launch.log"

  echo "===== launching ${run_name} =====" | tee "${log_path}"
  (
    export TRACK3_RESUME_CHECKPOINT="${checkpoint}"
    export TRACK3_RESUME_ADVANCE_DATA="${TRACK3_RESUME_ADVANCE_DATA:-1}"
    export TRACK3_RESUME_RESTORE_RNG="${TRACK3_RESUME_RESTORE_RNG:-1}"
    export TRACK3_RESUME_LOAD_OPTIMIZERS="${TRACK3_RESUME_LOAD_OPTIMIZERS:-1}"

    export TRACK3_TRAIN_STEPS="${TRACK3_TRAIN_STEPS:-3000}"
    export TRACK3_SEED_OFFSET="${seed_offset}"
    export TRACK3_TARGET_LOSS="${TRACK3_TARGET_LOSS:-3.28}"

    # Prefix schedule: keep the clean cd500/linear continuation after resume.
    export TRACK3_COOLDOWN_FRAC="${TRACK3_COOLDOWN_FRAC:-0.8333333333}"
    export TRACK3_LR_SCHEDULE="linear"
    export TRACK3_LR_POWER="1.0"
    export TRACK3_LR_SCHEDULE_STEPS="${TRACK3_LR_SCHEDULE_STEPS:-3000}"
    export TRACK3_LR_MIN_ETA="${TRACK3_LR_MIN_ETA:-0.0}"
    export TRACK3_LR_SWITCH_STEP="-1"
    export TRACK3_LR_AFTER_SWITCH=""

    # Smoothly blend the LR values into the current-record WR tail levels.
    export TRACK3_LR_BLEND_START="${blend_start}"
    export TRACK3_LR_BLEND_END="${blend_end}"
    export TRACK3_LR_BLEND_TARGET="pr287"
    export TRACK3_LR_BLEND_TARGET_POWER="1.20"
    export TRACK3_LR_BLEND_TARGET_STEPS="3105"

    export TRACK3_LOCOM_ENABLED=1
    export TRACK3_LOCOM_ACTIVE_WINDOWS="${TRACK3_LOCOM_ACTIVE_WINDOWS:-0:1800}"
    export TRACK3_LOCOM_END_STEP="${TRACK3_LOCOM_END_STEP:-1800}"
    export TRACK3_LOCOM_NORM_CAP="${TRACK3_LOCOM_NORM_CAP:-0.20}"
    export TRACK3_LOCOM_LOG_STEPS="${TRACK3_LOCOM_LOG_STEPS:-1600,1625,1650,1675,1700,1750,1800,1875,1900,1925,1950,1975,2000,2025,2050,2075,2100,2125,2250,2375,2400,2450,2500,2625,2750,2800,2875,2900,2925,2950,2975,3000}"

    export SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-25}"
    export NANOGPT_MODAL_GPU="${gpu}"
    export MODAL_RUN_NAME="${run_name}"
    export MODAL_DETACH="${MODAL_DETACH:-1}"
    bash tools/launch_modal_track3_locom_3000_seed.sh
  ) 2>&1 | tee -a "${log_path}"
}

launch_lane "blend1900to2400" 1900 2400
launch_lane "blend2000to2400" 2000 2400
launch_lane "blend2000to2600" 2000 2600
