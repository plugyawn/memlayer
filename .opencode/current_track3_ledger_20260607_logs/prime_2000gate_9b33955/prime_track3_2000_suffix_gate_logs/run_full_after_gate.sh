#!/usr/bin/env bash
set -euo pipefail
repo=/home/ubuntu/wr-track3-locom-20260606
gate_logdir=/home/ubuntu/prime_track3_2000_suffix_gate_logs
full_logdir=/home/ubuntu/prime_track3_2000_suffix_full_logs
mkdir -p "${full_logdir}"
cd "${repo}"
while [[ ! -f "${gate_logdir}/DONE" ]]; do
  if ! pgrep -af run_2000_suffix_gate.sh >/dev/null; then
    echo "gate process ended before DONE" | tee -a "${full_logdir}/sequence.status"
    exit 1
  fi
  sleep 30
done
source /home/ubuntu/venv/bin/activate
MODE=suffixes \
TRACK3_2000_LOG_DIR="${full_logdir}" \
TRACK3_2000_CHECKPOINT=/home/ubuntu/.cache/track3_checkpoints/track3_locom_good2000_seed3710_step2000.pt \
TRACK3_SUFFIX_STEPS=3000 \
TRACK3_SUFFIX_CHECKPOINT_STEPS=2400,2600,2800,3000 \
TRACK3_SUFFIX_LANES=control,floor111,floor111_norm002,floor111_random002,floor111_norm005,floor111_random005,ramp111 \
TRACK3_CHECKPOINT_DIR=/home/ubuntu/.cache/track3_checkpoints \
TRACK3_BASE_CHECKPOINT=/home/ubuntu/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt \
SCREEN_VAL_EVERY=25 \
NPROC_PER_NODE=1 \
bash tools/run_track3_locom_2000_suffix_probe.sh
touch "${full_logdir}/DONE"
