#!/usr/bin/env bash
set -euo pipefail

checkpoint="${TRACK3_RESUME_CHECKPOINT:?set TRACK3_RESUME_CHECKPOINT to the Modal-volume checkpoint path}"
seed_offset="${TRACK3_SEED_OFFSET:-400}"
gpu="${NANOGPT_MODAL_GPU:-H100}"
stamp="${SUFFIX_STAMP:-$(date -u +%Y%m%d%H%M%S)}"

mkdir -p .opencode

launch_lane() {
  local name="$1"
  local steps="$2"
  local schedule="$3"
  local power="$4"
  local schedule_steps="$5"
  local cap="$6"
  local end_step="$7"

  local run_name="track3-suffix-${name}-seed${seed_offset}-${stamp}"
  local log_path=".opencode/modal_${run_name}.launch.log"

  echo "===== launching ${run_name} =====" | tee "${log_path}"
  (
    export TRACK3_RESUME_CHECKPOINT="${checkpoint}"
    export TRACK3_RESUME_ADVANCE_DATA="${TRACK3_RESUME_ADVANCE_DATA:-1}"
    export TRACK3_RESUME_RESTORE_RNG="${TRACK3_RESUME_RESTORE_RNG:-1}"
    export TRACK3_TRAIN_STEPS="${steps}"
    export TRACK3_SEED_OFFSET="${seed_offset}"
    export TRACK3_TARGET_LOSS="${TRACK3_TARGET_LOSS:-3.28}"
    export TRACK3_LR_SCHEDULE="${schedule}"
    export TRACK3_LR_POWER="${power}"
    export TRACK3_LR_SCHEDULE_STEPS="${schedule_steps}"
    export TRACK3_LOCOM_NORM_CAP="${cap}"
    export TRACK3_LOCOM_END_STEP="${end_step}"
    export TRACK3_LOCOM_LOG_STEPS="${TRACK3_LOCOM_LOG_STEPS:-2800,2825,2850,2875,2900,2925,2950,2975,3000,3025,3030,3050,3075,3100}"
    export SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-25}"
    export NANOGPT_MODAL_GPU="${gpu}"
    export MODAL_RUN_NAME="${run_name}"
    export MODAL_DETACH="${MODAL_DETACH:-1}"
    bash tools/launch_modal_track3_locom_3000_seed.sh
  ) 2>&1 | tee -a "${log_path}"
}

# One exact-continuation lane to validate checkpoint fidelity.
launch_lane "fid3100-linear-cap020" 3100 linear 1.0 0 0.20 1000000000

# Prefer <=3030: make the tail less cold and/or let LocoProp retain more force.
launch_lane "s3030-power050-cap020" 3030 power 0.50 0 0.20 1000000000
launch_lane "s3030-power050-cap050" 3030 power 0.50 0 0.50 1000000000
launch_lane "s3030-power035-cap050" 3030 power 0.35 0 0.50 1000000000
launch_lane "s3030-pr2873065-cap020" 3030 pr287 1.20 3065 0.20 1000000000
launch_lane "s3030-pr2873065-cap050" 3030 pr287 1.20 3065 0.50 1000000000

# <=3100 fallback lanes: preserve more LR runway or remove late LocoProp if it hurts polish.
launch_lane "s3100-power050-cap020" 3100 power 0.50 0 0.20 1000000000
launch_lane "s3100-power050-cap050" 3100 power 0.50 0 0.50 1000000000
launch_lane "s3100-linear-no-late-locom" 3100 linear 1.0 0 0.20 2800
