#!/usr/bin/env bash
set -euo pipefail
while pgrep -f track3_survival_random_from_k5_1800 >/dev/null; do sleep 15; done
cd /root/wr-track3-locom-20260606
source /root/venv/bin/activate
label="track3_survival_noloco_from_k5_1800_$(date -u +%H%M%S)"
log_dir="/root/prime_track3_kdepth_logs"
log="${log_dir}/${label}.log"
echo "survival_noloco_start label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${log_dir}/sequence.status"
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
  TRACK3_LOCOM_ENABLED="0" \
  TRACK3_LOCOM_ACTIVE_WINDOWS="" \
  TRACK3_LOCOM_END_STEP="0" \
  TRACK3_LOCOM_LOG_STEPS="1800,1825,1850,1875,1900,1925,1950,1975,2000,2025,2050,2075,2100,2125" \
  SCREEN_VAL_EVERY="25" \
  NPROC_PER_NODE="1" \
  bash tools/run_track3_locom_kdiag_probe.sh 2>&1 | tee "${log}"
echo "survival_noloco_done label=${label} $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee -a "${log_dir}/sequence.status"
