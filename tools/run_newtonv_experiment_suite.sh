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
  env \
    -u LOCO_DIAG \
    -u LOCO_DIAG_SURFACES \
    -u LOCO_DIAG_ATTN_LAYERS \
    -u LOCO_DIAG_MLP_LAYERS \
    -u LOCO_FULL_SURFACES \
    -u LOCO_FULL_WINDOWS \
    -u LOCO_FULL_COLLECT_WINDOWS \
    -u LOCO_FULL_NOOP \
    -u LOCO_FULL_SCHEDULE_ONLY \
    -u LOCO_FULL_END_STEP \
    -u LOCO_FULL_APPLY_BEFORE_MOMENTUM \
    -u LOCO_FULL_REFRESH_INTERVAL \
    -u LOCO_FULL_EMA_BETA \
    -u LOCO_FULL_RIDGE_REL \
    -u LOCO_FULL_BLEND_MAX \
    -u LOCO_FULL_BLEND_STEPS \
    -u LOCO_FULL_FILTER \
    -u LOCO_FULL_METRIC_POLAR \
    -u LOCO_FULL_NORM_RESTORE \
    -u LOCO_FULL_LOCAL_STATS \
    -u LOCO_FULL_APPLY_INTERVAL \
    -u LOCO_FULL_PRECOND_DTYPE \
    -u LOCO_FULL_POLAR_ITERS \
    -u LOCO_FULL_BLOCK_SIZE \
    -u LOCO_FULL_POWER_ALPHA \
    -u LOCO_FULL_POWER_CLIP \
    -u LOCO_FULL_FINITE_T \
    -u LOCO_FULL_SHRINK_ONLY \
    -u LOCO_FULL_STATIC_NORM \
    -u LOCO_FULL_SKIP_VARRED \
    -u LOCO_FULL_RESET_EACH_WINDOW \
    -u LOCO_FULL_BLEND_RESTART_EACH_WINDOW \
    -u LOCO_FULL_LOG_PRECOND \
    -u LOCO_FULL_LOG_PRECOND_DETAIL \
    -u LOCO_FULL_LOG_SPECTRUM \
    -u LOCO_FULL_LOG_EIGEN_ENERGY \
    -u LOCO_FULL_LOG_POSTPOLAR \
    LOG_PATH="${log_path}" \
    "$@"
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
    LOCO_DIAG_ATTN_LAYERS=0-1 \
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
    LOCO_DIAG_ATTN_LAYERS=0-1 \
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

  run_case ps_qkv_before_polar5_ridge020 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v \
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
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_paperfilter_ladder() {
  local pf_steps="${PF_STEPS:-120}"
  local pf_val_every="${PF_VAL_EVERY:-40}"
  local pf_collect="${PF_COLLECT_WINDOWS:-0-64}"
  local pf_windows="${PF_WINDOWS:-48-112}"

  run_case pf_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${pf_steps}" \
    SCREEN_VAL_EVERY="${pf_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case pf_v01_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${pf_collect}" \
    LOCO_FULL_WINDOWS="${pf_windows}" \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${pf_steps}" \
    SCREEN_VAL_EVERY="${pf_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case pf_inverse_v01_before_polar4_ridge020_blend010 \
    LOCO_FULL_COLLECT_WINDOWS="${pf_collect}" \
    LOCO_FULL_WINDOWS="${pf_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${pf_steps}" \
    SCREEN_VAL_EVERY="${pf_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case pf_finite_v01_before_polar4_ridge020_blend010 \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${pf_collect}" \
    LOCO_FULL_WINDOWS="${pf_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_FILTER=finite \
    LOCO_FULL_FINITE_T=1.0 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${pf_steps}" \
    SCREEN_VAL_EVERY="${pf_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh

  run_case pf_power05_v01_before_polar4_ridge020_blend010 \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${pf_collect}" \
    LOCO_FULL_WINDOWS="${pf_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_POWER_ALPHA=0.5 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${pf_steps}" \
    SCREEN_VAL_EVERY="${pf_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh
}

run_metricpolar_ladder() {
  local mp_steps="${MP_STEPS:-120}"
  local mp_val_every="${MP_VAL_EVERY:-40}"

  run_case mp_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mp_steps}" \
    SCREEN_VAL_EVERY="${mp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mp_schedule_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    SCREEN_STEPS="${mp_steps}" \
    SCREEN_VAL_EVERY="${mp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mp_cholmetric_v01_polar4 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mp_steps}" \
    SCREEN_VAL_EVERY="${mp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case mp_cholmetric_v01_polar5 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=5 \
    SCREEN_STEPS="${mp_steps}" \
    SCREEN_VAL_EVERY="${mp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case mp_cholmetric_qkv01_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mp_steps}" \
    SCREEN_VAL_EVERY="${mp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_metricpromote_ladder() {
  local mpp_steps="${MPP_STEPS:-200}"
  local mpp_val_every="${MPP_VAL_EVERY:-50}"

  run_case mpp_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mpp_steps}" \
    SCREEN_VAL_EVERY="${mpp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mpp_cholmetric_qkv01_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mpp_steps}" \
    SCREEN_VAL_EVERY="${mpp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mpp_cholmetric_qkv01_polar4_blend100 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_BLEND_STEPS=100 \
    SCREEN_STEPS="${mpp_steps}" \
    SCREEN_VAL_EVERY="${mpp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_metricv_promote_ladder() {
  local mvp_steps="${MVP_STEPS:-200}"
  local mvp_val_every="${MVP_VAL_EVERY:-50}"
  local mvp_collect="${MVP_COLLECT_WINDOWS:-0-64}"
  local mvp_windows="${MVP_WINDOWS:-48-112}"

  run_case mvp_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mvp_steps}" \
    SCREEN_VAL_EVERY="${mvp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mvp_v01_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${mvp_collect}" \
    LOCO_FULL_WINDOWS="${mvp_windows}" \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mvp_steps}" \
    SCREEN_VAL_EVERY="${mvp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mvp_cholmetric_v01_polar4_r003_blend025 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${mvp_collect}" \
    LOCO_FULL_WINDOWS="${mvp_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_RIDGE_REL=0.03 \
    LOCO_FULL_BLEND_MAX=0.25 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mvp_steps}" \
    SCREEN_VAL_EVERY="${mvp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case mvp_cholmetric_v01_polar4_r020_blend010_norm \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${mvp_collect}" \
    LOCO_FULL_WINDOWS="${mvp_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mvp_steps}" \
    SCREEN_VAL_EVERY="${mvp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_metricv_window_ladder() {
  local mvsw_steps="${MVSW_STEPS:-200}"
  local mvsw_val_every="${MVSW_VAL_EVERY:-50}"
  local mvsw_collect="${MVSW_COLLECT_WINDOWS:-0-64}"
  local mvsw_windows="${MVSW_WINDOWS:-48-160}"

  run_case mvsw_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mvsw_steps}" \
    SCREEN_VAL_EVERY="${mvsw_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mvsw_v01_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${mvsw_collect}" \
    LOCO_FULL_WINDOWS="${mvsw_windows}" \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mvsw_steps}" \
    SCREEN_VAL_EVERY="${mvsw_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mvsw_cholmetric_v01_polar4_r020_blend010_norm \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${mvsw_collect}" \
    LOCO_FULL_WINDOWS="${mvsw_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mvsw_steps}" \
    SCREEN_VAL_EVERY="${mvsw_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_paper_v_promote_ladder() {
  local pvp_steps="${PVP_STEPS:-200}"
  local pvp_val_every="${PVP_VAL_EVERY:-50}"
  local pvp_collect="${PVP_COLLECT_WINDOWS:-0-64}"
  local pvp_windows="${PVP_WINDOWS:-48-112}"

  run_case pvp_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${pvp_steps}" \
    SCREEN_VAL_EVERY="${pvp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case pvp_v01_noop_before_r020_blend010 \
    LOCO_FULL_NOOP=1 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${pvp_collect}" \
    LOCO_FULL_WINDOWS="${pvp_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${pvp_steps}" \
    SCREEN_VAL_EVERY="${pvp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case pvp_v01_noop_after_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${pvp_collect}" \
    LOCO_FULL_WINDOWS="${pvp_windows}" \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${pvp_steps}" \
    SCREEN_VAL_EVERY="${pvp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case pvp_finite_v01_before_r020_blend010 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${pvp_collect}" \
    LOCO_FULL_WINDOWS="${pvp_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_FILTER=finite \
    LOCO_FULL_FINITE_T=1.0 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    SCREEN_STEPS="${pvp_steps}" \
    SCREEN_VAL_EVERY="${pvp_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh

  run_case pvp_power05_v01_before_r020_blend010 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${pvp_collect}" \
    LOCO_FULL_WINDOWS="${pvp_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_POWER_ALPHA=0.5 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    SCREEN_STEPS="${pvp_steps}" \
    SCREEN_VAL_EVERY="${pvp_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh

  run_case pvp_inverse_v01_before_r020_blend010 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${pvp_collect}" \
    LOCO_FULL_WINDOWS="${pvp_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${pvp_steps}" \
    SCREEN_VAL_EVERY="${pvp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case pvp_cholmetric_v01_after_r020_blend005_norm \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${pvp_collect}" \
    LOCO_FULL_WINDOWS="${pvp_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.05 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${pvp_steps}" \
    SCREEN_VAL_EVERY="${pvp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_metricsurface_ladder() {
  local mps_steps="${MPS_STEPS:-120}"
  local mps_val_every="${MPS_VAL_EVERY:-40}"

  run_case mps_qk01_cholmetric_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mps_steps}" \
    SCREEN_VAL_EVERY="${mps_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mps_o01_cholmetric_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=o \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mps_steps}" \
    SCREEN_VAL_EVERY="${mps_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mps_qkvo01_cholmetric_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mps_steps}" \
    SCREEN_VAL_EVERY="${mps_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mps_qkv03_cholmetric_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v \
    LOCO_DIAG_ATTN_LAYERS=0-3 \
    LOCO_FULL_COLLECT_WINDOWS=0-64 \
    LOCO_FULL_WINDOWS=48-112 \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mps_steps}" \
    SCREEN_VAL_EVERY="${mps_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_surface_control_ladder() {
  local sc_steps="${SC_STEPS:-120}"
  local sc_val_every="${SC_VAL_EVERY:-40}"
  local sc_layers="${SC_LAYERS:-0-1}"
  local sc_collect="${SC_COLLECT_WINDOWS:-0-64}"
  local sc_windows="${SC_WINDOWS:-48-112}"

  run_case sc_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${sc_steps}" \
    SCREEN_VAL_EVERY="${sc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case sc_qk_noop_metric_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=qk \
    LOCO_DIAG_ATTN_LAYERS="${sc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${sc_collect}" \
    LOCO_FULL_WINDOWS="${sc_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${sc_steps}" \
    SCREEN_VAL_EVERY="${sc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case sc_qk_cholmetric_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk \
    LOCO_DIAG_ATTN_LAYERS="${sc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${sc_collect}" \
    LOCO_FULL_WINDOWS="${sc_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${sc_steps}" \
    SCREEN_VAL_EVERY="${sc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case sc_o_noop_metric_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=o \
    LOCO_DIAG_ATTN_LAYERS="${sc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${sc_collect}" \
    LOCO_FULL_WINDOWS="${sc_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${sc_steps}" \
    SCREEN_VAL_EVERY="${sc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case sc_o_cholmetric_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=o \
    LOCO_DIAG_ATTN_LAYERS="${sc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${sc_collect}" \
    LOCO_FULL_WINDOWS="${sc_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${sc_steps}" \
    SCREEN_VAL_EVERY="${sc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case sc_qkvo_noop_metric_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS="${sc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${sc_collect}" \
    LOCO_FULL_WINDOWS="${sc_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${sc_steps}" \
    SCREEN_VAL_EVERY="${sc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case sc_qkvo_cholmetric_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS="${sc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${sc_collect}" \
    LOCO_FULL_WINDOWS="${sc_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${sc_steps}" \
    SCREEN_VAL_EVERY="${sc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_qkvo_metric_promote_ladder() {
  local qmp_steps="${QMP_STEPS:-200}"
  local qmp_val_every="${QMP_VAL_EVERY:-50}"
  local qmp_layers="${QMP_LAYERS:-0-1}"
  local qmp_collect="${QMP_COLLECT_WINDOWS:-0-64}"
  local qmp_windows="${QMP_WINDOWS:-48-112}"

  run_case qmp_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${qmp_steps}" \
    SCREEN_VAL_EVERY="${qmp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qmp_qkvo_noop_metric_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS="${qmp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qmp_collect}" \
    LOCO_FULL_WINDOWS="${qmp_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${qmp_steps}" \
    SCREEN_VAL_EVERY="${qmp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qmp_qkvo_cholmetric_polar4 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS="${qmp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qmp_collect}" \
    LOCO_FULL_WINDOWS="${qmp_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${qmp_steps}" \
    SCREEN_VAL_EVERY="${qmp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_qkvo_schedule_ladder() {
  local qs_steps="${QS_STEPS:-200}"
  local qs_val_every="${QS_VAL_EVERY:-50}"
  local qs_layers="${QS_LAYERS:-0-3}"
  local qs_collect="${QS_COLLECT_WINDOWS:-0-64}"
  local qs_windows="${QS_WINDOWS:-48-112}"

  run_case qs_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${qs_steps}" \
    SCREEN_VAL_EVERY="${qs_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qs_qkvo_schedule_only_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS="${qs_layers}" \
    LOCO_FULL_WINDOWS="${qs_windows}" \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${qs_steps}" \
    SCREEN_VAL_EVERY="${qs_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qs_qkvo_noop_metric_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS="${qs_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qs_collect}" \
    LOCO_FULL_WINDOWS="${qs_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${qs_steps}" \
    SCREEN_VAL_EVERY="${qs_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_mlpfc_ladder() {
  local mfc_steps="${MFC_STEPS:-120}"
  local mfc_val_every="${MFC_VAL_EVERY:-40}"
  local mfc_layers="${MFC_LAYERS:-0-1}"
  local mfc_collect="${MFC_COLLECT_WINDOWS:-0-64}"
  local mfc_windows="${MFC_WINDOWS:-48-112}"

  run_case mfc_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mfc_steps}" \
    SCREEN_VAL_EVERY="${mfc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mfc_noop_after_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mfc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mfc_collect}" \
    LOCO_FULL_WINDOWS="${mfc_windows}" \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mfc_steps}" \
    SCREEN_VAL_EVERY="${mfc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mfc_inverse_before_r020_blend010 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mfc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mfc_collect}" \
    LOCO_FULL_WINDOWS="${mfc_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mfc_steps}" \
    SCREEN_VAL_EVERY="${mfc_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case mfc_inverse_after_polar4_r020_blend010 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mfc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mfc_collect}" \
    LOCO_FULL_WINDOWS="${mfc_windows}" \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mfc_steps}" \
    SCREEN_VAL_EVERY="${mfc_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case mfc_cholmetric_after_polar4_r020_blend005_norm \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mfc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mfc_collect}" \
    LOCO_FULL_WINDOWS="${mfc_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.05 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mfc_steps}" \
    SCREEN_VAL_EVERY="${mfc_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_mlpfc_promote_ladder() {
  local mfp_steps="${MFP_STEPS:-200}"
  local mfp_val_every="${MFP_VAL_EVERY:-50}"
  local mfp_layers="${MFP_LAYERS:-0-1}"
  local mfp_collect="${MFP_COLLECT_WINDOWS:-0-64}"
  local mfp_windows="${MFP_WINDOWS:-48-112}"

  run_case mfp_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mfp_steps}" \
    SCREEN_VAL_EVERY="${mfp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mfp_noop_after_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mfp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mfp_collect}" \
    LOCO_FULL_WINDOWS="${mfp_windows}" \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mfp_steps}" \
    SCREEN_VAL_EVERY="${mfp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case mfp_inverse_before_r020_blend010 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mfp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mfp_collect}" \
    LOCO_FULL_WINDOWS="${mfp_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mfp_steps}" \
    SCREEN_VAL_EVERY="${mfp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case mfp_cholmetric_after_polar4_r020_blend005_norm \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mfp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mfp_collect}" \
    LOCO_FULL_WINDOWS="${mfp_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.05 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${mfp_steps}" \
    SCREEN_VAL_EVERY="${mfp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_mlpfc_before_control_ladder() {
  local mbc_steps="${MBC_STEPS:-200}"
  local mbc_val_every="${MBC_VAL_EVERY:-50}"
  local mbc_layers="${MBC_LAYERS:-0-1}"
  local mbc_collect="${MBC_COLLECT_WINDOWS:-0-64}"
  local mbc_windows="${MBC_WINDOWS:-48-112}"

  run_case mbc_noop_before_r020_blend010 \
    LOCO_FULL_NOOP=1 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mbc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mbc_collect}" \
    LOCO_FULL_WINDOWS="${mbc_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mbc_steps}" \
    SCREEN_VAL_EVERY="${mbc_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case mbc_inverse_before_r020_blend010 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mbc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mbc_collect}" \
    LOCO_FULL_WINDOWS="${mbc_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.2 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mbc_steps}" \
    SCREEN_VAL_EVERY="${mbc_val_every}" \
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
  paperfilter)
    run_paperfilter_ladder
    ;;
  metricpolar)
    run_metricpolar_ladder
    ;;
  metricpromote)
    run_metricpromote_ladder
    ;;
  metricv_promote)
    run_metricv_promote_ladder
    ;;
  metricv_window)
    run_metricv_window_ladder
    ;;
  paper_v_promote)
    run_paper_v_promote_ladder
    ;;
  metricsurfaces)
    run_metricsurface_ladder
    ;;
  surface_control)
    run_surface_control_ladder
    ;;
  qkvo_metric_promote)
    run_qkvo_metric_promote_ladder
    ;;
  qkvo_schedule)
    run_qkvo_schedule_ladder
    ;;
  mlpfc)
    run_mlpfc_ladder
    ;;
  mlpfc_promote)
    run_mlpfc_promote_ladder
    ;;
  mlpfc_before_control)
    run_mlpfc_before_control_ladder
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
    echo "NEWTONV_SUITE must be timing, filters, quick, raw200, promote, polar4, permutations, next, tail, warmmetric, overprecond, overpromote, scheduleonly, preconddiag, schedule_diag, rightfilter, paperstyle, paperfilter, metricpolar, metricpromote, metricv_promote, metricv_window, paper_v_promote, metricsurfaces, surface_control, qkvo_metric_promote, qkvo_schedule, mlpfc, mlpfc_promote, mlpfc_before_control, or all; got ${suite}" >&2
    exit 2
    ;;
esac
