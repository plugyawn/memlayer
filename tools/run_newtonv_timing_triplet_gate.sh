#!/usr/bin/env bash
set -euo pipefail

steps="${SCREEN_STEPS:-120}"
val_every="${SCREEN_VAL_EVERY:-0}"
warmup="${SCREEN_WARMUP:-0,1,8,18,19,20,21,24,38,39,40,41,48,58,59,60}"
variant="${NEWTONV_VARIANT:-baseline}"
layers="${LOCO_DIAG_ATTN_LAYERS:-all}"
windows="${LOCO_FULL_WINDOWS:-0-48}"
cache_dir="${TORCHINDUCTOR_CACHE_DIR:-${HOME}/.cache/torchinductor-speedrun-newtonv}"
nproc="${NPROC_PER_NODE:-1}"
log_path="${LOG_PATH:-.opencode/newtonv_timing_${variant}_screen${steps}.log}"

python3 tools/make_train_screen.py \
  --source train_gpt.py \
  --output train_gpt_screen.py \
  --steps "${steps}" \
  --extension 0 \
  --val-every "${val_every}" \
  --warmup "${warmup}"

mkdir -p "$(dirname "${log_path}")"

base_env=(
  PYTHONUNBUFFERED=1
  TORCHINDUCTOR_CACHE_DIR="${cache_dir}"
)

case "${variant}" in
  baseline)
    env -u LOCO_DIAG \
      -u LOCO_DIAG_SURFACES \
      -u LOCO_FULL_SURFACES \
      "${base_env[@]}" \
      torchrun --standalone --nproc_per_node="${nproc}" train_gpt_screen.py 2>&1 | tee "${log_path}"
    ;;
  noop)
    env "${base_env[@]}" \
      LOCO_FULL_SURFACES="${LOCO_FULL_SURFACES:-v}" \
      LOCO_DIAG_ATTN_LAYERS="${layers}" \
      LOCO_FULL_WINDOWS="${windows}" \
      LOCO_FULL_NOOP=1 \
      LOCO_FULL_FILTER="${LOCO_FULL_FILTER:-inverse}" \
      LOCO_FULL_NORM_RESTORE="${LOCO_FULL_NORM_RESTORE:-1}" \
      LOCO_FULL_LOCAL_STATS="${LOCO_FULL_LOCAL_STATS:-1}" \
      LOCO_FULL_REFRESH_INTERVAL="${LOCO_FULL_REFRESH_INTERVAL:-8}" \
      LOCO_FULL_RIDGE_REL="${LOCO_FULL_RIDGE_REL:-0.03}" \
      torchrun --standalone --nproc_per_node="${nproc}" train_gpt_screen.py 2>&1 | tee "${log_path}"
    ;;
  active)
    env "${base_env[@]}" \
      LOCO_FULL_SURFACES="${LOCO_FULL_SURFACES:-v}" \
      LOCO_DIAG_ATTN_LAYERS="${layers}" \
      LOCO_FULL_WINDOWS="${windows}" \
      LOCO_FULL_FILTER="${LOCO_FULL_FILTER:-inverse}" \
      LOCO_FULL_NORM_RESTORE="${LOCO_FULL_NORM_RESTORE:-1}" \
      LOCO_FULL_LOCAL_STATS="${LOCO_FULL_LOCAL_STATS:-1}" \
      LOCO_FULL_REFRESH_INTERVAL="${LOCO_FULL_REFRESH_INTERVAL:-8}" \
      LOCO_FULL_APPLY_INTERVAL="${LOCO_FULL_APPLY_INTERVAL:-1}" \
      LOCO_FULL_RIDGE_REL="${LOCO_FULL_RIDGE_REL:-0.03}" \
      LOCO_FULL_BLEND_MAX="${LOCO_FULL_BLEND_MAX:-0.25}" \
      LOCO_FULL_PRECOND_DTYPE="${LOCO_FULL_PRECOND_DTYPE:-fp32}" \
      LOCO_FULL_POLAR_ITERS="${LOCO_FULL_POLAR_ITERS:-5}" \
      torchrun --standalone --nproc_per_node="${nproc}" train_gpt_screen.py 2>&1 | tee "${log_path}"
    ;;
  *)
    echo "NEWTONV_VARIANT must be baseline, noop, or active; got ${variant}" >&2
    exit 2
    ;;
esac
