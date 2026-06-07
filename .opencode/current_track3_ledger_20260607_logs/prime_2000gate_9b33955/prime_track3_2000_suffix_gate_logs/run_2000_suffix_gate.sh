#!/usr/bin/env bash
set -euo pipefail

repo=/home/ubuntu/wr-track3-locom-20260606
logdir=/home/ubuntu/prime_track3_2000_suffix_gate_logs
home_dir=/home/ubuntu

export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export HF_HOME="${home_dir}/.cache/huggingface"
export XDG_CACHE_HOME="${home_dir}/.cache/xdg"
export TRITON_CACHE_DIR="${home_dir}/.cache/triton"
export TORCHINDUCTOR_CACHE_DIR="${home_dir}/.cache/torchinductor-track3-2000gate"

mkdir -p "${logdir}"
cd "${repo}"

sudo_cmd=()
if [[ "$(id -u)" != "0" ]]; then
  sudo_cmd=(sudo)
fi

if [[ ! -x "${home_dir}/venv/bin/python" ]]; then
  "${sudo_cmd[@]}" apt-get update
  "${sudo_cmd[@]}" apt-get install -y --no-install-recommends python3 python3-dev python3-venv python3-pip build-essential git ca-certificates curl
  python3 -m venv "${home_dir}/venv"
fi

source "${home_dir}/venv/bin/activate"
python -m pip install -q --upgrade pip
python -m pip install -q --index-url https://download.pytorch.org/whl/cu126 torch==2.7.1
python -m pip install -q numpy tqdm huggingface-hub typing-extensions setuptools

python data/cached_fineweb10B.py 20 > "${logdir}/cache_fineweb.log" 2>&1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader > "${logdir}/gpu.txt" 2>&1 || true

MODE=all \
TRACK3_2000_LOG_DIR="${logdir}" \
TRACK3_SUFFIX_STEPS=2125 \
TRACK3_SUFFIX_CHECKPOINT_STEPS=2125 \
TRACK3_SUFFIX_LANES=control,floor111,floor111_norm002,floor111_random002,floor111_norm005,floor111_random005,ramp111 \
TRACK3_CHECKPOINT_DIR=/home/ubuntu/.cache/track3_checkpoints \
TRACK3_BASE_CHECKPOINT=/home/ubuntu/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt \
SCREEN_VAL_EVERY=25 \
NPROC_PER_NODE=1 \
bash tools/run_track3_locom_2000_suffix_probe.sh

touch "${logdir}/DONE"
