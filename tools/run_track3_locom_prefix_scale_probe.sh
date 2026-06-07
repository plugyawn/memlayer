#!/usr/bin/env bash
set -euo pipefail

# Test the only remaining natural c_fc LocoProp prefix hypothesis:
# maybe the direction is usable, but the natural correction is too small.
#
# This is deliberately separate from run_track3_locom_prefix_specificity.sh,
# because the natural K5 lane has already matched alpha-zero. These lanes ask
# whether forcing the same true-post K5 correction to a visible base-step
# fraction beats the same-harness alpha-zero control and a random perturbation.

checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
steps="${TRACK3_TRAIN_STEPS:-2000}"
active_end="${TRACK3_PREFIX_ACTIVE_END:-1800}"
log_dir="${TRACK3_PREFIX_SCALE_LOG_DIR:-/root/prime_track3_prefix_scale_logs}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"

mkdir -p "${log_dir}"

run_lane() {
  local name="$1"
  local enabled="$2"
  local local_opt="$3"
  local correction_mode="$4"
  local norm_target="$5"
  local min_cos_desc="$6"
  local alpha="${7:-1.0}"

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
    TRACK3_LOCOM_MIN_COS_DESC="${min_cos_desc}" \
    TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1 \
    TRACK3_LOCOM_ALPHA="${alpha}" \
    TRACK3_LOCOM_SAMPLE_TOKENS=1024 \
    TRACK3_LOCOM_NORM_TARGET="${norm_target}" \
    TRACK3_LOCOM_NORM_TO_BASE=0 \
    TRACK3_LOCOM_NORM_CAP=0.20 \
    TRACK3_LOCOM_LOCAL_OPT="${local_opt}" \
    TRACK3_LOCOM_RANDOM_CORRECTION="$([[ "${local_opt}" == "random" ]] && echo 1 || echo 0)" \
    TRACK3_LOCOM_CORRECTION_MODE="${correction_mode}" \
    TRACK3_LOCOM_ACTIVE_WINDOWS="0:${active_end}" \
    TRACK3_LOCOM_END_STEP="${active_end}" \
    TRACK3_LOCOM_LOG_STEPS="1600,1625,1650,1675,1700,1725,1750,1775,1800,1900,2000" \
    TRACK3_LOCOM_DIAG_STEPS="1,2,4,5" \
    TRACK3_LOCOM_DIAG_MAX_LAYERS=12 \
    SCREEN_VAL_EVERY=25 \
    NPROC_PER_NODE="${NPROC_PER_NODE:-1}" \
    bash tools/run_track3_locom_kdiag_probe.sh
}

if [[ "${TRACK3_PREFIX_SCALE_SKIP_CONTROL:-0}" != "1" ]]; then
  run_lane "noloco" 1 "sgd" "normal" "0.0" "0.0" "0.0"
fi
if [[ "${TRACK3_PREFIX_SCALE_SKIP_NATURAL:-0}" != "1" ]]; then
  run_lane "active_k5" 1 "sgd" "normal" "0.0" "0.0"
fi
run_lane "norm002_k5" 1 "sgd" "normal" "0.02" "0.0"
run_lane "norm005_k5" 1 "sgd" "normal" "0.05" "0.0"
run_lane "random_norm002" 1 "random" "normal" "0.02" "0.0"

prefix_logs=("${log_dir}"/track3_prefix_*.log)
if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
  echo "prefix_scale_dry_run_no_analysis" | tee -a "${log_dir}/sequence.status"
elif [[ -e "${prefix_logs[0]}" ]]; then
  python3 tools/analyze_track3_locom_prefix_probe.py \
    --steps "1600,1625,1650,1675,1700,1725,1750,1775,1800,1900,2000" \
    --material-gain "${TRACK3_PREFIX_SCALE_MATERIAL_GAIN:-0.0010}" \
    "${prefix_logs[@]}" | tee "${log_dir}/track3_prefix_scale_decision.md" || true
fi

echo "prefix_scale_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${log_dir}/sequence.status"
