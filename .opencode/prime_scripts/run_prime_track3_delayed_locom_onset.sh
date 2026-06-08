#!/usr/bin/env bash
set -euo pipefail

repo="${TRACK3_REPO:-/root/wr-track3-locom-20260606}"
log_dir="${TRACK3_LOG_DIR:-/root/prime_track3_delayed_locom_onset_logs}"
ckpt_dir="${TRACK3_CHECKPOINT_DIR:-/root/.cache/track3_checkpoints}"
train_steps="${TRACK3_TRAIN_STEPS:-2000}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"

mkdir -p "${log_dir}" "${ckpt_dir}"
cd "${repo}"

if [[ -f /root/venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source /root/venv/bin/activate
elif [[ -f /home/ubuntu/venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source /home/ubuntu/venv/bin/activate
fi

status="${log_dir}/sequence.status"
echo "===== delayed_locom_onset $(date -u +%Y-%m-%dT%H:%M:%SZ) =====" | tee -a "${status}"
echo "repo=${repo} source=${source_script} train_steps=${train_steps} seed_offset=${seed_offset}" | tee -a "${status}"

run_lane() {
  local label="$1"
  local enabled="$2"
  local windows="$3"
  local scale_mode="$4"
  local act_target="$5"
  local norm_cap="$6"
  local log_file="${log_dir}/${label}.log"

  echo "===== ${label} $(date -u +%Y-%m-%dT%H:%M:%SZ) =====" | tee -a "${status}"
  env \
    TRACK3_SOURCE="${source_script}" \
    TRACK3_NUM_TRIALS=1 \
    TRACK3_TARGET_LOSS=3.28 \
    TRACK3_MBS="${TRACK3_MBS:-16}" \
    TRACK3_SEED_BASE=0 \
    TRACK3_SEED_OFFSET="${seed_offset}" \
    TRACK3_TRAIN_STEPS="${train_steps}" \
    TRACK3_COOLDOWN_FRAC="${TRACK3_COOLDOWN_FRAC:-1.0}" \
    TRACK3_LR_SCHEDULE="${TRACK3_LR_SCHEDULE:-power}" \
    TRACK3_LR_POWER="${TRACK3_LR_POWER:-2.0}" \
    TRACK3_LR_SCHEDULE_STEPS="${TRACK3_LR_SCHEDULE_STEPS:-3000}" \
    TRACK3_LR_MIN_ETA=0.0 \
    TRACK3_LR_MIN_ETA_WINDOWS= \
    TRACK3_LR_ADAM_MIN_ETA_WINDOWS= \
    TRACK3_LR_MUON_MIN_ETA_WINDOWS= \
    TRACK3_LR_BUMP_WINDOWS= \
    TRACK3_LR_ADAM_BUMP_WINDOWS= \
    TRACK3_LR_MUON_BUMP_WINDOWS= \
    TRACK3_LR_SWITCH_STEP=-1 \
    TRACK3_LR_AFTER_SWITCH= \
    TRACK3_LR_BLEND_START=-1 \
    TRACK3_LR_BLEND_END=-1 \
    TRACK3_LR_BLEND_TARGET= \
    TRACK3_LOCOM_ENABLED="${enabled}" \
    TRACK3_LOCOM_ACTIVE_WINDOWS="${windows}" \
    TRACK3_LOCOM_END_STEP="${train_steps}" \
    TRACK3_LOCOM_LAYERS="${TRACK3_LOCOM_LAYERS:-all}" \
    TRACK3_LOCOM_SURFACE=fc \
    TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-5}" \
    TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-2e-4}" \
    TRACK3_LOCOM_PROX="${TRACK3_LOCOM_PROX:-0.1}" \
    TRACK3_LOCOM_TARGET_SPACE=post \
    TRACK3_LOCOM_TRUE_POST_GRAD=1 \
    TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1 \
    TRACK3_LOCOM_MIN_COS_DESC="${TRACK3_LOCOM_MIN_COS_DESC:-0.0}" \
    TRACK3_LOCOM_SAMPLE_TOKENS="${TRACK3_LOCOM_SAMPLE_TOKENS:-1024}" \
    TRACK3_LOCOM_SCALE_MODE="${scale_mode}" \
    TRACK3_LOCOM_ACT_TARGET="${act_target}" \
    TRACK3_LOCOM_NORM_CAP="${norm_cap}" \
    TRACK3_LOCOM_NORM_TARGET=0.0 \
    TRACK3_LOCOM_NORM_TO_BASE=0 \
    TRACK3_LOCOM_LOG_STEPS=0,1,2,10,50,125,250,500,750,1000,1125,1200,1225,1250,1375,1500,1600,1625,1650,1700,1750,1800,1900,2000 \
    TRACK3_LOCOM_DIAG_STEPS=1,3,5 \
    TRACK3_LOCOM_DIAG_MAX_LAYERS=4 \
    TRACK3_CHECKPOINT_DIR="${ckpt_dir}" \
    TRACK3_CHECKPOINT_PREFIX="${label}" \
    TRACK3_CHECKPOINT_STEPS=1200,1600,1800,2000 \
    SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-25}" \
    NPROC_PER_NODE="${NPROC_PER_NODE:-1}" \
    TRACK3_GENERATED_SCRIPT="/tmp/${label}.py" \
    bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${log_file}"
}

# Exact prefix/schedule control. This compiles the generated script but disables
# LocoProp entirely, so any delayed-onset win must beat this curve.
run_lane "track3_simplemuon_control_seed${seed_offset}_to${train_steps}" \
  0 "" param 0.0 0.0

# Main hypothesis: let Muon accumulate breadth first, then apply a functional
# LocoProp correction once the prefix state exists.
run_lane "track3_locom_actbase050_on1200_seed${seed_offset}_to${train_steps}" \
  1 "1200:${train_steps}" act_base "${TRACK3_LOCOM_ACT_TARGET_1200:-0.50}" "${TRACK3_LOCOM_NORM_CAP_1200:-1.0}"

run_lane "track3_locom_actbase050_on1600_seed${seed_offset}_to${train_steps}" \
  1 "1600:${train_steps}" act_base "${TRACK3_LOCOM_ACT_TARGET_1600:-0.50}" "${TRACK3_LOCOM_NORM_CAP_1600:-1.0}"

python3 tools/analyze_track3_locom_lr_slope.py \
  --steps 1000,1200,1250,1375,1500,1600,1700,1800,1900,2000 \
  --target-step 3000 \
  --target-loss 3.28 \
  "${log_dir}" | tee "${log_dir}/delayed_onset_slope.md" || true

echo "done delayed_locom_onset $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${status}"
