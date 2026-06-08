#!/usr/bin/env bash
set -euo pipefail

repo="${TRACK3_REPO:-/root/wr-track3-locom-20260606}"
log_dir="${TRACK3_LOG_DIR:-/root/prime_track3_delayed_locom_resume_onset_logs}"
ckpt_dir="${TRACK3_CHECKPOINT_DIR:-/root/.cache/track3_checkpoints}"
train_steps="${TRACK3_TRAIN_STEPS:-1800}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
seed="${TRACK3_SEED:-${seed_offset}}"
prefix_label="track3_simplemuon_prefix_seed${seed_offset}_to${train_steps}"

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
echo "===== delayed_locom_resume_onset $(date -u +%Y-%m-%dT%H:%M:%SZ) =====" | tee -a "${status}"
echo "repo=${repo} source=${source_script} train_steps=${train_steps} seed_offset=${seed_offset}" | tee -a "${status}"

common_env=(
  TRACK3_SOURCE="${source_script}"
  TRACK3_NUM_TRIALS=1
  TRACK3_TARGET_LOSS=3.28
  TRACK3_MBS="${TRACK3_MBS:-16}"
  TRACK3_SEED_BASE=0
  TRACK3_SEED_OFFSET="${seed_offset}"
  TRACK3_TRAIN_STEPS="${train_steps}"
  TRACK3_COOLDOWN_FRAC="${TRACK3_COOLDOWN_FRAC:-1.0}"
  TRACK3_LR_SCHEDULE="${TRACK3_LR_SCHEDULE:-power}"
  TRACK3_LR_POWER="${TRACK3_LR_POWER:-2.0}"
  TRACK3_LR_SCHEDULE_STEPS="${TRACK3_LR_SCHEDULE_STEPS:-3000}"
  TRACK3_LR_MIN_ETA=0.0
  TRACK3_LR_MIN_ETA_WINDOWS=
  TRACK3_LR_ADAM_MIN_ETA_WINDOWS=
  TRACK3_LR_MUON_MIN_ETA_WINDOWS=
  TRACK3_LR_BUMP_WINDOWS=
  TRACK3_LR_ADAM_BUMP_WINDOWS=
  TRACK3_LR_MUON_BUMP_WINDOWS=
  TRACK3_LR_SWITCH_STEP=-1
  TRACK3_LR_AFTER_SWITCH=
  TRACK3_LR_BLEND_START=-1
  TRACK3_LR_BLEND_END=-1
  TRACK3_LR_BLEND_TARGET=
  TRACK3_LOCOM_LAYERS="${TRACK3_LOCOM_LAYERS:-all}"
  TRACK3_LOCOM_SURFACE=fc
  TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-5}"
  TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-2e-4}"
  TRACK3_LOCOM_PROX="${TRACK3_LOCOM_PROX:-0.1}"
  TRACK3_LOCOM_TARGET_SPACE=post
  TRACK3_LOCOM_TRUE_POST_GRAD=1
  TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1
  TRACK3_LOCOM_MIN_COS_DESC="${TRACK3_LOCOM_MIN_COS_DESC:-0.0}"
  TRACK3_LOCOM_SAMPLE_TOKENS="${TRACK3_LOCOM_SAMPLE_TOKENS:-1024}"
  TRACK3_LOCOM_LOG_STEPS=0,1,2,10,50,125,250,500,750,1000,1125,1200,1225,1250,1375,1500,1600,1625,1650,1700,1750,1800,1900,2000
  TRACK3_LOCOM_DIAG_STEPS=1,3,5
  TRACK3_LOCOM_DIAG_MAX_LAYERS="${TRACK3_LOCOM_DIAG_MAX_LAYERS:-12}"
  TRACK3_LOCOM_PREP_MAX_STATS="${TRACK3_LOCOM_PREP_MAX_STATS:-12}"
  TRACK3_LOCOM_APPLY_MAX_STATS="${TRACK3_LOCOM_APPLY_MAX_STATS:-12}"
  TRACK3_CHECKPOINT_DIR="${ckpt_dir}"
  SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-25}"
  NPROC_PER_NODE="${NPROC_PER_NODE:-1}"
)

