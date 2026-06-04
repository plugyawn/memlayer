#!/usr/bin/env bash
set -euo pipefail

label=wr_record_locom_aux_k5_lr1e3_nogate_2000_seed3710_h100_mbs64
repo=/root/wr-fresh-20260526
logdir=/root/prime_track3_logs

mkdir -p "$logdir"
cd "$repo"

run_log="$logdir/${label}.log"
outer_log="$logdir/${label}.outer.log"
gate_status_file="$logdir/${label}.gate.status"

{
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "repo=$repo"
  echo "label=$label"
  echo "source=records/track_3_optimization/results/20260509_contra_soft_muon/03c36e81-e2e5-4916-bf16-0141999b1dbb.txt"
  echo "seed=3710 train_steps=2000 schedule_steps=3105 final_mbs=64 generator=aux"
  echo "wr_locom=K5 inner_lr=1e-3 no accept gates cap0.20 sample512 aux_seqs16"
  echo "purpose=WR-stack LocoProp-M through the meaningful 1000-2000 phase; 500-step screen was not decisive"
  echo "gates=1000:3.6650,1250:3.6060,1500:3.5500,1625:3.5280,1750:3.5000,1875:3.4750,2000:3.4450"
} > "$gate_status_file"

setsid env \
  RUN_LABEL="$label" \
  REPO_DIR="$repo" \
  WR_TRAIN_STEPS=2000 \
  WR_SCHEDULE_STEPS=3105 \
  WR_SEED=3710 \
  NPROC_PER_NODE=1 \
  FINAL_MBS=64 \
  WR_LOCOM_GENERATOR=aux \
  WR_LOCOM_AUX_SEQS=16 \
  WR_LOCOM_BATCHED_PREP=1 \
  WR_LOCOM_ENABLED=1 \
  WR_LOCOM_LAYERS=all \
  WR_LOCOM_STEPS=5 \
  WR_LOCOM_SAMPLE_TOKENS=512 \
  WR_LOCOM_INNER_LR=0.001 \
  WR_LOCOM_TARGET_GAMMA=1.0 \
  WR_LOCOM_PROX=0.1 \
  WR_LOCOM_ALPHA=1.0 \
  WR_LOCOM_NORM_CAP=0.20 \
  WR_LOCOM_NORM_TO_BASE=0 \
  WR_LOCOM_REQUIRE_LOSS_DECREASE=0 \
  WR_LOCOM_MIN_COS_DESC=-inf \
  WR_LOCOM_LOG_STEPS=0,1,2,10,50,125,250,500,750,875,1000,1125,1250,1375,1500,1625,1750,1875,2000 \
  SCREEN_VAL_EVERY=125 \
  bash tools/prime_wr_record_locom_remote.sh > "$outer_log" 2>&1 &

run_pid=$!
echo "run_pid=$run_pid" >> "$gate_status_file"

set +e
python3 tools/watch_track3_gates.py \
  --log "$run_log" \
  --pid "$run_pid" \
  --status-file "$gate_status_file" \
  --poll-interval 30 \
  --grace-seconds 30 \
  --max-loss 1000:3.6650 \
  --max-loss 1250:3.6060 \
  --max-loss 1500:3.5500 \
  --max-loss 1625:3.5280 \
  --max-loss 1750:3.5000 \
  --max-loss 1875:3.4750 \
  --max-loss 2000:3.4450
watch_rc=$?

wait "$run_pid"
run_rc=$?
set -e

{
  echo "finished $(date -u +%Y-%m-%dT%H:%M:%SZ) watch_rc=$watch_rc run_rc=$run_rc"
  echo "log=$run_log"
  echo "outer_log=$outer_log"
} >> "$gate_status_file"

touch "$logdir/${label}.DONE"
exit "$run_rc"
