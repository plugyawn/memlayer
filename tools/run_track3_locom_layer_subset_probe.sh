#!/usr/bin/env bash
set -euo pipefail

# Run the layer-subset probe for Track 3 LocoProp-M on an already
# prepared GPU machine. This script does not provision hardware.
#
# It assumes the all-layer K5 prefix can reproduce ~3.3987 @1800 and the
# healthy 1900->2000 carry window. The correction is active only through 1800,
# then every lane continues without LocoProp to 2000. The probe asks whether the
# robust c_fc subset from kdiag is sufficient:
#   core_7_10      = layers 7,8,9,10
#   expanded_6_10  = layers 6,7,8,9,10

checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
steps="${TRACK3_TRAIN_STEPS:-2000}"
active_end="${TRACK3_LAYER_SUBSET_ACTIVE_END:-1800}"
log_dir="${TRACK3_LAYER_SUBSET_LOG_DIR:-/root/prime_track3_layer_subset_logs}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"

mkdir -p "${log_dir}"
python3 tools/check_track3_locom_layer_subset_manifest.py --manifest-only \
  | tee "${log_dir}/track3_layer_subset_manifest.md"

run_lane() {
  local name="$1"
  local enabled="$2"
  local layers="$3"

  local label="track3_layersubset_${name}_seed${seed_offset}"
  echo "===== ${label} layers=${layers} =====" | tee -a "${log_dir}/sequence.status"

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
    TRACK3_LOCOM_LAYERS="${layers}" \
    TRACK3_LOCOM_STEPS=5 \
    TRACK3_LOCOM_INNER_LR=2e-4 \
    TRACK3_LOCOM_TARGET_SPACE=post \
    TRACK3_LOCOM_TRUE_POST_GRAD=1 \
    TRACK3_LOCOM_MIN_COS_DESC=0.0 \
    TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1 \
    TRACK3_LOCOM_ALPHA=1.0 \
    TRACK3_LOCOM_SAMPLE_TOKENS=1024 \
    TRACK3_LOCOM_NORM_TARGET=0.0 \
    TRACK3_LOCOM_NORM_TO_BASE=0 \
    TRACK3_LOCOM_NORM_CAP=0.20 \
    TRACK3_LOCOM_LOCAL_OPT=sgd \
    TRACK3_LOCOM_RANDOM_CORRECTION=0 \
    TRACK3_LOCOM_CORRECTION_MODE=normal \
    TRACK3_LOCOM_ACTIVE_WINDOWS="0:${active_end}" \
    TRACK3_LOCOM_END_STEP="${active_end}" \
    TRACK3_LOCOM_LOG_STEPS="1600,1625,1650,1675,1700,1725,1750,1775,1800,1900,2000" \
    TRACK3_LOCOM_DIAG_STEPS="1,2,4,5" \
    TRACK3_LOCOM_DIAG_MAX_LAYERS=12 \
    SCREEN_VAL_EVERY=25 \
    NPROC_PER_NODE="${NPROC_PER_NODE:-1}" \
    bash tools/run_track3_locom_kdiag_probe.sh
}

run_lane "active_all" 1 "all"
run_lane "core_7_10" 1 "7,8,9,10"
run_lane "expanded_6_10" 1 "6,7,8,9,10"
if [[ "${TRACK3_LAYER_SUBSET_INCLUDE_FREQ:-0}" == "1" ]]; then
  run_lane "freq_0_6_10" 1 "0,6,10"
fi
run_lane "noloco" 0 "all"

subset_logs=("${log_dir}"/track3_layersubset_*.log)
if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
  echo "layer_subset_dry_run_no_header_validation" | tee -a "${log_dir}/sequence.status"
elif [[ -e "${subset_logs[0]}" ]]; then
  python3 tools/check_track3_locom_layer_subset_manifest.py \
    "${subset_logs[@]}" | tee "${log_dir}/track3_layer_subset_manifest_check.md"
  python3 tools/analyze_track3_locom_layer_subset_probe.py \
    --steps "1600,1625,1650,1675,1700,1725,1750,1775,1800,1900,2000" \
    "${subset_logs[@]}" | tee "${log_dir}/track3_layer_subset_decision.md" || true
fi

echo "layer_subset_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${log_dir}/sequence.status"