run_prefix() {
  local log_file="${log_dir}/${prefix_label}.log"
  echo "===== prefix ${prefix_label} $(date -u +%Y-%m-%dT%H:%M:%SZ) =====" | tee -a "${status}"
  env \
    "${common_env[@]}" \
    TRACK3_LOCOM_ENABLED=0 \
    TRACK3_LOCOM_ACTIVE_WINDOWS= \
    TRACK3_LOCOM_END_STEP="${train_steps}" \
    TRACK3_LOCOM_SCALE_MODE=param \
    TRACK3_LOCOM_ACT_TARGET=0.0 \
    TRACK3_LOCOM_NORM_CAP=0.0 \
    TRACK3_LOCOM_NORM_TARGET=0.0 \
    TRACK3_LOCOM_NORM_TO_BASE=0 \
    TRACK3_CHECKPOINT_PREFIX="${prefix_label}" \
    TRACK3_CHECKPOINT_STEPS=1200,1600,1800,2000 \
    TRACK3_GENERATED_SCRIPT="/tmp/${prefix_label}.py" \
    bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${log_file}"
}

run_resume_lane() {
  local onset="$1"
  local label="track3_locom_actbase050_resume${onset}_seed${seed_offset}_to${train_steps}"
  local checkpoint="${ckpt_dir}/${prefix_label}_seed${seed}_step${onset}.pt"
  local log_file="${log_dir}/${label}.log"
  if [[ ! -f "${checkpoint}" ]]; then
    echo "missing checkpoint ${checkpoint}" | tee -a "${status}"
    return 1
  fi
  echo "===== ${label} $(date -u +%Y-%m-%dT%H:%M:%SZ) =====" | tee -a "${status}"
  env \
    "${common_env[@]}" \
    TRACK3_LOCOM_ENABLED=1 \
    TRACK3_LOCOM_ACTIVE_WINDOWS="${onset}:${train_steps}" \
    TRACK3_LOCOM_END_STEP="${train_steps}" \
    TRACK3_LOCOM_SCALE_MODE=act_base \
    TRACK3_LOCOM_ACT_TARGET="${TRACK3_LOCOM_ACT_TARGET:-0.50}" \
    TRACK3_LOCOM_NORM_CAP="${TRACK3_LOCOM_NORM_CAP:-1.0}" \
    TRACK3_LOCOM_NORM_TARGET=0.0 \
    TRACK3_LOCOM_NORM_TO_BASE=0 \
    TRACK3_RESUME_CHECKPOINT="${checkpoint}" \
    TRACK3_RESUME_LOAD_OPTIMIZERS=1 \
    TRACK3_RESUME_RESTORE_RNG=1 \
    TRACK3_RESUME_ADVANCE_DATA=1 \
    TRACK3_CHECKPOINT_PREFIX="${label}" \
    TRACK3_CHECKPOINT_STEPS=1800,2000 \
    TRACK3_GENERATED_SCRIPT="/tmp/${label}.py" \
    bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${log_file}"
}

run_prefix
run_resume_lane 1200
run_resume_lane 1600

control_log="${log_dir}/${prefix_label}.log"
on1200_log="${log_dir}/track3_locom_actbase050_resume1200_seed${seed_offset}_to${train_steps}.log"
on1600_log="${log_dir}/track3_locom_actbase050_resume1600_seed${seed_offset}_to${train_steps}.log"

python3 tools/analyze_track3_locom_lr_slope.py \
  --steps 1000,1200,1250,1375,1500,1600,1700,1800,1900,2000 \
  --target-step 3000 \
  --target-loss 3.28 \
  "${log_dir}" | tee "${log_dir}/delayed_resume_onset_slope.md" || true

python3 tools/analyze_locom_apply_scale.py \
  "${on1200_log}" "${on1600_log}" | tee "${log_dir}/delayed_resume_onset_apply_scale.md" || true

python3 tools/analyze_locom_kdiag.py \
  "${on1200_log}" "${on1600_log}" | tee "${log_dir}/delayed_resume_onset_kdiag.md" || true

python3 tools/analyze_track3_locom_prefix_effect_size.py \
  --active "${on1200_log}" \
  --control "${control_log}" \
  --k 5 \
  --decision-step "${train_steps}" \
  --material-gain 0.001 \
  | tee "${log_dir}/delayed_resume_onset_1200_effect.md" || true

python3 tools/analyze_track3_locom_prefix_effect_size.py \
  --active "${on1600_log}" \
  --control "${control_log}" \
  --k 5 \
  --decision-step "${train_steps}" \
  --material-gain 0.001 \
  | tee "${log_dir}/delayed_resume_onset_1600_effect.md" || true

echo "done delayed_locom_resume_onset $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${status}"
