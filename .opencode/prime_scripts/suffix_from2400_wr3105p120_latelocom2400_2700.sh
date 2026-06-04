#!/usr/bin/env bash
set -euo pipefail

label=track3_from2400_wr3105p120_latelocom2400_2700_seed3710
repo=/home/ubuntu/wr-fresh-20260526
logdir=/home/ubuntu/prime_track3_logs
ckpt_dir=/home/ubuntu/.cache/track3_checkpoints

cd "$repo"
source /home/ubuntu/venv/bin/activate

export PYTHONUNBUFFERED=1
export HF_HOME=/home/ubuntu/.cache/huggingface
export XDG_CACHE_HOME=/home/ubuntu/.cache/xdg
export TRITON_CACHE_DIR=/home/ubuntu/.cache/triton
export TORCHINDUCTOR_CACHE_DIR=/home/ubuntu/.cache/torchinductor-track3-from2400-wr3105p120-latelocom2400-2700

{
  echo "started $(date -Is)"
  echo "resume=$ckpt_dir/track3_short2000_wr3105p120_mult035_hold2400_seed3710_step2400.pt"
  echo "tail=pr287 h3105 p1.20; resume at 2400; LR multiplier 0.35 held 2400-2450 then fade to 1 by 2750"
  echo "late_locom=active 2400:2700, cap=0.20, K=4; tests whether the stalled suffix needs actual LocoProp again"
  echo "gate: kill if not better than scheduler-only failed suffix at 2500/2600"
} > "$logdir/${label}.status"

run_log="$logdir/${label}.log"

python3 -c 'import os, sys; os.setsid(); os.execvp(sys.argv[1], sys.argv[1:])' env \
  TRACK3_SOURCE=records/track_3_optimization/train_gpt_simple.py \
  TRACK3_GENERATED_SCRIPT="$logdir/${label}_train_gpt_simple_locom.py" \
  TRACK3_TRAIN_STEPS=3000 \
  TRACK3_NUM_TRIALS=1 \
  TRACK3_TARGET_LOSS=3.28 \
  TRACK3_MBS=16 \
  TRACK3_SEED_BASE=0 \
  TRACK3_SEED_OFFSET=3710 \
  TRACK3_RESUME_CHECKPOINT="$ckpt_dir/track3_short2000_wr3105p120_mult035_hold2400_seed3710_step2400.pt" \
  TRACK3_RESUME_ADVANCE_DATA=1 \
  TRACK3_RESUME_RESTORE_RNG=1 \
  TRACK3_RESUME_LOAD_OPTIMIZERS=1 \
  TRACK3_CHECKPOINT_STEPS=2600,2750,2800,2875 \
  TRACK3_CHECKPOINT_DIR="$ckpt_dir" \
  TRACK3_CHECKPOINT_PREFIX=track3_from2400_wr3105p120_latelocom2400_2700 \
  TRACK3_LOCOM_ENABLED=1 \
  TRACK3_LOCOM_LAYERS=all \
  TRACK3_LOCOM_STEPS=4 \
  TRACK3_LOCOM_SAMPLE_TOKENS=1024 \
  TRACK3_LOCOM_INNER_LR=0.1 \
  TRACK3_LOCOM_TARGET_GAMMA=1.0 \
  TRACK3_LOCOM_PROX=0.1 \
  TRACK3_LOCOM_ALPHA=1.0 \
  TRACK3_LOCOM_NORM_CAP=0.20 \
  TRACK3_LOCOM_INTERVAL=1 \
  TRACK3_LOCOM_ACTIVE_WINDOWS=0:1800,2400:2700 \
  TRACK3_LOCOM_END_STEP=2700 \
  TRACK3_LR_SWITCH_STEP=2400 \
  TRACK3_LR_AFTER_SWITCH=pr287 \
  TRACK3_LR_AFTER_SWITCH_POWER=1.20 \
  TRACK3_LR_AFTER_SWITCH_STEPS=3105 \
  TRACK3_LR_BUMP_WINDOWS=2400:2400:2450:2750:0.35 \
  TRACK3_LOCOM_LOG_STEPS=2400,2401,2425,2450,2475,2500,2525,2550,2575,2600,2625,2650,2700,2750,2800,2875,2950,3000 \
  SCREEN_VAL_EVERY=25 \
  NPROC_PER_NODE=1 \
  bash tools/run_track3_locoprop_m.sh > "$run_log" 2>&1 &
run_pid=$!

python3 tools/watch_track3_gates.py \
  --log "$run_log" \
  --pid "$run_pid" \
  --status-file "$logdir/${label}.status" \
  --max-loss 2500:3.3400 \
  --max-loss 2600:3.3375 \
  --max-loss 2750:3.3120 \
  --max-loss 2875:3.2865 &
watch_pid=$!

set +e
wait "$run_pid"
rc=$?
wait "$watch_pid"
watch_rc=$?
set -e

echo "finished $(date -Is) rc=$rc watch_rc=$watch_rc" >> "$logdir/${label}.status"
touch "$logdir/${label}.DONE"
if [[ "$watch_rc" -eq 42 ]]; then
  exit 42
fi
exit "$rc"
