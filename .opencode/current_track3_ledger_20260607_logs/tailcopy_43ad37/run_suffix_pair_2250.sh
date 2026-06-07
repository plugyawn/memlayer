#!/usr/bin/env bash
set -euo pipefail
cd /root/wr-track3-locom-20260606
source .venv/bin/activate
export MODE=suffixes
export TRACK3_2000_CHECKPOINT=/root/.cache/track3_checkpoints/track3_locom_good2000_tailcopy43ad37_seed3710_step2000.pt
export TRACK3_CHECKPOINT_DIR=/root/.cache/track3_checkpoints
export TRACK3_2000_LOG_DIR=/root/prime_track3_locom_2000_suffix_logs_43ad37
export TRACK3_SEED_OFFSET=3710
export TRACK3_SUFFIX_STEPS=2250
export TRACK3_SUFFIX_ACTIVE_END=2250
export TRACK3_SUFFIX_LANES=control,natural
export TRACK3_SUFFIX_CHECKPOINT_STEPS=2125,2250
bash tools/run_track3_locom_2000_suffix_probe.sh
