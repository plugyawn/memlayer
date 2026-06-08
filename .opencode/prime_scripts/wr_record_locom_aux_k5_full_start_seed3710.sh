#!/usr/bin/env bash
set -euo pipefail

label=wr_record_locom_aux_k5_full_start_seed3710_h100_mbs64
repo=/root/wr-fresh-20260526
logdir=/root/prime_track3_logs

mkdir -p "$logdir"
cd "$repo"

run_log="$logdir/${label}.log"
outer_log="$logdir/${label}.outer.log"
status_file="$logdir/${label}.status"

{
  echo "started $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  echo "repo=$repo"
  echo "label=$label"
  echo "source=records/track_3_optimization/results/20260509_contra_soft_muon/03c36e81-e2e5-4916-bf16-0141999b1dbb.txt"
  echo "seed=3710 train_steps=3040 schedule_steps=3105 final_mbs=64 generator=aux"
  echo "wr_stack=current-record 20260509 contra->normal->soft muon, SOAP mlp_plus_v, PR287 power LR"
  echo "wr_locom=active 0:3040, c_fc/all layers, K5, inner_lr=1e-3, prox=0.1, cap0.20, sample1024, aux_seqs16"
  echo "wr_locom_best_practices=hookless aux capture, batched prep, no accept/cos gate, additive correction after optimizer step, no optimizer-state mutation"
  echo "decision_gate=do not judge before step 2000 unless setup/OOM/nonfinite; compare slope and loss at 2000+"
} > "$status_file"

setsid env \
  RUN_LABEL="$label" \
  REPO_DIR="$repo" \
  WR_TRAIN_STEPS=3040 \
  WR_SCHEDULE_STEPS=3105 \
  WR_SEED=3710 \
  NPROC_PER_NODE=1 \
  FINAL_MBS=64 \
  WR_LOCOM_GENERATOR=aux \
  WR_LOCOM_AUX_SEQS=16 \
  WR_LOCOM_BATCHED_PREP=1 \
  WR_LOCOM_ENABLED=1 \
  WR_LOCOM_LAYERS=all \
  WR_LOCOM_ACTIVE_WINDOWS=0:3040 \
  WR_LOCOM_START_STEP=0 \
  WR_LOCOM_END_STEP=3040 \
  WR_LOCOM_INTERVAL=1 \
  WR_LOCOM_STEPS=5 \
  WR_LOCOM_SAMPLE_TOKENS=1024 \
  WR_LOCOM_INNER_LR=0.001 \
  WR_LOCOM_TARGET_GAMMA=1.0 \
  WR_LOCOM_PROX=0.1 \
  WR_LOCOM_ALPHA=1.0 \
  WR_LOCOM_NORM_CAP=0.20 \
  WR_LOCOM_NORM_TO_BASE=0 \
  WR_LOCOM_REQUIRE_LOSS_DECREASE=0 \
  WR_LOCOM_MIN_COS_DESC=-inf \
  WR_LOCOM_LOG_STEPS=0,1,2,10,50,125,250,375,500,625,750,875,1000,1125,1250,1375,1500,1625,1750,1875,2000,2125,2250,2375,2500,2625,2750,2875,3000,3030,3040 \
  SCREEN_VAL_EVERY=125 \
  bash tools/prime_wr_record_locom_remote.sh > "$outer_log" 2>&1 &

run_pid=$!
echo "run_pid=$run_pid" >> "$status_file"
wait "$run_pid"
run_rc=$?

{
  echo "finished $(date -u +%Y-%m-%dT%H:%M:%SZ) run_rc=$run_rc"
  echo "log=$run_log"
  echo "outer_log=$outer_log"
} >> "$status_file"

touch "$logdir/${label}.DONE"
exit "$run_rc"
