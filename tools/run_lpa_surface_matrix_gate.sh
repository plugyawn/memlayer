#!/usr/bin/env bash
set -euo pipefail

# Fixed-control surface screen for state-decoupled LocoProp-style corrections.
# This intentionally reuses the paired replay harness, so each surface gets:
#   noop -> active -> noop2
# from the same saved initial state.

steps="${LPA_STEPS:-${SCREEN_STEPS:-80}}"
val_every="${LPA_VAL_EVERY:-${SCREEN_VAL_EVERY:-40}}"
layers="${LPA_LAYERS:-0-1}"
collect="${LPA_COLLECT_WINDOWS:-0-64}"
windows="${LPA_WINDOWS:-48-64}"
refresh="${LPA_REFRESH_INTERVAL:-16}"
ema="${LPA_EMA_BETA:-0.8}"
ridge="${LPA_RIDGE_REL:-0.2}"
blend="${LPA_BLEND_MAX:-0.05}"
blend_steps="${LPA_BLEND_STEPS:-16}"
finite_t="${LPA_FINITE_T:-2.0}"
clip="${LPA_POWER_CLIP:-2.0}"
norm_to_base="${LPA_NORM_TO_BASE:-1}"
component="${LPA_COMPONENT:-full}"
paired_cases="${LPA_PAIRED_CASES:-noop,active,noop2}"
surfaces_csv="${LPA_SURFACE_MATRIX:-v,qk,o,mlp_fc}"
label_prefix="${LPA_SUITE_LABEL_PREFIX:-lpa_surface_matrix}"

IFS=',' read -ra surfaces <<< "${surfaces_csv}"

for surface in "${surfaces[@]}"; do
  surface="$(echo "${surface}" | xargs)"
  [[ -n "${surface}" ]] || continue
  surface_label="${surface//[^0-9A-Za-z]/_}"
  echo "===== LPA_SURFACE_MATRIX_START ${surface} $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  NEWTONV_SUITE=locoprop_additive_paired \
  NEWTONV_SUITE_LABEL="${label_prefix}_${surface_label}" \
  LPA_SURFACE="${surface}" \
  LPA_STEPS="${steps}" \
  LPA_VAL_EVERY="${val_every}" \
  LPA_LAYERS="${layers}" \
  LPA_COLLECT_WINDOWS="${collect}" \
  LPA_WINDOWS="${windows}" \
  LPA_REFRESH_INTERVAL="${refresh}" \
  LPA_EMA_BETA="${ema}" \
  LPA_RIDGE_REL="${ridge}" \
  LPA_BLEND_MAX="${blend}" \
  LPA_BLEND_STEPS="${blend_steps}" \
  LPA_FILTER=finite \
  LPA_FINITE_T="${finite_t}" \
  LPA_POWER_CLIP="${clip}" \
  LPA_NORM_TO_BASE="${norm_to_base}" \
  LPA_COMPONENT="${component}" \
  LPA_PAIRED_CASES="${paired_cases}" \
  LPA_LOG_PRECOND="${LPA_LOG_PRECOND:-1}" \
  LPA_LOG_PRECOND_DETAIL="${LPA_LOG_PRECOND_DETAIL:-0}" \
  LPA_LOG_STEPS="${LPA_LOG_STEPS:-48,50,56,64,80,100,120}" \
  bash tools/run_newtonv_experiment_suite.sh
  echo "===== LPA_SURFACE_MATRIX_END ${surface} $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
done
