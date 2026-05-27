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

run_next_tail() {
  run_case tail_polar4_v01_win48_112 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case tail_qk_win32_80_p4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk \
    LOCO_FULL_WINDOWS=32-80 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case tail_o_win32_80_p4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=o \
    LOCO_FULL_WINDOWS=32-80 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_warmmetric_ladder() {
  run_case warm_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case warm_v01_collect0_48_apply48_112_p4 \
    LOCO_FULL_COLLECT_WINDOWS=0-48 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case warm_v01_collect0_64_apply48_112_p4 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case warm_o_collect0_64_apply48_112_p4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=o \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case warm_vo_collect0_64_apply48_112_p4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=v,o \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_overprecond_ladder() {
  run_case over_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case over_v01_warm_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case over_v01_warm_polar5 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=5 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case over_v01_warm_polar4 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case over_v01_warm_polar4_skipvr \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_SKIP_VARRED=1 \
    SCREEN_STEPS="${next_steps}" \
    SCREEN_VAL_EVERY="${next_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_overpromote_ladder() {
  run_case overpromote_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case overpromote_v01_warm_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case overpromote_v01_warm_noop_polar5 \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=5 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case overpromote_vall_warm_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case overpromote_v01_warm_active_polar5 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=5 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case overpromote_v01_warm_active_polar4 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_schedule_only_ladder() {
  run_case schedule_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case schedule_vobank_noop_polar5_nostats \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=5 \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case schedule_vobank_noop_polar4_nostats \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case schedule_vobank_noop_polar5_all_nostats \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_WINDOWS=all \
    LOCO_FULL_POLAR_ITERS=5 \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case schedule_vobank_noop_polar4_all_nostats \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_WINDOWS=all \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case schedule_v01_noop_polar5_collect \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=5 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case schedule_vall_noop_polar4_collect \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${promote_steps}" \
    SCREEN_VAL_EVERY="${promote_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_precond_diag_ladder() {
  local diag_steps="${DIAG_STEPS:-120}"
  local diag_val_every="${DIAG_VAL_EVERY:-40}"
  local diag_log_steps="${DIAG_LOG_STEPS:-50,64,80,100,112}"

  run_case diag_v01_warm_active_polar5 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=5 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${diag_log_steps}" \
    SCREEN_STEPS="${diag_steps}" \
    SCREEN_VAL_EVERY="${diag_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case diag_v01_warm_active_polar4 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${diag_log_steps}" \
    SCREEN_STEPS="${diag_steps}" \
    SCREEN_VAL_EVERY="${diag_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case diag_vall_warm_active_polar4 \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${diag_log_steps}" \
    SCREEN_STEPS="${diag_steps}" \
    SCREEN_VAL_EVERY="${diag_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_schedule_diag_ladder() {
  run_schedule_only_ladder
  run_precond_diag_ladder
}

run_rightfilter_ladder() {
  local rf_steps="${RF_STEPS:-120}"
  local rf_val_every="${RF_VAL_EVERY:-40}"

  run_case rf_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${rf_steps}" \
    SCREEN_VAL_EVERY="${rf_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case rf_schedule_noop_polar5 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=5 \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    SCREEN_STEPS="${rf_steps}" \
    SCREEN_VAL_EVERY="${rf_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case rf_schedule_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    SCREEN_STEPS="${rf_steps}" \
    SCREEN_VAL_EVERY="${rf_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case rf_inverse_v01_polar4 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${rf_steps}" \
    SCREEN_VAL_EVERY="${rf_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case rf_topshrink_v01_polar4 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_FILTER=topshrink \
    LOCO_FULL_SHRINK_RANK=64 \
    LOCO_FULL_SHRINK_T=1.0 \
    LOCO_FULL_SHRINK_CLIP=2.0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${rf_steps}" \
    SCREEN_VAL_EVERY="${rf_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case rf_finite_dense_v01_polar4 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_FILTER=finite \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_FINITE_T=1.0 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${rf_steps}" \
    SCREEN_VAL_EVERY="${rf_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh

  run_case rf_power05_dense_v01_polar4 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_POWER_ALPHA=0.5 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${rf_steps}" \
    SCREEN_VAL_EVERY="${rf_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh
}

run_paperstyle_ladder() {
  local ps_steps="${PS_STEPS:-120}"
  local ps_val_every="${PS_VAL_EVERY:-40}"

  run_case ps_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${ps_steps}" \
    SCREEN_VAL_EVERY="${ps_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case ps_v01_before_polar5_ridge020 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_POLAR_ITERS=5 \
    SCREEN_STEPS="${ps_steps}" \
    SCREEN_VAL_EVERY="${ps_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case ps_v01_before_polar4_ridge020 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${ps_steps}" \
    SCREEN_VAL_EVERY="${ps_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case ps_vall_before_polar5_ridge020 \
    LOCO_DIAG_ATTN_LAYERS=all \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_POLAR_ITERS=5 \
    SCREEN_STEPS="${ps_steps}" \
    SCREEN_VAL_EVERY="${ps_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
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
  tail)
    run_next_tail
    ;;
  warmmetric)
    run_warmmetric_ladder
    ;;
  overprecond)
    run_overprecond_ladder
    ;;
  overpromote)
    run_overpromote_ladder
    ;;
  scheduleonly)
    run_schedule_only_ladder
    ;;
  preconddiag)
    run_precond_diag_ladder
    ;;
  schedule_diag)
    run_schedule_diag_ladder
    ;;
  rightfilter)
    run_rightfilter_ladder
    ;;
  paperstyle)
    run_paperstyle_ladder
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
    echo "NEWTONV_SUITE must be timing, filters, quick, raw200, promote, polar4, permutations, next, tail, warmmetric, overprecond, overpromote, scheduleonly, preconddiag, schedule_diag, rightfilter, paperstyle, or all; got ${suite}" >&2
    exit 2
    ;;
esac
