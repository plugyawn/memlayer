#!/usr/bin/env bash
set -euo pipefail

steps="${SCREEN_STEPS:-80}"
val_every="${SCREEN_VAL_EVERY:-40}"
prefix="${SOFTPOLAR_RUN_PREFIX:-softpolar_pr291_$(date -u +%Y%m%dT%H%M%SZ)}"
layers="${LOCO_DIAG_MLP_LAYERS:-0-1}"
attn_layers="${LOCO_DIAG_ATTN_LAYERS:-${layers}}"
windows="${LOCO_SOFT_POLAR_WINDOWS:-48-64}"
log_dir="${SOFTPOLAR_LOG_DIR:-.opencode}"

mkdir -p "${log_dir}"

run_case() {
  local name="$1"
  local surfaces="$2"
  local log_path="${log_dir}/${prefix}_${name}_screen${steps}.log"
  echo "===== SOFTPOLAR_PR291_CASE_START ${name} surfaces=${surfaces} log=${log_path} ====="
  LOG_PATH="${log_path}" \
  SCREEN_STEPS="${steps}" \
  SCREEN_VAL_EVERY="${val_every}" \
  LOCO_SOFT_POLAR_IMPL="pr291" \
  LOCO_SOFT_POLAR_ALPHA="${LOCO_SOFT_POLAR_ALPHA:-0.9}" \
  LOCO_SOFT_POLAR_POWER="${LOCO_SOFT_POLAR_POWER:-0.1}" \
  LOCO_SOFT_POLAR_SURFACES="${surfaces}" \
  LOCO_SOFT_POLAR_WINDOWS="${windows}" \
  LOCO_DIAG_MLP_LAYERS="${layers}" \
  LOCO_DIAG_ATTN_LAYERS="${attn_layers}" \
  bash tools/run_softpolar_mlpfc_gate.sh
  echo "===== SOFTPOLAR_PR291_CASE_END ${name} ====="
}

run_case "mlpfc" "mlp_fc"
run_case "all_l01" "qk,v,o,mlp_fc"
