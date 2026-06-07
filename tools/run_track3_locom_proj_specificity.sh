#!/usr/bin/env bash
set -euo pipefail

# Guarded c_proj LocoProp-M specificity probe.
#
# Current evidence rules out the c_fc true-post additive K5-10 path: active and
# alpha-zero match through 2000. This runner tests a genuinely different object:
# the MLP projection matrix. It intentionally defaults to the cheap pair only
# (active vs alpha-zero). Run MODE=controls only if the active pair beats the
# alpha-zero lane by a material margin.

mode="${MODE:-pair}" # pair | controls | all
checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
steps="${TRACK3_TRAIN_STEPS:-2000}"
active_end="${TRACK3_PREFIX_ACTIVE_END:-1800}"
log_dir="${TRACK3_PROJ_SPEC_LOG_DIR:-/root/prime_track3_locom_proj_specificity_logs}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"

mkdir -p "${log_dir}"

run_lane() {
  local name="$1"
  local alpha="$2"
  local local_opt="$3"
  local correction_mode="$4"
  local norm_target="$5"
  local min_cos_desc="$6"

  local label="track3_proj_${name}_seed${seed_offset}"
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
    TRACK3_LOCOM_ENABLED=1 \
    TRACK3_LOCOM_SURFACE=proj \
    TRACK3_LOCOM_LAYERS="${TRACK3_LOCOM_LAYERS:-all}" \
    TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-5}" \
    TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-2e-4}" \
    TRACK3_LOCOM_TARGET_SPACE=post \
    TRACK3_LOCOM_TRUE_POST_GRAD=1 \
    TRACK3_LOCOM_MIN_COS_DESC="${min_cos_desc}" \
    TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1 \
    TRACK3_LOCOM_ALPHA="${alpha}" \
    TRACK3_LOCOM_SAMPLE_TOKENS="${TRACK3_LOCOM_SAMPLE_TOKENS:-1024}" \
    TRACK3_LOCOM_NORM_TARGET="${norm_target}" \
    TRACK3_LOCOM_NORM_TO_BASE=0 \
    TRACK3_LOCOM_NORM_CAP="${TRACK3_LOCOM_NORM_CAP:-0.20}" \
    TRACK3_LOCOM_LOCAL_OPT="${local_opt}" \
    TRACK3_LOCOM_RANDOM_CORRECTION="$([[ "${local_opt}" == "random" ]] && echo 1 || echo 0)" \
    TRACK3_LOCOM_CORRECTION_MODE="${correction_mode}" \
    TRACK3_LOCOM_ACTIVE_WINDOWS="0:${active_end}" \
    TRACK3_LOCOM_END_STEP="${active_end}" \
    TRACK3_LOCOM_LOG_STEPS="1600,1625,1650,1675,1700,1725,1750,1775,1800,1900,2000" \
    TRACK3_LOCOM_DIAG_STEPS="1,2,4,5,8,10" \
    TRACK3_LOCOM_DIAG_MAX_LAYERS=12 \
    SCREEN_VAL_EVERY=25 \
    NPROC_PER_NODE="${NPROC_PER_NODE:-1}" \
    bash tools/run_track3_locom_kdiag_probe.sh
}

case "${mode}" in
  pair)
    run_lane "alpha_zero" "0.0" "sgd" "normal" "0.0" "0.0"
    run_lane "active_k5" "1.0" "sgd" "normal" "0.0" "0.0"
    ;;
  controls)
    run_lane "random_norm002" "1.0" "random" "normal" "0.02" "0.0"
    run_lane "orthogonal_norm002" "1.0" "sgd" "orthogonal" "0.02" "-1.0"
    ;;
  all)
    MODE=pair TRACK3_PROJ_SPEC_LOG_DIR="${log_dir}" bash "$0"
    MODE=controls TRACK3_PROJ_SPEC_LOG_DIR="${log_dir}" bash "$0"
    ;;
  *)
    echo "unsupported MODE=${mode}; use pair, controls, or all" >&2
    exit 2
    ;;
esac

active_log="${log_dir}/track3_proj_active_k5_seed${seed_offset}.log"
control_log="${log_dir}/track3_proj_alpha_zero_seed${seed_offset}.log"
if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
  echo "proj_specificity_dry_run_no_analysis" | tee -a "${log_dir}/sequence.status"
elif [[ -f "${active_log}" && -f "${control_log}" ]]; then
  python3 tools/analyze_track3_locom_prefix_effect_size.py \
    --active "${active_log}" \
    --control "${control_log}" \
    --k 5 \
    --decision-step "${TRACK3_PROJ_SPEC_DECISION_STEP:-2000}" \
    --material-gain "${TRACK3_PROJ_SPEC_MATERIAL_GAIN:-0.001}" \
    | tee "${log_dir}/track3_proj_specificity_pair_decision.md" || true
fi

echo "proj_specificity_done $(date -u +%Y-%m-%dT%H:%M:%SZ) mode=${mode}" | tee -a "${log_dir}/sequence.status"
