#!/usr/bin/env bash
set -euo pipefail

suite="${NEWTONV_SUITE:-quick}"
label="${NEWTONV_SUITE_LABEL:-${suite}}"
timing_steps="${TIMING_STEPS:-80}"
timing_val_every="${TIMING_VAL_EVERY:-20}"
filter_steps="${FILTER_STEPS:-80}"
filter_val_every="${FILTER_VAL_EVERY:-20}"
raw_steps="${RAW_STEPS:-200}"
raw_val_every="${RAW_VAL_EVERY:-50}"
promote_steps="${PROMOTE_STEPS:-200}"
promote_val_every="${PROMOTE_VAL_EVERY:-50}"
perm_steps="${PERM_STEPS:-80}"
perm_val_every="${PERM_VAL_EVERY:-20}"
next_steps="${NEXT_STEPS:-120}"
next_val_every="${NEXT_VAL_EVERY:-40}"

run_case() {
  local name="$1"
  shift
  local log_path=".opencode/suite_${label}_${name}.log"
  echo "===== NEWTONV_CASE_START ${name} $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
  env LOG_PATH="${log_path}" "$@"
  echo "===== NEWTONV_CASE_END ${name} $(date -u +%Y-%m-%dT%H:%M:%SZ) ====="
}

run_timing_triplet() {
  run_case timing_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${timing_steps}" \
    SCREEN_VAL_EVERY="${timing_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case timing_noop \
    NEWTONV_VARIANT=noop \
    SCREEN_STEPS="${timing_steps}" \
    SCREEN_VAL_EVERY="${timing_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case timing_active_inverse \
    NEWTONV_VARIANT=active \
    SCREEN_STEPS="${timing_steps}" \
    SCREEN_VAL_EVERY="${timing_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_filter_ladder() {
  run_case block_power_a075 \
    SCREEN_STEPS="${filter_steps}" \
    SCREEN_VAL_EVERY="${filter_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh

  run_case block_power_a050 \
    LOCO_FULL_POWER_ALPHA=0.5 \
    SCREEN_STEPS="${filter_steps}" \
    SCREEN_VAL_EVERY="${filter_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh

  run_case block_power_shrink_only \
    LOCO_FULL_SHRINK_ONLY=1 \
    LOCO_FULL_STATIC_NORM=0 \
    SCREEN_STEPS="${filter_steps}" \
    SCREEN_VAL_EVERY="${filter_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh

  run_case block_finite_t2 \
    LOCO_FULL_FILTER=finite \
    SCREEN_STEPS="${filter_steps}" \
    SCREEN_VAL_EVERY="${filter_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh
}

run_polar4_priority() {
  run_case polar4_vall_win48 \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_WINDOWS=0-48 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${perm_steps}" \
    SCREEN_VAL_EVERY="${perm_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case polar4_v01_end100 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${perm_steps}" \
    SCREEN_VAL_EVERY="${perm_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_permutation_rest() {
  run_case perm_v01_win48 \
    LOCO_FULL_WINDOWS=0-48 \
    SCREEN_STEPS="${perm_steps}" \
    SCREEN_VAL_EVERY="${perm_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case perm_v01_win64 \
    LOCO_FULL_WINDOWS=0-64 \
    SCREEN_STEPS="${perm_steps}" \
    SCREEN_VAL_EVERY="${perm_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case perm_qk_win48 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk \
    LOCO_FULL_WINDOWS=0-48 \
    SCREEN_STEPS="${perm_steps}" \
    SCREEN_VAL_EVERY="${perm_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case perm_o_win48 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=o \
    LOCO_FULL_WINDOWS=0-48 \
    SCREEN_STEPS="${perm_steps}" \
    SCREEN_VAL_EVERY="${perm_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_permutation_queue() {
  run_polar4_priority
  run_permutation_rest
}

run_next_ladder() {
  run_case next_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case next_noop_vall_win32_80_p4 \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_WINDOWS=32-80 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case next_polar4_vall_win0_48 \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_WINDOWS=0-48 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case next_polar4_v01_end100 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case next_polar4_vall_win32_80 \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_WINDOWS=32-80 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case next_polar4_v01_win32_80 \
    LOCO_FULL_WINDOWS=32-80 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case next_polar4_v01_win48_112 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case next_qk_win32_80_p4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk \
    LOCO_FULL_WINDOWS=32-80 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case next_o_win32_80_p4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=o \
    LOCO_FULL_WINDOWS=32-80 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

case "${suite}" in
  timing)
    run_timing_triplet
    ;;
  filters)
    run_filter_ladder
    ;;
  quick)
    run_timing_triplet
    run_polar4_priority
    run_filter_ladder
    ;;
  raw200)
    run_case raw_v01_end100 \
      SCREEN_STEPS="${raw_steps}" \
      SCREEN_VAL_EVERY="${raw_val_every}" \
      bash tools/run_newtonv_raw_v01_gate.sh
    ;;
  promote)
    run_case promote_baseline \
      NEWTONV_VARIANT=baseline \
      SCREEN_STEPS="${promote_steps}" \
      SCREEN_VAL_EVERY="${promote_val_every}" \
      bash tools/run_newtonv_timing_triplet_gate.sh

    run_case promote_active_inverse_all_win48 \
      NEWTONV_VARIANT=active \
      SCREEN_STEPS="${promote_steps}" \
      SCREEN_VAL_EVERY="${promote_val_every}" \
      bash tools/run_newtonv_timing_triplet_gate.sh

    run_case promote_raw_v01_end100 \
      SCREEN_STEPS="${promote_steps}" \
      SCREEN_VAL_EVERY="${promote_val_every}" \
      bash tools/run_newtonv_raw_v01_gate.sh
    ;;
  permutations)
    run_permutation_queue
    ;;
  polar4)
    run_polar4_priority
    ;;
  next)
    run_next_ladder
    ;;
  all)
    run_timing_triplet
    run_next_ladder
    run_permutation_queue
    run_filter_ladder
    run_case raw_v01_end100 \
      SCREEN_STEPS="${raw_steps}" \
      SCREEN_VAL_EVERY="${raw_val_every}" \
      bash tools/run_newtonv_raw_v01_gate.sh
    ;;
  *)
    echo "NEWTONV_SUITE must be timing, filters, quick, raw200, promote, polar4, permutations, next, or all; got ${suite}" >&2
    exit 2
    ;;
esac
