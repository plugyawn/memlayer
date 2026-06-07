#!/usr/bin/env bash
set -euo pipefail
cd /root/wr-track3-locom-20260606
source .venv/bin/activate
export TRACK3_SUFFIX_CHECKPOINT=/root/.cache/track3_checkpoints/track3_locom_good2000_tailcopy43ad37_seed3710_step2000.pt
export TRACK3_SUFFIX_FROM_STEP=2000
export TRACK3_SUFFIX_LOG_DIR=/root/prime_track3_tail_pr287_from2000_logs_43ad37
export TRACK3_CHECKPOINT_DIR=/root/.cache/track3_checkpoints
export TRACK3_SEED_OFFSET=3710
export TRACK3_TRAIN_STEPS=2500
export TRACK3_CHECKPOINT_STEPS=2250,2400,2500
export TRACK3_SUFFIX_LANES=pr287_h3105p120
bash tools/run_track3_suffix_schedule_probe.sh
