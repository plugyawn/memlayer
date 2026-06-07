#!/usr/bin/env bash
set -euo pipefail

repo=/root/wr-track3-locom-20260606
logdir=/root/prime_track3_suffix_bridge_logs
ckpt_dir=/root/.cache/track3_checkpoints

export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export HF_HOME=/root/.cache/huggingface
export XDG_CACHE_HOME=/root/.cache/xdg
export TRITON_CACHE_DIR=/root/.cache/triton
export TORCHINDUCTOR_CACHE_DIR=/root/.cache/torchinductor-track3-suffixbridge

mkdir -p "${logdir}" "${ckpt_dir}"
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

TRACK3_SUFFIX_CHECKPOINT=/root/.cache/track3_checkpoints/track3_noloco_ckpt2125_seed3710_seed3710_step2125.pt \
TRACK3_SUFFIX_FROM_STEP=2125 \
TRACK3_SUFFIX_LOG_DIR="${logdir}" \
TRACK3_CHECKPOINT_DIR="${ckpt_dir}" \
TRACK3_SUFFIX_LANES=bump150_2250_2650,blend_p15_2250_2650 \
TRACK3_TRAIN_STEPS=2400 \
TRACK3_GATE_STEP=2400 \
TRACK3_GATE_LOSS=3.3365 \
TRACK3_ANALYZE_STEPS=2125,2250,2400 \
bash tools/run_track3_suffix_bridge_probe.sh

touch "${logdir}/DONE"
