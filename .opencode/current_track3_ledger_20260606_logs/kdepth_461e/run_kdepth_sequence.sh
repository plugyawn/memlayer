#!/usr/bin/env bash
set -euo pipefail

repo=/root/wr-track3-locom-20260606
logdir=/root/prime_track3_kdepth_logs

export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export HF_HOME=/root/.cache/huggingface
export XDG_CACHE_HOME=/root/.cache/xdg
export TRITON_CACHE_DIR=/root/.cache/triton
export TORCHINDUCTOR_CACHE_DIR=/root/.cache/torchinductor-track3-kdepth

mkdir -p "${logdir}"
cd "${repo}"

if [[ ! -x /root/venv/bin/python ]]; then
  apt-get update
  apt-get install -y --no-install-recommends python3 python3-dev python3-venv python3-pip build-essential git ca-certificates curl
  python3 -m venv /root/venv
fi

source /root/venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q --index-url https://download.pytorch.org/whl/cu126 torch==2.7.1
python -m pip install -q numpy tqdm huggingface-hub typing-extensions setuptools

python data/cached_fineweb10B.py 20 > "${logdir}/cache_fineweb.log" 2>&1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader > "${logdir}/gpu.txt" 2>&1 || true

run_lane() {
  local name="$1"
  local local_steps="$2"
  local inner_lr="$3"
  local label="track3_kdepth_${name}_$(date -u +%H%M%S)"

  echo "lane_start ${name} K=${local_steps} inner_lr=${inner_lr} label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${logdir}/sequence.status"
  TRACK3_KDIAG_PROFILE=post-true-k10-lr2e4-active-poscos \
  TRACK3_KDIAG_LABEL="${label}" \
  TRACK3_KDIAG_LOG_DIR="${logdir}" \
  TRACK3_TRAIN_STEPS=1800 \
  TRACK3_NUM_TRIALS=1 \
  TRACK3_TARGET_LOSS=3.28 \
  TRACK3_SOURCE=records/track_3_optimization/train_gpt_simple.py \
  TRACK3_MBS=16 \
  TRACK3_SEED_BASE=0 \
  TRACK3_SEED_OFFSET=3710 \
  TRACK3_RESUME_CHECKPOINT=/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt \
  TRACK3_RESUME_ADVANCE_DATA=1 \
  TRACK3_RESUME_RESTORE_RNG=1 \
  TRACK3_RESUME_LOAD_OPTIMIZERS=1 \
  TRACK3_CHECKPOINT_STEPS=1800 \
  TRACK3_CHECKPOINT_DIR=/root/.cache/track3_checkpoints \
  TRACK3_CHECKPOINT_PREFIX="track3_kdepth_${name}" \
  TRACK3_CHECKPOINT_EXIT_AFTER=0 \
  TRACK3_COOLDOWN_FRAC=1.0 \
  TRACK3_LR_SCHEDULE=power \
  TRACK3_LR_POWER=2.0 \
  TRACK3_LR_SCHEDULE_STEPS=3000 \
  TRACK3_LR_MIN_ETA=0.0 \
  TRACK3_LR_SWITCH_STEP=-1 \
  TRACK3_LR_AFTER_SWITCH= \
  TRACK3_LR_BUMP_WINDOWS= \
  TRACK3_LOCOM_ENABLED=1 \
  TRACK3_LOCOM_LAYERS=all \
  TRACK3_LOCOM_STEPS="${local_steps}" \
  TRACK3_LOCOM_INNER_LR="${inner_lr}" \
  TRACK3_LOCOM_TARGET_SPACE=post \
  TRACK3_LOCOM_TRUE_POST_GRAD=1 \
  TRACK3_LOCOM_MIN_COS_DESC=0.0 \
  TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1 \
  TRACK3_LOCOM_ALPHA=1.0 \
  TRACK3_LOCOM_SAMPLE_TOKENS=1024 \
  TRACK3_LOCOM_NORM_TARGET=0.0 \
  TRACK3_LOCOM_NORM_TO_BASE=0 \
  TRACK3_LOCOM_NORM_CAP=0.20 \
  TRACK3_LOCOM_ACTIVE_WINDOWS=0:1800 \
  TRACK3_LOCOM_END_STEP=1800 \
  TRACK3_LOCOM_LOG_STEPS=1600,1625,1650,1675,1700,1725,1750,1775,1800 \
  TRACK3_LOCOM_DIAG_STEPS=1,2,4,5,8,10 \
  TRACK3_LOCOM_DIAG_MAX_LAYERS=12 \
  SCREEN_VAL_EVERY=25 \
  NPROC_PER_NODE=1 \
  bash tools/run_track3_locom_kdiag_probe.sh
  echo "lane_done ${name} label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${logdir}/sequence.status"
}

run_lane k10-lr2e4 10 2e-4
run_lane k8-lr2e4 8 2e-4
run_lane k5-lr2e4 5 2e-4
run_lane k5-lr3e4 5 3e-4
touch "${logdir}/DONE"
