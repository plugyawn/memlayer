#!/usr/bin/env bash
set -euo pipefail
cd "/root/wr-track3-locom-20260606"
export PATH="/root/venv/bin:$PATH"
export PYTHONUNBUFFERED=1
export HF_HOME=/root/.cache/huggingface
export XDG_CACHE_HOME=/root/.cache/xdg
export TRITON_CACHE_DIR=/root/.cache/triton
export TORCHINDUCTOR_CACHE_DIR=/root/.cache/torchinductor-track3-kdiag
logdir="/root/prime_track3_kdiag_logs"
label="track3_kdiag_post-true-k10-lr2e4-active-poscos-coldp2_115017"
echo "profile_start post-true-k10-lr2e4-active-poscos-coldp2 label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${logdir}/sequence.status"
TRACK3_KDIAG_PROFILE=post-true-k10-lr2e4-active-poscos \
TRACK3_KDIAG_LABEL="${label}" \
TRACK3_KDIAG_LOG_DIR="${logdir}" \
TRACK3_TRAIN_STEPS=3000 \
TRACK3_COOLDOWN_FRAC=1.0 \
TRACK3_LR_SCHEDULE=power \
TRACK3_LR_POWER=2.0 \
TRACK3_LOCOM_NORM_TARGET=0.0 \
TRACK3_LOCOM_NORM_TO_BASE=0 \
TRACK3_LOCOM_ACTIVE_WINDOWS=0:3000 \
TRACK3_LOCOM_END_STEP=3000 \
TRACK3_LOCOM_LOG_STEPS=1600,1625,1650,1675,1700,1725,1750,1775,1800,1900,2000,2125,2250,2400,2500,2625,2750,2875,3000 \
SCREEN_VAL_EVERY=25 \
bash tools/run_track3_locom_kdiag_probe.sh
echo "profile_done post-true-k10-lr2e4-active-poscos-coldp2 label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${logdir}/sequence.status"
