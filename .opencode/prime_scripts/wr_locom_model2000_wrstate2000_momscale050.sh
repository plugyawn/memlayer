#!/usr/bin/env bash
set -euo pipefail

repo=/root/wr-fresh-20260526
logdir=/root/prime_track3_logs
ckpt_dir=/root/.cache/track3_checkpoints
loco_model_ckpt="$ckpt_dir/track3_prime_recover_loco2400_h3075ramp2350x150_seed3710_step2000.pt"
wr_state_ckpt="$ckpt_dir/wr_source_seed3710_step2000.pt"

mkdir -p "$logdir" "$ckpt_dir"
cd "$repo"

export PYTHONUNBUFFERED=1
export HF_HOME=/root/.cache/huggingface
export XDG_CACHE_HOME=/root/.cache/xdg
export TRITON_CACHE_DIR=/root/.cache/triton
export TORCHINDUCTOR_CACHE_DIR=/root/.cache/torchinductor-wr-locom-momscale050

source_script=records/track_3_optimization/results/20260509_contra_soft_muon/03c36e81-e2e5-4916-bf16-0141999b1dbb.txt

if [[ ! -f "$loco_model_ckpt" ]]; then
  echo "missing_loco_model_checkpoint=$loco_model_ckpt" >&2
  exit 2
fi

if [[ ! -f "$wr_state_ckpt" ]]; then
  RUN_LABEL=wr_source_seed3710_ckpt2000_for_momscale \
  WR_RESUME_SOURCE="$source_script" \
  WR_TRAIN_STEPS=2000 \
  WR_SCHEDULE_STEPS=3105 \
  WR_SEED=3710 \
  WR_SAVE_CHECKPOINT="$wr_state_ckpt" \
  WR_SAVE_CHECKPOINT_STEP=2000 \
  WR_TARGET_LOSS=0 \
  SCREEN_VAL_EVERY=125 \
  NPROC_PER_NODE=1 \
  bash tools/prime_wr_record_resume_remote.sh
fi

label=wr_locom_model2000_wrstate2000_momscale050_seed3710
{
  echo "started $(date -Is)"
  echo "model_checkpoint=$loco_model_ckpt"
  echo "optimizer_checkpoint=$wr_state_ckpt"
  echo "optimizer2_momentum_scale=0.5"
  echo "train_steps=3000 schedule_steps=3105 seed=3710"
  echo "purpose=LocoProp-M prefix model state plus mature WR optimizer state with optimizer2 momentum interpolation"
  sha256sum "$loco_model_ckpt" "$wr_state_ckpt"
} > "$logdir/${label}.status"

RUN_LABEL="$label" \
WR_RESUME_SOURCE="$source_script" \
WR_TRAIN_STEPS=3000 \
WR_SCHEDULE_STEPS=3105 \
WR_SEED=3710 \
WR_RESUME_MODEL_CHECKPOINT="$loco_model_ckpt" \
WR_RESUME_OPTIMIZER_CHECKPOINT="$wr_state_ckpt" \
WR_RESUME_LOAD_OPTIMIZERS=1 \
WR_RESUME_RESTORE_RNG=1 \
WR_RESUME_ADVANCE_DATA=1 \
WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE=0.5 \
WR_TARGET_LOSS=3.28 \
SCREEN_VAL_EVERY=25 \
NPROC_PER_NODE=1 \
bash tools/prime_wr_record_resume_remote.sh

rc=$?
echo "finished $(date -Is) rc=$rc" >> "$logdir/${label}.status"
exit "$rc"
