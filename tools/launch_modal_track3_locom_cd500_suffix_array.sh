#!/usr/bin/env bash
set -euo pipefail

checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500_end1800_pr2873075_seed3703_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3703}"
gpu="${NANOGPT_MODAL_GPU:-H100}"
stamp="${SUFFIX_STAMP:-$(date -u +%Y%m%d%H%M%S)}"

mkdir -p .opencode

launch_lane() {
  local name="$1"
  local steps="$2"
  local cooldown_frac="$3"
  local schedule="$4"
  local power="$5"
  local schedule_steps="$6"
  local lr_min_eta="$7"
  local switch_step="$8"
  local after_switch="$9"
  local after_power="${10}"
  local after_steps="${11}"
  local locom_end="${12}"
  local soft_muon="${13}"
  local soft_blend="${14}"
  local soft_start="${15}"
  local soft_end="${16}"
  local soft_ceil="${17}"
  local load_optimizers="${18}"
  local bump_windows="${19:-}"

  local run_name="track3-cd500ckpt1600-${name}-seed${seed_offset}-${stamp}"
  local log_path=".opencode/modal_${run_name}.launch.log"

  echo "===== launching ${run_name} =====" | tee "${log_path}"
  (
    export TRACK3_RESUME_CHECKPOINT="${checkpoint}"
    export TRACK3_RESUME_ADVANCE_DATA="${TRACK3_RESUME_ADVANCE_DATA:-1}"
    export TRACK3_RESUME_RESTORE_RNG="${TRACK3_RESUME_RESTORE_RNG:-1}"
    export TRACK3_RESUME_LOAD_OPTIMIZERS="${load_optimizers}"
    export TRACK3_TRAIN_STEPS="${steps}"
    export TRACK3_SEED_OFFSET="${seed_offset}"
    export TRACK3_TARGET_LOSS="${TRACK3_TARGET_LOSS:-3.28}"
    export TRACK3_COOLDOWN_FRAC="${cooldown_frac}"
    export TRACK3_LR_SCHEDULE="${schedule}"
    export TRACK3_LR_POWER="${power}"
    export TRACK3_LR_SCHEDULE_STEPS="${schedule_steps}"
    export TRACK3_LR_MIN_ETA="${lr_min_eta}"
    export TRACK3_LR_SWITCH_STEP="${switch_step}"
    export TRACK3_LR_AFTER_SWITCH="${after_switch}"
    export TRACK3_LR_AFTER_SWITCH_POWER="${after_power}"
    export TRACK3_LR_AFTER_SWITCH_STEPS="${after_steps}"
    export TRACK3_LR_BUMP_WINDOWS="${bump_windows}"
    export TRACK3_LOCOM_ENABLED=1
    export TRACK3_LOCOM_ACTIVE_WINDOWS="0:${locom_end}"
    export TRACK3_LOCOM_END_STEP="${locom_end}"
    export TRACK3_LOCOM_NORM_CAP="${TRACK3_LOCOM_NORM_CAP:-0.20}"
    export TRACK3_LOCOM_LOG_STEPS="${TRACK3_LOCOM_LOG_STEPS:-1600,1625,1650,1675,1700,1750,1800,1875,2000,2125,2250,2375,2500,2625,2750,2800,2825,2850,2875,2900,2925,2950,2975,3000,3025,3030,3050,3075,3100}"
    export TRACK3_SOFT_MUON="${soft_muon}"
    export TRACK3_SOFT_MUON_BLEND="${soft_blend}"
    export TRACK3_SOFT_MUON_START_STEP="${soft_start}"
    export TRACK3_SOFT_MUON_END_STEP="${soft_end}"
    export TRACK3_SOFT_MUON_CEIL="${soft_ceil}"
    export TRACK3_SOFT_MUON_NORM_RESTORE="${TRACK3_SOFT_MUON_NORM_RESTORE:-1}"
    export SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-25}"
    export NANOGPT_MODAL_GPU="${gpu}"
    export MODAL_RUN_NAME="${run_name}"
    export MODAL_DETACH="${MODAL_DETACH:-1}"
    bash tools/launch_modal_track3_locom_3000_seed.sh
  ) 2>&1 | tee -a "${log_path}"
}

# Exact continuation of the cd500/end1800/PR287-3075 plan from the 1600 image.
launch_lane "fid3000-cd500-end1800-pr2873075" 3000 0.8333333333 linear 1.0 3000 0.0 1800 pr287 1.20 3075 1800 0 1.0 -1 -1 1.0 1

# Keep LocoProp-M alive all the way through the 3000-step landing.
launch_lane "full-locom3000-cd500-pr2873075" 3000 0.8333333333 linear 1.0 3000 0.0 1800 pr287 1.20 3075 3000 0 1.0 -1 -1 1.0 1

# cd500 has eta ~=0.56 at step 1600, versus ~=0.67 in the old cd070 lead.
# This keeps the same handoff but temporarily restores that missing LR scale.
launch_lane "lrcomp3000-bump118-end1800-pr2873075" 3000 0.8333333333 linear 1.0 3000 0.0 1800 pr287 1.20 3075 1800 0 1.0 -1 -1 1.0 1 "1600:1700:2300:2700:1.18"

# Softer PR287 merge: keep the cd500 linear schedule through LocoProp shutoff,
# then switch later with a gentler PR287 power. This tests whether the 1800
# handoff is the source of the late slope kink.
launch_lane "softmerge3000-switch2000-pr2873075-p110" 3000 0.8333333333 linear 1.0 3000 0.0 2000 pr287 1.10 3075 1800 0 1.0 -1 -1 1.0 1

# Terminal update-geometry probe: preserve the LocoProp suffix, then ramp
# toward PR291 Soft-Muon in the low-LR landing region, mirroring the current
# record's normal-to-soft ramp.
launch_lane "terminal-soft2500to3010-full-locom3100-pr2873105" 3100 0.8333333333 linear 1.0 3100 0.0 1800 pr287 1.20 3105 3100 1 1.0 2500 3010 0.80 1
