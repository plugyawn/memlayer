#!/usr/bin/env bash
set -euo pipefail

steps="${SCREEN_STEPS:-80}"
val_every="${SCREEN_VAL_EVERY:-40}"
warmup="${SCREEN_WARMUP:-0,1,8,18,19,20,21,24,38,39,40,41,48,58,59,60,64,78,79,80,81}"
layers="${LOCO_DIAG_MLP_LAYERS:-0-1}"
attn_layers="${LOCO_DIAG_ATTN_LAYERS:-${layers}}"
surfaces="${LOCO_SOFT_POLAR_SURFACES:-mlp_fc}"
alpha="${LOCO_SOFT_POLAR_ALPHA:-0.5}"
eps="${LOCO_SOFT_POLAR_EPS:-1e-6}"
windows="${LOCO_SOFT_POLAR_WINDOWS:-48-64}"
label_layers="${layers//[^0-9A-Za-z]/_}"
label_surfaces="${surfaces//[^0-9A-Za-z]/_}"
label_windows="${windows//[^0-9A-Za-z]/_}"
label_alpha="${alpha//[^0-9A-Za-z]/_}"
label_eps="${eps//[^0-9A-Za-z]/_}"
log_path="${LOG_PATH:-.opencode/softpolar_${label_surfaces}_layers${label_layers}_win${label_windows}_a${label_alpha}_eps${label_eps}_screen${steps}.log}"
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
LOCO_SOFT_POLAR=1 \
LOCO_SOFT_POLAR_SURFACES="${surfaces}" \
LOCO_SOFT_POLAR_ALPHA="${alpha}" \
LOCO_SOFT_POLAR_EPS="${eps}" \
LOCO_SOFT_POLAR_WINDOWS="${windows}" \
LOCO_SOFT_POLAR_BLEND_MAX="${LOCO_SOFT_POLAR_BLEND_MAX:-1.0}" \
LOCO_SOFT_POLAR_BLEND_STEPS="${LOCO_SOFT_POLAR_BLEND_STEPS:-16}" \
LOCO_SOFT_POLAR_NORM_RESTORE="${LOCO_SOFT_POLAR_NORM_RESTORE:-1}" \
LOCO_DIAG_MLP_LAYERS="${layers}" \
LOCO_DIAG_ATTN_LAYERS="${attn_layers}" \
LOCO_FULL_LOG_PRECOND="${LOCO_FULL_LOG_PRECOND:-0}" \
LOCO_FULL_LOG_PRECOND_DETAIL="${LOCO_FULL_LOG_PRECOND_DETAIL:-0}" \
LOCO_DIAG_LOG_STEPS="${LOCO_DIAG_LOG_STEPS:-48,50,56,64,80,100,120}" \
torchrun --standalone --nproc_per_node="${nproc}" train_gpt_screen.py 2>&1 | tee "${log_path}"
