#!/usr/bin/env bash
set -euo pipefail
repo=/root/wr-track3-locom-20260606
logdir=/root/prime_track3_kdiag_logs
profile=post-true-k10-lr2e4-active-poscos
label=track3_truepost3000_${profile}_$(date -u +%H%M%S)

export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export HF_HOME=/root/.cache/huggingface
export XDG_CACHE_HOME=/root/.cache/xdg
export TRITON_CACHE_DIR=/root/.cache/triton
export TORCHINDUCTOR_CACHE_DIR=/root/.cache/torchinductor-track3-truepost3000

mkdir -p "$logdir"
cd "$repo"

if [[ ! -x /root/venv/bin/python ]]; then
  apt-get update
  apt-get install -y --no-install-recommends python3 python3-dev python3-venv python3-pip build-essential git ca-certificates curl
  python3 -m venv /root/venv
fi

source /root/venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q --index-url https://download.pytorch.org/whl/cu126 torch==2.7.1
python -m pip install -q numpy tqdm huggingface-hub typing-extensions

python data/cached_fineweb10B.py 20 > "$logdir/cache_fineweb.log" 2>&1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader > "$logdir/gpu.txt" 2>&1 || true

echo "$label" > "$logdir/active_screen.label"
echo "profile_start $profile label=$label $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$logdir/sequence.status"
TRACK3_KDIAG_PROFILE="$profile" \
TRACK3_KDIAG_LABEL="$label" \
TRACK3_KDIAG_LOG_DIR="$logdir" \
TRACK3_TRAIN_STEPS=3000 \
TRACK3_LOCOM_ACTIVE_WINDOWS=0:3000 \
TRACK3_LOCOM_END_STEP=3000 \
TRACK3_LOCOM_LOG_STEPS=1600,1625,1750,1800,2000,2125,2250,2400,2500,2625,2750,2875,3000 \
SCREEN_VAL_EVERY=25 \
bash tools/run_track3_locom_kdiag_probe.sh

echo "profile_done $profile label=$label $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "$logdir/sequence.status"
touch "$logdir/DONE"
