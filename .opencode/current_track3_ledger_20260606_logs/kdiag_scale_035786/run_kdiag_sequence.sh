#!/usr/bin/env bash
set -euo pipefail

repo=/root/wr-track3-locom-20260606
logdir=/root/prime_track3_kdiag_logs
profiles_csv="post-true-k10-lr1e4-alpha0,post-true-k10-lr2e4-alpha0,post-true-k10-lr3e4-alpha0,post-true-k10-lr1e3-alpha0"

export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export HF_HOME=/root/.cache/huggingface
export XDG_CACHE_HOME=/root/.cache/xdg
export TRITON_CACHE_DIR=/root/.cache/triton
export TORCHINDUCTOR_CACHE_DIR=/root/.cache/torchinductor-track3-kdiag-scale

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
python -m pip install -q numpy tqdm huggingface-hub typing-extensions

python data/cached_fineweb10B.py 20 > "${logdir}/cache_fineweb.log" 2>&1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader > "${logdir}/gpu.txt" 2>&1 || true

IFS=',' read -r -a profiles <<< "${profiles_csv}"
for profile in "${profiles[@]}"; do
  profile="$(echo "${profile}" | xargs)"
  [[ -z "${profile}" ]] && continue
  label="track3_kdiag_${profile}_$(date -u +%H%M%S)"
  echo "profile_start ${profile} label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${logdir}/sequence.status"
  TRACK3_KDIAG_PROFILE="${profile}" \
  TRACK3_KDIAG_LABEL="${label}" \
  TRACK3_KDIAG_LOG_DIR="${logdir}" \
  bash tools/run_track3_locom_kdiag_probe.sh
  echo "profile_done ${profile} label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${logdir}/sequence.status"
done
touch "${logdir}/DONE"
