#!/usr/bin/env bash
set -euo pipefail

steps="${SCREEN_STEPS:-60}"
val_every="${SCREEN_VAL_EVERY:-20}"
warmup="${SCREEN_WARMUP:-0,1,8,18,19,20,21,24,38,39,40,41,48,58,59,60}"
log_path="${LOG_PATH:-.opencode/newtonv_fullv_layers0_1_norminverse_nonorm_screen${steps}.log}"
cache_dir="${TORCHINDUCTOR_CACHE_DIR:-${HOME}/.cache/torchinductor-speedrun-newtonv}"
nproc="${NPROC_PER_NODE:-1}"

python3 tools/make_train_screen.py \
  --source train_gpt.py \
  --output train_gpt_screen.py \
  --steps "${steps}" \
  --extension 0 \
  --val-every "${val_every}" \
  --warmup "${warmup}"

mkdir -p "$(dirname "${log_path}")"

PYTHONUNBUFFERED=1 \
TORCHINDUCTOR_CACHE_DIR="${cache_dir}" \
LOCO_FULL_SURFACES="${LOCO_FULL_SURFACES:-v}" \
LOCO_DIAG_ATTN_LAYERS="${LOCO_DIAG_ATTN_LAYERS:-0-1}" \
LOCO_FULL_END_STEP="${LOCO_FULL_END_STEP:-100}" \
LOCO_FULL_FILTER="${LOCO_FULL_FILTER:-norminverse}" \
LOCO_FULL_NORM_RESTORE="${LOCO_FULL_NORM_RESTORE:-0}" \
LOCO_FULL_LOCAL_STATS="${LOCO_FULL_LOCAL_STATS:-1}" \
LOCO_FULL_REFRESH_INTERVAL="${LOCO_FULL_REFRESH_INTERVAL:-8}" \
LOCO_FULL_APPLY_INTERVAL="${LOCO_FULL_APPLY_INTERVAL:-1}" \
LOCO_FULL_RIDGE_REL="${LOCO_FULL_RIDGE_REL:-0.03}" \
LOCO_FULL_BLEND_MAX="${LOCO_FULL_BLEND_MAX:-0.25}" \
LOCO_FULL_PRECOND_DTYPE="${LOCO_FULL_PRECOND_DTYPE:-fp32}" \
torchrun --standalone --nproc_per_node="${nproc}" train_gpt_screen.py 2>&1 | tee "${log_path}"
