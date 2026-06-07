#!/usr/bin/env bash
set -euo pipefail

repo="${TRACK3_REPO:-/root/wr-track3-locom-20260606}"
log_dir="${TRACK3_LOG_DIR:-/root/prime_track3_actscale_from1600_logs}"
ckpt_dir="${TRACK3_CHECKPOINT_DIR:-/root/.cache/track3_checkpoints}"
resume_ckpt="${TRACK3_RESUME_CHECKPOINT:-${ckpt_dir}/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
label="${TRACK3_KDIAG_LABEL:-track3_actbase100_cap100_from1600_seed3710_to2400}"

mkdir -p "${log_dir}" "${ckpt_dir}"
cd "${repo}"

if [[ -f /root/venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source /root/venv/bin/activate
elif [[ -f /home/ubuntu/venv/bin/activate ]]; then
  # shellcheck disable=SC1091
  source /home/ubuntu/venv/bin/activate
fi

if [[ ! -f "${resume_ckpt}" ]]; then
  echo "missing resume checkpoint: ${resume_ckpt}" >&2
  exit 2
fi

logfile="${log_dir}/${label}.log"
status="${log_dir}/sequence.status"

echo "===== ${label} $(date -u +%Y-%m-%dT%H:%M:%SZ) =====" | tee -a "${status}"
env \
  TRACK3_SOURCE=records/track_3_optimization/train_gpt_simple.py \
  TRACK3_NUM_TRIALS=1 \
  TRACK3_TARGET_LOSS=3.28 \
  TRACK3_MBS=16 \
  TRACK3_SEED_BASE=0 \
  TRACK3_SEED_OFFSET=3710 \
  TRACK3_RESUME_CHECKPOINT="${resume_ckpt}" \
  TRACK3_RESUME_ADVANCE_DATA=1 \
  TRACK3_RESUME_RESTORE_RNG=1 \
  TRACK3_RESUME_LOAD_OPTIMIZERS=1 \
  TRACK3_TRAIN_STEPS=2400 \
  TRACK3_COOLDOWN_FRAC=1.0 \
  TRACK3_LR_SCHEDULE=power \
  TRACK3_LR_POWER=2.0 \
  TRACK3_LR_SCHEDULE_STEPS=3000 \
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
  TRACK3_LOCOM_ENABLED=1 \
  TRACK3_LOCOM_ACTIVE_WINDOWS=1600:2200 \
  TRACK3_LOCOM_END_STEP=2200 \
  TRACK3_LOCOM_LAYERS=all \
  TRACK3_LOCOM_SURFACE=fc \
  TRACK3_LOCOM_STEPS=5 \
  TRACK3_LOCOM_INNER_LR=2e-4 \
  TRACK3_LOCOM_PROX=0.1 \
  TRACK3_LOCOM_TARGET_SPACE=post \
  TRACK3_LOCOM_TRUE_POST_GRAD=1 \
  TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1 \
  TRACK3_LOCOM_MIN_COS_DESC=0.0 \
  TRACK3_LOCOM_SAMPLE_TOKENS=1024 \
  TRACK3_LOCOM_SCALE_MODE=act_base \
  TRACK3_LOCOM_ACT_TARGET=1.0 \
  TRACK3_LOCOM_NORM_CAP=1.0 \
  TRACK3_LOCOM_NORM_TARGET=0.0 \
  TRACK3_LOCOM_NORM_TO_BASE=0 \
  TRACK3_LOCOM_LOG_STEPS=1600,1625,1650,1700,1750,1800,1875,2000,2125,2200,2400 \
  TRACK3_LOCOM_DIAG_STEPS=1,3,5 \
  TRACK3_LOCOM_DIAG_MAX_LAYERS=4 \
  TRACK3_CHECKPOINT_DIR="${ckpt_dir}" \
  TRACK3_CHECKPOINT_PREFIX="${label}" \
  TRACK3_CHECKPOINT_STEPS=1800,2000,2125,2200,2400 \
  SCREEN_VAL_EVERY=25 \
  NPROC_PER_NODE=1 \
  bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${logfile}"

python3 tools/analyze_track3_locom_lr_slope.py \
  --steps 1600,1800,2000,2125,2200,2400 \
  --target-step 3000 \
  --target-loss 3.28 \
  "${log_dir}" | tee "${log_dir}/lr_slope.md" || true

echo "done ${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${status}"
