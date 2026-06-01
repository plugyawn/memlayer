#!/usr/bin/env bash
set -euo pipefail

checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/modal3100_locom_seed400_step2400.pt}"
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
  local cap_windows="${8:-}"
  local lr_min_eta="${9:-0.0}"

  local run_name="track3-s2400-pre3000-${name}-seed${seed_offset}-${stamp}"
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
    export TRACK3_LR_MIN_ETA="${lr_min_eta}"
    export TRACK3_LOCOM_NORM_CAP="${cap}"
    export TRACK3_LOCOM_END_STEP="${end_step}"
    export TRACK3_LOCOM_LOG_STEPS="${TRACK3_LOCOM_LOG_STEPS:-2400,2425,2450,2475,2500,2600,2700,2750,2800,2875,2900,2925,2950,2975,3000}"
    if [[ -n "${cap_windows}" ]]; then
      export TRACK3_LOCOM_NORM_CAP_WINDOWS="${cap_windows}"
    else
      unset TRACK3_LOCOM_NORM_CAP_WINDOWS || true
    fi
    export SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-25}"
    export NANOGPT_MODAL_GPU="${gpu}"
    export MODAL_RUN_NAME="${run_name}"
    export MODAL_DETACH="${MODAL_DETACH:-1}"
    bash tools/launch_modal_track3_locom_3000_seed.sh
  ) 2>&1 | tee -a "${log_path}"
}

# Fidelity and controls from the saved 2400 state.
launch_lane "fid3000-linear-cap020" 3000 linear 1.0 0 0.20 1000000000
launch_lane "s3000-linear-nolate" 3000 linear 1.0 0 0.20 2400

# Old suffix-family LR variants, forced to decide by 3000.
launch_lane "s3000-power050-cap020" 3000 power 0.50 0 0.20 1000000000
launch_lane "s3000-power050-cap040" 3000 power 0.50 0 0.40 1000000000
launch_lane "s3000-power035-cap040" 3000 power 0.35 0 0.40 1000000000
launch_lane "s3000-pr2873065-cap020" 3000 pr287 1.20 3065 0.20 1000000000
launch_lane "s3000-pr2873065-cap040" 3000 pr287 1.20 3065 0.40 1000000000

# Requested higher LocoProp force around the critical tail, but only after the saved 2400 state.
launch_lane "s3000-linear-capwin040-2400-3000" 3000 linear 1.0 0 0.20 1000000000 "2400:3000:0.40"

