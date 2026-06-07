#!/usr/bin/env bash
set -euo pipefail
cd /root/wr-track3-locom-20260606
source .venv/bin/activate
export MODE=save2000
export FORCE_2000=1
export TRACK3_BASE_CHECKPOINT=/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt
export TRACK3_CHECKPOINT_DIR=/root/.cache/track3_checkpoints
export TRACK3_2000_PREFIX=track3_locom_good2000_tailcopy43ad37
export TRACK3_2000_LOG_DIR=/root/prime_track3_locom_2000_suffix_logs_43ad37
export TRACK3_SEED_OFFSET=3710
bash tools/run_track3_locom_2000_suffix_probe.sh
