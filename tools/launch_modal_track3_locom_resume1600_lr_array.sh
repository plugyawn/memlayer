#!/usr/bin/env bash
set -euo pipefail

checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/modal3000_locom_end1600_pr2873065_seed2900_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-2900}"
gpu="${NANOGPT_MODAL_GPU:-H100}"
stamp="${SUFFIX_STAMP:-$(date -u +%Y%m%d%H%M%S)}"

mkdir -p .opencode

launch_lane() {
  local name="$1"
  local steps="$2"
  local schedule="$3"
  local power="$4"
  local schedule_steps="$5"
  local bump_windows="$6"

  local run_name="track3-r1600-noloco-${name}-seed${seed_offset}-${stamp}"
  local log_path=".opencode/modal_${run_name}.launch.log"

  echo "===== launching ${run_name} =====" | tee "${log_path}"
  (
    export TRACK3_RESUME_CHECKPOINT="${checkpoint}"
    export TRACK3_RESUME_ADVANCE_DATA="${TRACK3_RESUME_ADVANCE_DATA:-1}"
    export TRACK3_RESUME_RESTORE_RNG="${TRACK3_RESUME_RESTORE_RNG:-1}"
    export TRACK3_RESUME_LOAD_OPTIMIZERS="${TRACK3_RESUME_LOAD_OPTIMIZERS:-1}"
    export TRACK3_TRAIN_STEPS="${steps}"
    export TRACK3_SEED_OFFSET="${seed_offset}"
    export TRACK3_TARGET_LOSS="${TRACK3_TARGET_LOSS:-3.28}"
    export TRACK3_LR_SCHEDULE="${schedule}"
    export TRACK3_LR_POWER="${power}"
    export TRACK3_LR_SCHEDULE_STEPS="${schedule_steps}"
    export TRACK3_LR_BUMP_WINDOWS="${bump_windows}"
    # Keep the same LocoProp-enabled/uncompiled execution path used by the
    # successful continuous nolate1600 runs. Turning LOCO_M off flips this
    # generator onto the compiled path and produced immediate NaNs after resume.
    export TRACK3_LOCOM_ENABLED=1
    export TRACK3_LOCOM_ACTIVE_WINDOWS="${TRACK3_LOCOM_ACTIVE_WINDOWS:-0:1600}"
    export TRACK3_LOCOM_END_STEP="${TRACK3_LOCOM_END_STEP:-1600}"
    export TRACK3_LOCOM_LOG_STEPS="${TRACK3_LOCOM_LOG_STEPS:-1600,1625,1650,1675,1700,1750,1800,1875,2000,2125,2250,2375,2500,2625,2750,2875,2900,2925,2950,2975,3000}"
    export SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-25}"
    export NANOGPT_MODAL_GPU="${gpu}"
    export MODAL_RUN_NAME="${run_name}"
    export MODAL_DETACH="${MODAL_DETACH:-1}"
    bash tools/launch_modal_track3_locom_3000_seed.sh
  ) 2>&1 | tee -a "${log_path}"
}

# Control: same tail schedule, but no LocoProp after the 1600 checkpoint.
launch_lane "ctrl-pr2873065" 3000 pr287 1.20 3065 ""

# Smooth LR compensation for removing LocoProp at step 1600.
launch_lane "bump110-long" 3000 pr287 1.20 3065 "1600:1750:2350:2850:1.10"
launch_lane "bump118-long" 3000 pr287 1.20 3065 "1600:1750:2350:2850:1.18"
launch_lane "bump128-long" 3000 pr287 1.20 3065 "1600:1750:2350:2850:1.28"

# Different shape: stronger but shorter compensation pulse.
launch_lane "bump125-short" 3000 pr287 1.20 3065 "1600:1700:2000:2450:1.25"

# Different shape: carry compensation deep into the final descent.
launch_lane "bump118-latefade" 3000 pr287 1.20 3065 "1600:1800:2600:3000:1.18"

# Schedule-only alternative: more LR runway, no explicit bump.
launch_lane "pr2873125-nobump" 3000 pr287 1.20 3125 ""
