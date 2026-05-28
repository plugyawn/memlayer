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
    -u LOCO_FULL_APPLY_POST_VARRED \
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

run_v_spectral_shape_ladder() {
  local vss_steps="${VSS_STEPS:-160}"
  local vss_val_every="${VSS_VAL_EVERY:-25}"
  local vss_collect="${VSS_COLLECT_WINDOWS:-0-64}"
  local vss_windows="${VSS_WINDOWS:-48-112}"
  local vss_log_steps="${VSS_LOG_STEPS:-48,50,56,64,80,100,112,150,160}"

  run_case vss_baseline_a \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${vss_steps}" \
    SCREEN_VAL_EVERY="${vss_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vss_baseline_b \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${vss_steps}" \
    SCREEN_VAL_EVERY="${vss_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vss_v01_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${vss_collect}" \
    LOCO_FULL_WINDOWS="${vss_windows}" \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${vss_steps}" \
    SCREEN_VAL_EVERY="${vss_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vss_metric_v01_r020_blend010_norm \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${vss_collect}" \
    LOCO_FULL_WINDOWS="${vss_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_DIAG_LOG_STEPS="${vss_log_steps}" \
    SCREEN_STEPS="${vss_steps}" \
    SCREEN_VAL_EVERY="${vss_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case vss_power05_v01_r020_blend010 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${vss_collect}" \
    LOCO_FULL_WINDOWS="${vss_windows}" \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_POWER_ALPHA=0.5 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${vss_log_steps}" \
    SCREEN_STEPS="${vss_steps}" \
    SCREEN_VAL_EVERY="${vss_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh

  run_case vss_power075_v01_r020_blend010 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS=0-1 \
    LOCO_FULL_COLLECT_WINDOWS="${vss_collect}" \
    LOCO_FULL_WINDOWS="${vss_windows}" \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_POWER_ALPHA=0.75 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${vss_log_steps}" \
    SCREEN_STEPS="${vss_steps}" \
    SCREEN_VAL_EVERY="${vss_val_every}" \
    bash tools/run_newtonv_block_power_gate.sh
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

run_qkvo_power_shape_ladder() {
  local qps_steps="${QPS_STEPS:-160}"
  local qps_val_every="${QPS_VAL_EVERY:-25}"
  local qps_layers="${QPS_LAYERS:-0-1}"
  local qps_collect="${QPS_COLLECT_WINDOWS:-0-64}"
  local qps_windows="${QPS_WINDOWS:-48-112}"
  local qps_log_steps="${QPS_LOG_STEPS:-48,50,56,64,80,100,112,150,160}"

  run_case qps_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${qps_steps}" \
    SCREEN_VAL_EVERY="${qps_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qps_qkvo_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS="${qps_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qps_collect}" \
    LOCO_FULL_WINDOWS="${qps_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${qps_steps}" \
    SCREEN_VAL_EVERY="${qps_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qps_qkvo_power05_r020_blend010 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS="${qps_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qps_collect}" \
    LOCO_FULL_WINDOWS="${qps_windows}" \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_POWER_ALPHA=0.5 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${qps_log_steps}" \
    SCREEN_STEPS="${qps_steps}" \
    SCREEN_VAL_EVERY="${qps_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qps_qkvo_power075_r020_blend010 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v,o \
    LOCO_DIAG_ATTN_LAYERS="${qps_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qps_collect}" \
    LOCO_FULL_WINDOWS="${qps_windows}" \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_POWER_ALPHA=0.75 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${qps_log_steps}" \
    SCREEN_STEPS="${qps_steps}" \
    SCREEN_VAL_EVERY="${qps_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_qkv_power_shape_ladder() {
  local qvp_steps="${QVP_STEPS:-160}"
  local qvp_val_every="${QVP_VAL_EVERY:-40}"
  local qvp_layers="${QVP_LAYERS:-all}"
  local qvp_collect="${QVP_COLLECT_WINDOWS:-0-64}"
  local qvp_windows="${QVP_WINDOWS:-48-112}"
  local qvp_log_steps="${QVP_LOG_STEPS:-48,50,64,80,100,112,150,160}"

  run_case qvp_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${qvp_steps}" \
    SCREEN_VAL_EVERY="${qvp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qvp_qkv_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=qk,v \
    LOCO_DIAG_ATTN_LAYERS="${qvp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qvp_collect}" \
    LOCO_FULL_WINDOWS="${qvp_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=0 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${qvp_steps}" \
    SCREEN_VAL_EVERY="${qvp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qvp_qkv_power05_r020_blend010 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v \
    LOCO_DIAG_ATTN_LAYERS="${qvp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qvp_collect}" \
    LOCO_FULL_WINDOWS="${qvp_windows}" \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_POWER_ALPHA=0.5 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${qvp_log_steps}" \
    SCREEN_STEPS="${qvp_steps}" \
    SCREEN_VAL_EVERY="${qvp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qvp_qkv_power075_r020_blend010 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v \
    LOCO_DIAG_ATTN_LAYERS="${qvp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qvp_collect}" \
    LOCO_FULL_WINDOWS="${qvp_windows}" \
    LOCO_FULL_REFRESH_INTERVAL=16 \
    LOCO_FULL_EMA_BETA=0.8 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_POWER_ALPHA=0.75 \
    LOCO_FULL_POWER_CLIP=2.0 \
    LOCO_FULL_BLOCK_SIZE=0 \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${qvp_log_steps}" \
    SCREEN_STEPS="${qvp_steps}" \
    SCREEN_VAL_EVERY="${qvp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_qkv_inverse_control_ladder() {
  local qic_steps="${QIC_STEPS:-200}"
  local qic_val_every="${QIC_VAL_EVERY:-50}"
  local qic_layers="${QIC_LAYERS:-all}"
  local qic_collect="${QIC_COLLECT_WINDOWS:-0-64}"
  local qic_windows="${QIC_WINDOWS:-48-112}"
  local qic_ridge="${QIC_RIDGE_REL:-0.20}"
  local qic_refresh="${QIC_REFRESH_INTERVAL:-16}"
  local qic_ema="${QIC_EMA_BETA:-0.8}"

  run_case qic_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${qic_steps}" \
    SCREEN_VAL_EVERY="${qic_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qic_qkv_noop_before_r020 \
    LOCO_FULL_NOOP=1 \
    LOCO_FULL_SURFACES=qk,v \
    LOCO_DIAG_ATTN_LAYERS="${qic_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qic_collect}" \
    LOCO_FULL_WINDOWS="${qic_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${qic_refresh}" \
    LOCO_FULL_EMA_BETA="${qic_ema}" \
    LOCO_FULL_RIDGE_REL="${qic_ridge}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${qic_steps}" \
    SCREEN_VAL_EVERY="${qic_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case qic_vall_inverse_before_r020 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${qic_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qic_collect}" \
    LOCO_FULL_WINDOWS="${qic_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${qic_refresh}" \
    LOCO_FULL_EMA_BETA="${qic_ema}" \
    LOCO_FULL_RIDGE_REL="${qic_ridge}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${qic_steps}" \
    SCREEN_VAL_EVERY="${qic_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case qic_qk_inverse_before_r020 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk \
    LOCO_DIAG_ATTN_LAYERS="${qic_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qic_collect}" \
    LOCO_FULL_WINDOWS="${qic_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${qic_refresh}" \
    LOCO_FULL_EMA_BETA="${qic_ema}" \
    LOCO_FULL_RIDGE_REL="${qic_ridge}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${qic_steps}" \
    SCREEN_VAL_EVERY="${qic_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case qic_qkv_inverse_before_r020 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=qk,v \
    LOCO_DIAG_ATTN_LAYERS="${qic_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${qic_collect}" \
    LOCO_FULL_WINDOWS="${qic_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${qic_refresh}" \
    LOCO_FULL_EMA_BETA="${qic_ema}" \
    LOCO_FULL_RIDGE_REL="${qic_ridge}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${qic_steps}" \
    SCREEN_VAL_EVERY="${qic_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh
}

run_v_varred_interaction_ladder() {
  local vvr_steps="${VVR_STEPS:-160}"
  local vvr_val_every="${VVR_VAL_EVERY:-25}"
  local vvr_layers="${VVR_LAYERS:-0-1}"
  local vvr_collect="${VVR_COLLECT_WINDOWS:-0-64}"
  local vvr_windows="${VVR_WINDOWS:-48-112}"
  local vvr_log_steps="${VVR_LOG_STEPS:-48,50,56,64,80,100,112,150,160}"

  run_case vvr_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${vvr_steps}" \
    SCREEN_VAL_EVERY="${vvr_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vvr_v01_noop_polar4 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vvr_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vvr_collect}" \
    LOCO_FULL_WINDOWS="${vvr_windows}" \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${vvr_steps}" \
    SCREEN_VAL_EVERY="${vvr_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vvr_v01_noop_polar4_skipvr \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vvr_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vvr_collect}" \
    LOCO_FULL_WINDOWS="${vvr_windows}" \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_SKIP_VARRED=1 \
    SCREEN_STEPS="${vvr_steps}" \
    SCREEN_VAL_EVERY="${vvr_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vvr_metric_v01_varred_r020_blend010_norm \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vvr_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vvr_collect}" \
    LOCO_FULL_WINDOWS="${vvr_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${vvr_log_steps}" \
    SCREEN_STEPS="${vvr_steps}" \
    SCREEN_VAL_EVERY="${vvr_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case vvr_metric_v01_skipvr_r020_blend010_norm \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vvr_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vvr_collect}" \
    LOCO_FULL_WINDOWS="${vvr_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_SKIP_VARRED=1 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${vvr_log_steps}" \
    SCREEN_STEPS="${vvr_steps}" \
    SCREEN_VAL_EVERY="${vvr_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_v_short_pulse_ladder() {
  local vsp_steps="${VSP_STEPS:-120}"
  local vsp_val_every="${VSP_VAL_EVERY:-25}"
  local vsp_layers="${VSP_LAYERS:-0-1}"
  local vsp_collect="${VSP_COLLECT_WINDOWS:-0-64}"
  local vsp_win_short="${VSP_WINDOW_SHORT:-48-56}"
  local vsp_win_mid="${VSP_WINDOW_MID:-48-64}"
  local vsp_log_steps="${VSP_LOG_STEPS:-48,50,56,64,75,100,120}"

  run_case vsp_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${vsp_steps}" \
    SCREEN_VAL_EVERY="${vsp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vsp_v01_noop_polar4_win48_56 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vsp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vsp_collect}" \
    LOCO_FULL_WINDOWS="${vsp_win_short}" \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${vsp_steps}" \
    SCREEN_VAL_EVERY="${vsp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vsp_metric_skipvr_win48_56 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vsp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vsp_collect}" \
    LOCO_FULL_WINDOWS="${vsp_win_short}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_SKIP_VARRED=1 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${vsp_log_steps}" \
    SCREEN_STEPS="${vsp_steps}" \
    SCREEN_VAL_EVERY="${vsp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case vsp_v01_noop_polar4_win48_64 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vsp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vsp_collect}" \
    LOCO_FULL_WINDOWS="${vsp_win_mid}" \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${vsp_steps}" \
    SCREEN_VAL_EVERY="${vsp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vsp_metric_skipvr_win48_64 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vsp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vsp_collect}" \
    LOCO_FULL_WINDOWS="${vsp_win_mid}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL=0.20 \
    LOCO_FULL_BLEND_MAX=0.10 \
    LOCO_FULL_BLEND_STEPS=32 \
    LOCO_FULL_POLAR_ITERS=4 \
    LOCO_FULL_SKIP_VARRED=1 \
    LOCO_FULL_LOG_PRECOND=1 \
    LOCO_FULL_LOG_PRECOND_DETAIL=1 \
    LOCO_FULL_LOG_SPECTRUM=1 \
    LOCO_FULL_LOG_EIGEN_ENERGY=1 \
    LOCO_FULL_LOG_POSTPOLAR=1 \
    LOCO_DIAG_LOG_STEPS="${vsp_log_steps}" \
    SCREEN_STEPS="${vsp_steps}" \
    SCREEN_VAL_EVERY="${vsp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_v_schedule_pulse_ladder() {
  local vsc_steps="${VSC_STEPS:-120}"
  local vsc_val_every="${VSC_VAL_EVERY:-25}"
  local vsc_layers="${VSC_LAYERS:-0-1}"
  local vsc_win_short="${VSC_WINDOW_SHORT:-48-56}"
  local vsc_win_mid="${VSC_WINDOW_MID:-48-64}"

  run_case vsc_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${vsc_steps}" \
    SCREEN_VAL_EVERY="${vsc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vsc_v01_noop_polar4_win48_56 \
    NEWTONV_VARIANT=noop \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vsc_layers}" \
    LOCO_FULL_WINDOWS="${vsc_win_short}" \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${vsc_steps}" \
    SCREEN_VAL_EVERY="${vsc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vsc_schedule_only_polar4_win48_56 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vsc_layers}" \
    LOCO_FULL_WINDOWS="${vsc_win_short}" \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${vsc_steps}" \
    SCREEN_VAL_EVERY="${vsc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case vsc_schedule_only_polar4_win48_64 \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vsc_layers}" \
    LOCO_FULL_WINDOWS="${vsc_win_mid}" \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    LOCO_FULL_POLAR_ITERS=4 \
    SCREEN_STEPS="${vsc_steps}" \
    SCREEN_VAL_EVERY="${vsc_val_every}" \
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
  local mfp_metric_ridge="${MFP_METRIC_RIDGE_REL:-0.20}"
  local mfp_metric_blend="${MFP_METRIC_BLEND_MAX:-0.05}"
  local mfp_metric_blend_label="${mfp_metric_blend/./}"
  local mfp_metric_blend_steps="${MFP_METRIC_BLEND_STEPS:-32}"
  local mfp_metric_polar_iters="${MFP_METRIC_POLAR_ITERS:-4}"

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

  run_case "mfp_cholmetric_after_polar${mfp_metric_polar_iters}_r020_blend${mfp_metric_blend_label}_norm" \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mfp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mfp_collect}" \
    LOCO_FULL_WINDOWS="${mfp_windows}" \
    LOCO_FULL_METRIC_POLAR=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    LOCO_FULL_RIDGE_REL="${mfp_metric_ridge}" \
    LOCO_FULL_BLEND_MAX="${mfp_metric_blend}" \
    LOCO_FULL_BLEND_STEPS="${mfp_metric_blend_steps}" \
    LOCO_FULL_POLAR_ITERS="${mfp_metric_polar_iters}" \
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
  local mbc_refresh_interval="${MBC_REFRESH_INTERVAL:-16}"
  local mbc_ema_beta="${MBC_EMA_BETA:-0.8}"
  local mbc_ridge="${MBC_RIDGE_REL:-0.2}"
  local mbc_ridge_label="${mbc_ridge/./}"
  local mbc_blend="${MBC_BLEND_MAX:-0.10}"
  local mbc_blend_label="${mbc_blend/./}"
  local mbc_blend_steps="${MBC_BLEND_STEPS:-32}"

  run_case mbc_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mbc_steps}" \
    SCREEN_VAL_EVERY="${mbc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case "mbc_schedule_only_before_r${mbc_ridge_label}_blend${mbc_blend_label}" \
    NEWTONV_VARIANT=active \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mbc_layers}" \
    LOCO_FULL_WINDOWS="${mbc_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mbc_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mbc_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mbc_ridge}" \
    LOCO_FULL_BLEND_MAX="${mbc_blend}" \
    LOCO_FULL_BLEND_STEPS="${mbc_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mbc_steps}" \
    SCREEN_VAL_EVERY="${mbc_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case "mbc_noop_before_r${mbc_ridge_label}_blend${mbc_blend_label}" \
    LOCO_FULL_NOOP=1 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mbc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mbc_collect}" \
    LOCO_FULL_WINDOWS="${mbc_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mbc_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mbc_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mbc_ridge}" \
    LOCO_FULL_BLEND_MAX="${mbc_blend}" \
    LOCO_FULL_BLEND_STEPS="${mbc_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mbc_steps}" \
    SCREEN_VAL_EVERY="${mbc_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "mbc_inverse_before_r${mbc_ridge_label}_blend${mbc_blend_label}" \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mbc_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mbc_collect}" \
    LOCO_FULL_WINDOWS="${mbc_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mbc_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mbc_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mbc_ridge}" \
    LOCO_FULL_BLEND_MAX="${mbc_blend}" \
    LOCO_FULL_BLEND_STEPS="${mbc_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mbc_steps}" \
    SCREEN_VAL_EVERY="${mbc_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_mlpfc_filter_control_ladder() {
  local mff_steps="${MFF_STEPS:-200}"
  local mff_val_every="${MFF_VAL_EVERY:-50}"
  local mff_layers="${MFF_LAYERS:-0-1}"
  local mff_collect="${MFF_COLLECT_WINDOWS:-0-64}"
  local mff_windows="${MFF_WINDOWS:-48-112}"
  local mff_refresh_interval="${MFF_REFRESH_INTERVAL:-16}"
  local mff_ema_beta="${MFF_EMA_BETA:-0.8}"
  local mff_ridge="${MFF_RIDGE_REL:-0.2}"
  local mff_ridge_label="${mff_ridge/./}"
  local mff_blend="${MFF_BLEND_MAX:-0.10}"
  local mff_blend_label="${mff_blend/./}"
  local mff_blend_steps="${MFF_BLEND_STEPS:-32}"
  local mff_power_alpha="${MFF_POWER_ALPHA:-0.5}"
  local mff_power_alpha_label="${mff_power_alpha/./}"
  local mff_finite_t="${MFF_FINITE_T:-1.0}"
  local mff_finite_t_label="${mff_finite_t/./}"
  local mff_clip="${MFF_POWER_CLIP:-2.0}"

  run_case mff_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mff_steps}" \
    SCREEN_VAL_EVERY="${mff_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case "mff_noop_before_r${mff_ridge_label}_blend${mff_blend_label}" \
    LOCO_FULL_NOOP=1 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mff_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mff_collect}" \
    LOCO_FULL_WINDOWS="${mff_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mff_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mff_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mff_ridge}" \
    LOCO_FULL_BLEND_MAX="${mff_blend}" \
    LOCO_FULL_BLEND_STEPS="${mff_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mff_steps}" \
    SCREEN_VAL_EVERY="${mff_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "mff_inverse_before_r${mff_ridge_label}_blend${mff_blend_label}" \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mff_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mff_collect}" \
    LOCO_FULL_WINDOWS="${mff_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mff_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mff_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mff_ridge}" \
    LOCO_FULL_BLEND_MAX="${mff_blend}" \
    LOCO_FULL_BLEND_STEPS="${mff_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mff_steps}" \
    SCREEN_VAL_EVERY="${mff_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "mff_power${mff_power_alpha_label}_before_r${mff_ridge_label}_blend${mff_blend_label}" \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mff_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mff_collect}" \
    LOCO_FULL_WINDOWS="${mff_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mff_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mff_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mff_ridge}" \
    LOCO_FULL_BLEND_MAX="${mff_blend}" \
    LOCO_FULL_BLEND_STEPS="${mff_blend_steps}" \
    LOCO_FULL_FILTER=power \
    LOCO_FULL_POWER_ALPHA="${mff_power_alpha}" \
    LOCO_FULL_POWER_CLIP="${mff_clip}" \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mff_steps}" \
    SCREEN_VAL_EVERY="${mff_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "mff_finite_t${mff_finite_t_label}_before_r${mff_ridge_label}_blend${mff_blend_label}" \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mff_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mff_collect}" \
    LOCO_FULL_WINDOWS="${mff_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mff_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mff_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mff_ridge}" \
    LOCO_FULL_BLEND_MAX="${mff_blend}" \
    LOCO_FULL_BLEND_STEPS="${mff_blend_steps}" \
    LOCO_FULL_FILTER=finite \
    LOCO_FULL_FINITE_T="${mff_finite_t}" \
    LOCO_FULL_POWER_CLIP="${mff_clip}" \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mff_steps}" \
    SCREEN_VAL_EVERY="${mff_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_mlpfc_blend_ladder() {
  local mbg_steps="${MBG_STEPS:-200}"
  local mbg_val_every="${MBG_VAL_EVERY:-50}"
  local mbg_layers="${MBG_LAYERS:-0-1}"
  local mbg_collect="${MBG_COLLECT_WINDOWS:-0-64}"
  local mbg_windows="${MBG_WINDOWS:-48-112}"
  local mbg_refresh_interval="${MBG_REFRESH_INTERVAL:-16}"
  local mbg_ema_beta="${MBG_EMA_BETA:-0.8}"
  local mbg_ridge="${MBG_RIDGE_REL:-0.2}"
  local mbg_ridge_label="${mbg_ridge/./}"
  local mbg_blend_steps="${MBG_BLEND_STEPS:-32}"
  local mbg_blends="${MBG_BLEND_LIST:-0.025 0.05 0.075 0.10}"

  run_case mbg_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mbg_steps}" \
    SCREEN_VAL_EVERY="${mbg_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case "mbg_noop_before_r${mbg_ridge_label}" \
    LOCO_FULL_NOOP=1 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mbg_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mbg_collect}" \
    LOCO_FULL_WINDOWS="${mbg_windows}" \
    LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mbg_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mbg_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mbg_ridge}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mbg_steps}" \
    SCREEN_VAL_EVERY="${mbg_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  for mbg_blend in ${mbg_blends}; do
    local mbg_blend_label="${mbg_blend/./}"
    run_case "mbg_inverse_before_r${mbg_ridge_label}_blend${mbg_blend_label}" \
      LOCO_FULL_SURFACES=mlp_fc \
      LOCO_DIAG_MLP_LAYERS="${mbg_layers}" \
      LOCO_FULL_COLLECT_WINDOWS="${mbg_collect}" \
      LOCO_FULL_WINDOWS="${mbg_windows}" \
      LOCO_FULL_APPLY_BEFORE_MOMENTUM=1 \
      LOCO_FULL_REFRESH_INTERVAL="${mbg_refresh_interval}" \
      LOCO_FULL_EMA_BETA="${mbg_ema_beta}" \
      LOCO_FULL_RIDGE_REL="${mbg_ridge}" \
      LOCO_FULL_BLEND_MAX="${mbg_blend}" \
      LOCO_FULL_BLEND_STEPS="${mbg_blend_steps}" \
      LOCO_FULL_FILTER=inverse \
      LOCO_FULL_NORM_RESTORE=1 \
      SCREEN_STEPS="${mbg_steps}" \
      SCREEN_VAL_EVERY="${mbg_val_every}" \
      bash tools/run_newtonv_raw_v01_gate.sh
  done
}

run_mlpfc_postvarred_control_ladder() {
  local mpv_steps="${MPV_STEPS:-200}"
  local mpv_val_every="${MPV_VAL_EVERY:-50}"
  local mpv_layers="${MPV_LAYERS:-0-1}"
  local mpv_collect="${MPV_COLLECT_WINDOWS:-0-64}"
  local mpv_windows="${MPV_WINDOWS:-48-112}"
  local mpv_refresh_interval="${MPV_REFRESH_INTERVAL:-16}"
  local mpv_ema_beta="${MPV_EMA_BETA:-0.8}"
  local mpv_ridge="${MPV_RIDGE_REL:-0.2}"
  local mpv_ridge_label="${mpv_ridge/./}"
  local mpv_blend="${MPV_BLEND_MAX:-0.02}"
  local mpv_blend_label="${mpv_blend/./}"
  local mpv_blend_steps="${MPV_BLEND_STEPS:-32}"
  local mpv_finite_t="${MPV_FINITE_T:-1.0}"
  local mpv_clip="${MPV_POWER_CLIP:-2.0}"

  run_case mpv_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${mpv_steps}" \
    SCREEN_VAL_EVERY="${mpv_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case "mpv_schedule_only_postvarred_r${mpv_ridge_label}_blend${mpv_blend_label}" \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mpv_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mpv_collect}" \
    LOCO_FULL_WINDOWS="${mpv_windows}" \
    LOCO_FULL_APPLY_POST_VARRED=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mpv_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mpv_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mpv_ridge}" \
    LOCO_FULL_BLEND_MAX="${mpv_blend}" \
    LOCO_FULL_BLEND_STEPS="${mpv_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mpv_steps}" \
    SCREEN_VAL_EVERY="${mpv_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "mpv_noop_postvarred_r${mpv_ridge_label}_blend${mpv_blend_label}" \
    LOCO_FULL_NOOP=1 \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mpv_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mpv_collect}" \
    LOCO_FULL_WINDOWS="${mpv_windows}" \
    LOCO_FULL_APPLY_POST_VARRED=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mpv_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mpv_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mpv_ridge}" \
    LOCO_FULL_BLEND_MAX="${mpv_blend}" \
    LOCO_FULL_BLEND_STEPS="${mpv_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mpv_steps}" \
    SCREEN_VAL_EVERY="${mpv_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "mpv_inverse_postvarred_r${mpv_ridge_label}_blend${mpv_blend_label}" \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mpv_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mpv_collect}" \
    LOCO_FULL_WINDOWS="${mpv_windows}" \
    LOCO_FULL_APPLY_POST_VARRED=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mpv_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mpv_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mpv_ridge}" \
    LOCO_FULL_BLEND_MAX="${mpv_blend}" \
    LOCO_FULL_BLEND_STEPS="${mpv_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mpv_steps}" \
    SCREEN_VAL_EVERY="${mpv_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "mpv_finite_postvarred_r${mpv_ridge_label}_blend${mpv_blend_label}" \
    LOCO_FULL_SURFACES=mlp_fc \
    LOCO_DIAG_MLP_LAYERS="${mpv_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${mpv_collect}" \
    LOCO_FULL_WINDOWS="${mpv_windows}" \
    LOCO_FULL_APPLY_POST_VARRED=1 \
    LOCO_FULL_REFRESH_INTERVAL="${mpv_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${mpv_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${mpv_ridge}" \
    LOCO_FULL_BLEND_MAX="${mpv_blend}" \
    LOCO_FULL_BLEND_STEPS="${mpv_blend_steps}" \
    LOCO_FULL_FILTER=finite \
    LOCO_FULL_FINITE_T="${mpv_finite_t}" \
    LOCO_FULL_POWER_CLIP="${mpv_clip}" \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${mpv_steps}" \
    SCREEN_VAL_EVERY="${mpv_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh
}

run_v_postvarred_control_ladder() {
  local vpp_steps="${VPP_STEPS:-200}"
  local vpp_val_every="${VPP_VAL_EVERY:-50}"
  local vpp_layers="${VPP_LAYERS:-0-1}"
  local vpp_collect="${VPP_COLLECT_WINDOWS:-0-64}"
  local vpp_windows="${VPP_WINDOWS:-48-112}"
  local vpp_refresh_interval="${VPP_REFRESH_INTERVAL:-16}"
  local vpp_ema_beta="${VPP_EMA_BETA:-0.8}"
  local vpp_ridge="${VPP_RIDGE_REL:-0.2}"
  local vpp_ridge_label="${vpp_ridge/./}"
  local vpp_blend="${VPP_BLEND_MAX:-0.02}"
  local vpp_blend_label="${vpp_blend/./}"
  local vpp_blend_steps="${VPP_BLEND_STEPS:-32}"
  local vpp_finite_t="${VPP_FINITE_T:-1.0}"
  local vpp_clip="${VPP_POWER_CLIP:-2.0}"

  run_case vpp_baseline \
    NEWTONV_VARIANT=baseline \
    SCREEN_STEPS="${vpp_steps}" \
    SCREEN_VAL_EVERY="${vpp_val_every}" \
    bash tools/run_newtonv_timing_triplet_gate.sh

  run_case "vpp_schedule_only_postvarred_r${vpp_ridge_label}_blend${vpp_blend_label}" \
    LOCO_FULL_SCHEDULE_ONLY=1 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vpp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vpp_collect}" \
    LOCO_FULL_WINDOWS="${vpp_windows}" \
    LOCO_FULL_APPLY_POST_VARRED=1 \
    LOCO_FULL_REFRESH_INTERVAL="${vpp_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${vpp_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${vpp_ridge}" \
    LOCO_FULL_BLEND_MAX="${vpp_blend}" \
    LOCO_FULL_BLEND_STEPS="${vpp_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${vpp_steps}" \
    SCREEN_VAL_EVERY="${vpp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "vpp_noop_postvarred_r${vpp_ridge_label}_blend${vpp_blend_label}" \
    LOCO_FULL_NOOP=1 \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vpp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vpp_collect}" \
    LOCO_FULL_WINDOWS="${vpp_windows}" \
    LOCO_FULL_APPLY_POST_VARRED=1 \
    LOCO_FULL_REFRESH_INTERVAL="${vpp_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${vpp_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${vpp_ridge}" \
    LOCO_FULL_BLEND_MAX="${vpp_blend}" \
    LOCO_FULL_BLEND_STEPS="${vpp_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${vpp_steps}" \
    SCREEN_VAL_EVERY="${vpp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "vpp_inverse_postvarred_r${vpp_ridge_label}_blend${vpp_blend_label}" \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vpp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vpp_collect}" \
    LOCO_FULL_WINDOWS="${vpp_windows}" \
    LOCO_FULL_APPLY_POST_VARRED=1 \
    LOCO_FULL_REFRESH_INTERVAL="${vpp_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${vpp_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${vpp_ridge}" \
    LOCO_FULL_BLEND_MAX="${vpp_blend}" \
    LOCO_FULL_BLEND_STEPS="${vpp_blend_steps}" \
    LOCO_FULL_FILTER=inverse \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${vpp_steps}" \
    SCREEN_VAL_EVERY="${vpp_val_every}" \
    bash tools/run_newtonv_raw_v01_gate.sh

  run_case "vpp_finite_postvarred_r${vpp_ridge_label}_blend${vpp_blend_label}" \
    LOCO_FULL_SURFACES=v \
    LOCO_DIAG_ATTN_LAYERS="${vpp_layers}" \
    LOCO_FULL_COLLECT_WINDOWS="${vpp_collect}" \
    LOCO_FULL_WINDOWS="${vpp_windows}" \
    LOCO_FULL_APPLY_POST_VARRED=1 \
    LOCO_FULL_REFRESH_INTERVAL="${vpp_refresh_interval}" \
    LOCO_FULL_EMA_BETA="${vpp_ema_beta}" \
    LOCO_FULL_RIDGE_REL="${vpp_ridge}" \
    LOCO_FULL_BLEND_MAX="${vpp_blend}" \
    LOCO_FULL_BLEND_STEPS="${vpp_blend_steps}" \
    LOCO_FULL_FILTER=finite \
    LOCO_FULL_FINITE_T="${vpp_finite_t}" \
    LOCO_FULL_POWER_CLIP="${vpp_clip}" \
    LOCO_FULL_STATIC_NORM=1 \
    LOCO_FULL_NORM_RESTORE=1 \
    SCREEN_STEPS="${vpp_steps}" \
    SCREEN_VAL_EVERY="${vpp_val_every}" \
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
  v_spectral_shape)
    run_v_spectral_shape_ladder
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
  qkvo_power_shape)
    run_qkvo_power_shape_ladder
    ;;
  qkv_power_shape)
    run_qkv_power_shape_ladder
    ;;
  qkv_inverse_control)
    run_qkv_inverse_control_ladder
    ;;
  v_varred_interaction)
    run_v_varred_interaction_ladder
    ;;
  v_short_pulse)
    run_v_short_pulse_ladder
    ;;
  v_schedule_pulse)
    run_v_schedule_pulse_ladder
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
  mlpfc_filter_control)
    run_mlpfc_filter_control_ladder
    ;;
  mlpfc_blend)
    run_mlpfc_blend_ladder
    ;;
  mlpfc_postvarred_control)
    run_mlpfc_postvarred_control_ladder
    ;;
  v_postvarred_control)
    run_v_postvarred_control_ladder
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
    echo "NEWTONV_SUITE must be timing, filters, quick, raw200, promote, polar4, permutations, next, tail, warmmetric, overprecond, overpromote, scheduleonly, preconddiag, schedule_diag, rightfilter, paperstyle, paperfilter, metricpolar, metricpromote, metricv_promote, metricv_window, v_spectral_shape, paper_v_promote, metricsurfaces, surface_control, qkvo_metric_promote, qkvo_schedule, qkvo_power_shape, qkv_power_shape, qkv_inverse_control, v_varred_interaction, v_short_pulse, v_schedule_pulse, mlpfc, mlpfc_promote, mlpfc_before_control, mlpfc_filter_control, mlpfc_blend, mlpfc_postvarred_control, v_postvarred_control, or all; got ${suite}" >&2
    exit 2
    ;;
esac
