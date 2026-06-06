#!/usr/bin/env bash
set -euo pipefail

# Run the decisive 1600->1800 prefix controls for "what makes LocoProp-M tick?"
# on an already-prepared GPU machine. This script does not provision hardware.
#
# The current evidence says K5/K8/K10 true-post c_fc LocoProp-M tie externally
# through 1800, and post-1800 active/random/no-correction suffixes also tie.
# The missing control is whether the 1600->1800 prefix is direction-specific.

checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
steps="${TRACK3_TRAIN_STEPS:-1800}"
log_dir="${TRACK3_PREFIX_SPEC_LOG_DIR:-/root/prime_track3_prefix_specificity_logs}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"

mkdir -p "${log_dir}"

run_lane() {
  local name="$1"
  local enabled="$2"
  local local_opt="$3"
  local correction_mode="$4"
  local norm_target="$5"

  local label="track3_prefix_${name}_seed${seed_offset}"
  echo "===== ${label} =====" | tee -a "${log_dir}/sequence.status"

  env \
    TRACK3_KDIAG_PROFILE="post-true-k10-lr2e4-active-poscos" \
    TRACK3_KDIAG_LABEL="${label}" \
    TRACK3_KDIAG_LOG_DIR="${log_dir}" \
    TRACK3_SOURCE="${source_script}" \
    TRACK3_GENERATED_SCRIPT="/tmp/${label}.py" \
    TRACK3_TRAIN_STEPS="${steps}" \
    TRACK3_NUM_TRIALS=1 \
    TRACK3_TARGET_LOSS=3.28 \
    TRACK3_MBS=16 \
    TRACK3_SEED_BASE=0 \
    TRACK3_SEED_OFFSET="${seed_offset}" \
    TRACK3_RESUME_CHECKPOINT="${checkpoint}" \
    TRACK3_RESUME_ADVANCE_DATA=1 \
    TRACK3_RESUME_RESTORE_RNG=1 \
    TRACK3_RESUME_LOAD_OPTIMIZERS=1 \
    TRACK3_COOLDOWN_FRAC=1.0 \
    TRACK3_LR_SCHEDULE=power \
    TRACK3_LR_POWER=2.0 \
    TRACK3_LR_SCHEDULE_STEPS=3000 \
    TRACK3_LR_MIN_ETA=0.0 \
    TRACK3_LR_SWITCH_STEP=-1 \
    TRACK3_LR_AFTER_SWITCH= \
    TRACK3_LR_BUMP_WINDOWS= \
    TRACK3_LOCOM_ENABLED="${enabled}" \
    TRACK3_LOCOM_LAYERS=all \
    TRACK3_LOCOM_STEPS=5 \
    TRACK3_LOCOM_INNER_LR=2e-4 \
    TRACK3_LOCOM_TARGET_SPACE=post \
    TRACK3_LOCOM_TRUE_POST_GRAD=1 \
    TRACK3_LOCOM_MIN_COS_DESC=0.0 \
    TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1 \
    TRACK3_LOCOM_ALPHA=1.0 \
    TRACK3_LOCOM_SAMPLE_TOKENS=1024 \
    TRACK3_LOCOM_NORM_TARGET="${norm_target}" \
    TRACK3_LOCOM_NORM_TO_BASE=0 \
    TRACK3_LOCOM_NORM_CAP=0.20 \
    TRACK3_LOCOM_LOCAL_OPT="${local_opt}" \
    TRACK3_LOCOM_RANDOM_CORRECTION="$([[ "${local_opt}" == "random" ]] && echo 1 || echo 0)" \
    TRACK3_LOCOM_CORRECTION_MODE="${correction_mode}" \
    TRACK3_LOCOM_ACTIVE_WINDOWS="0:${steps}" \
    TRACK3_LOCOM_END_STEP="${steps}" \
    TRACK3_LOCOM_LOG_STEPS="1600,1625,1650,1675,1700,1725,1750,1775,1800" \
    TRACK3_LOCOM_DIAG_STEPS="1,2,4,5,8,10" \
    TRACK3_LOCOM_DIAG_MAX_LAYERS=12 \
    SCREEN_VAL_EVERY=25 \
    NPROC_PER_NODE="${NPROC_PER_NODE:-1}" \
    bash tools/run_track3_locom_kdiag_probe.sh
}

run_lane "active_k5" 1 "sgd" "normal" "0.0"
run_lane "noloco" 0 "sgd" "normal" "0.0"
run_lane "random_norm002" 1 "random" "normal" "0.02"
run_lane "orthogonal_k5_norm002" 1 "sgd" "orthogonal" "0.02"

echo "prefix_specificity_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${log_dir}/sequence.status"
