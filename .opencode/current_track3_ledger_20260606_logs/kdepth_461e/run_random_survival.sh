#!/usr/bin/env bash
set -euo pipefail
cd /root/wr-track3-locom-20260606
source /root/venv/bin/activate
label="track3_survival_random_from_k5_1800_$(date -u +%H%M%S)"
log_dir="/root/prime_track3_kdepth_logs"
log="${log_dir}/${label}.log"
echo "survival_random_start label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${log_dir}/sequence.status"
env \
  TRACK3_KDIAG_PROFILE="post-true-k10-lr2e4-active-poscos" \
  TRACK3_KDIAG_LABEL="${label}" \
  TRACK3_SOURCE="records/track_3_optimization/train_gpt_simple.py" \
  TRACK3_GENERATED_SCRIPT="/tmp/${label}.py" \
  TRACK3_TRAIN_STEPS="2125" \
  TRACK3_NUM_TRIALS="1" \
  TRACK3_TARGET_LOSS="3.28" \
  TRACK3_MBS="16" \
  TRACK3_SEED_BASE="0" \
  TRACK3_SEED_OFFSET="3710" \
  TRACK3_RESUME_CHECKPOINT="/root/.cache/track3_checkpoints/track3_kdepth_k5-lr2e4_seed3710_step1800.pt" \
  TRACK3_RESUME_ADVANCE_DATA="1" \
  TRACK3_RESUME_RESTORE_RNG="1" \
  TRACK3_RESUME_LOAD_OPTIMIZERS="1" \
  TRACK3_COOLDOWN_FRAC="1.0" \
  TRACK3_LR_SCHEDULE="power" \
  TRACK3_LR_POWER="2.0" \
  TRACK3_LR_SCHEDULE_STEPS="3000" \
  TRACK3_LR_MIN_ETA="0.0" \
  TRACK3_LOCOM_ENABLED="1" \
  TRACK3_LOCOM_RANDOM_CORRECTION="1" \
  TRACK3_LOCOM_LOCAL_OPT="random" \
  TRACK3_LOCOM_CORRECTION_MODE="normal" \
  TRACK3_LOCOM_LAYERS="all" \
  TRACK3_LOCOM_STEPS="5" \
  TRACK3_LOCOM_INNER_LR="2e-4" \
  TRACK3_LOCOM_TARGET_SPACE="post" \
  TRACK3_LOCOM_TRUE_POST_GRAD="1" \
  TRACK3_LOCOM_MIN_COS_DESC="0.0" \
  TRACK3_LOCOM_REQUIRE_LOSS_DECREASE="1" \
  TRACK3_LOCOM_ALPHA="1.0" \
  TRACK3_LOCOM_SAMPLE_TOKENS="1024" \
  TRACK3_LOCOM_NORM_TARGET="0.0" \
  TRACK3_LOCOM_NORM_TO_BASE="0" \
  TRACK3_LOCOM_NORM_CAP="0.20" \
  TRACK3_LOCOM_ACTIVE_WINDOWS="1800:2126" \
  TRACK3_LOCOM_END_STEP="2126" \
  TRACK3_LOCOM_LOG_STEPS="1800,1825,1850,1875,1900,1925,1950,1975,2000,2025,2050,2075,2100,2125" \
  TRACK3_LOCOM_DIAG_STEPS="" \
  TRACK3_LOCOM_DIAG_MAX_LAYERS="4" \
  SCREEN_VAL_EVERY="25" \
  NPROC_PER_NODE="1" \
  bash tools/run_track3_locom_kdiag_probe.sh 2>&1 | tee "${log}"
echo "survival_random_done label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${log_dir}/sequence.status"
