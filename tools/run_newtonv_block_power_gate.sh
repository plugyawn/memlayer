#!/usr/bin/env bash
set -euo pipefail

steps="${SCREEN_STEPS:-80}"
val_every="${SCREEN_VAL_EVERY:-20}"
warmup="${SCREEN_WARMUP:-0,1,8,18,19,20,21,24,38,39,40,41,48,58,59,60}"
layers="${LOCO_DIAG_ATTN_LAYERS:-all}"
windows="${LOCO_FULL_WINDOWS:-0-48}"
block_size="${LOCO_FULL_BLOCK_SIZE:-256}"
alpha="${LOCO_FULL_POWER_ALPHA:-0.75}"
filter="${LOCO_FULL_FILTER:-power}"
polar_iters="${LOCO_FULL_POLAR_ITERS:-4}"
label_layers="${layers//[^0-9A-Za-z]/_}"
label_windows="${windows//[^0-9A-Za-z]/_}"
log_path="${LOG_PATH:-.opencode/newtonv_${filter}_block${block_size}_a${alpha}_p${polar_iters}_layers${label_layers}_win${label_windows}_screen${steps}.log}"
cache_dir="${TORCHINDUCTOR_CACHE_DIR:-${HOME}/.cache/torchinductor-speedrun-newtonv}"
nproc="${NPROC_PER_NODE:-1}"
norm_restore_default=0
if [[ "${LOCO_FULL_METRIC_POLAR:-0}" != "1" && "${LOCO_FULL_FILTER:-power}" == "inverse" ]]; then
  norm_restore_default=1
fi

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
LOCO_DIAG_ATTN_LAYERS="${layers}" \
LOCO_FULL_WINDOWS="${windows}" \
LOCO_FULL_FILTER="${filter}" \
LOCO_FULL_METRIC_POLAR="${LOCO_FULL_METRIC_POLAR:-0}" \
LOCO_FULL_BLOCK_SIZE="${block_size}" \
LOCO_FULL_POWER_ALPHA="${alpha}" \
LOCO_FULL_POWER_CLIP="${LOCO_FULL_POWER_CLIP:-2.0}" \
LOCO_FULL_FINITE_T="${LOCO_FULL_FINITE_T:-2.0}" \
LOCO_FULL_SHRINK_ONLY="${LOCO_FULL_SHRINK_ONLY:-0}" \
LOCO_FULL_STATIC_NORM="${LOCO_FULL_STATIC_NORM:-1}" \
LOCO_FULL_NORM_RESTORE="${LOCO_FULL_NORM_RESTORE:-${norm_restore_default}}" \
LOCO_FULL_LOCAL_STATS="${LOCO_FULL_LOCAL_STATS:-1}" \
LOCO_FULL_REFRESH_INTERVAL="${LOCO_FULL_REFRESH_INTERVAL:-8}" \
LOCO_FULL_APPLY_INTERVAL="${LOCO_FULL_APPLY_INTERVAL:-1}" \
LOCO_FULL_RIDGE_REL="${LOCO_FULL_RIDGE_REL:-0.03}" \
LOCO_FULL_BLEND_MAX="${LOCO_FULL_BLEND_MAX:-0.25}" \
LOCO_FULL_BLEND_STEPS="${LOCO_FULL_BLEND_STEPS:-100}" \
LOCO_FULL_PRECOND_DTYPE="${LOCO_FULL_PRECOND_DTYPE:-fp32}" \
LOCO_FULL_POLAR_ITERS="${polar_iters}" \
torchrun --standalone --nproc_per_node="${nproc}" train_gpt_screen.py 2>&1 | tee "${log_path}"
