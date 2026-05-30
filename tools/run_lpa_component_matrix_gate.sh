#!/usr/bin/env bash
set -euo pipefail

# Fixed-control component screen for state-decoupled LocoProp-style corrections.
# This holds the surface fixed and sweeps how the local correction is decomposed
# relative to the base NorMuon update:
#   full, parallel, orthogonal.
#
# LPA_COMPONENT_MATRIX accepts comma-separated entries:
#   parallel
#   orthogonal:0.02
#   orthogonal:0.05
#
# An entry without a blend uses LPA_BLEND_MAX.

steps="${LPA_STEPS:-${SCREEN_STEPS:-80}}"
val_every="${LPA_VAL_EVERY:-${SCREEN_VAL_EVERY:-40}}"
surface="${LPA_SURFACE:-v}"
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
paired_cases="${LPA_PAIRED_CASES:-noop,active,noop2}"
components_csv="${LPA_COMPONENT_MATRIX:-parallel:0.05,orthogonal:0.02,orthogonal:0.05}"
label_prefix="${LPA_SUITE_LABEL_PREFIX:-lpa_component_matrix}"

IFS=',' read -ra components <<< "${components_csv}"

for entry in "${components[@]}"; do
  entry="$(echo "${entry}" | xargs)"
  [[ -n "${entry}" ]] || continue

  component="${entry%%:*}"
  case_blend="${blend}"
  if [[ "${entry}" == *:* ]]; then
    case_blend="${entry#*:}"
  fi
  component="$(echo "${component}" | xargs)"
  case_blend="$(echo "${case_blend}" | xargs)"
  [[ -n "${component}" ]] || continue
  [[ -n "${case_blend}" ]] || case_blend="${blend}"

  blend_label="${case_blend//./p}"
  blend_label="${blend_label//-/m}"

  echo "===== LPA_COMPONENT_MATRIX_START ${surface} ${component} blend=${case_blend} $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  NEWTONV_SUITE=locoprop_additive_paired \
  NEWTONV_SUITE_LABEL="${label_prefix}_${surface}_${component}_b${blend_label}" \
  LPA_SURFACE="${surface}" \
  LPA_STEPS="${steps}" \
  LPA_VAL_EVERY="${val_every}" \
  LPA_LAYERS="${layers}" \
  LPA_COLLECT_WINDOWS="${collect}" \
  LPA_WINDOWS="${windows}" \
  LPA_REFRESH_INTERVAL="${refresh}" \
  LPA_EMA_BETA="${ema}" \
  LPA_RIDGE_REL="${ridge}" \
  LPA_BLEND_MAX="${case_blend}" \
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
  echo "===== LPA_COMPONENT_MATRIX_END ${surface} ${component} blend=${case_blend} $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
done
