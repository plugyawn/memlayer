#!/usr/bin/env bash
set -euo pipefail

# Targeted suffix probes for the corrected cold power-2 Track 3 LocoProp-M lane.
#
# Evidence so far:
# - coldp2 + true-post K10 LocoProp-M reaches ~3.3987 at step 1800.
# - The raw coldp2 schedule has enough slope through ~2000, then the LR eta
#   collapses and the run becomes slope-starved.
# - sample_tokens=2048 matched 1024, so the next lever is the post-1800 LR tail,
#   not more local-solve sampling.
#
# These lanes preserve the exact LocoProp primitive through step 1800 and only
# alter the late LR tail. They intentionally use the kdiag runner, not the
# generic launcher, so TRACK3_LOCOM_TRUE_POST_GRAD and diagnostics are preserved.

checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
gpu="${NANOGPT_MODAL_GPU:-H100}"
stamp="${TAIL_FLOOR_STAMP:-$(date -u +%Y%m%d%H%M%S)}"

mkdir -p .opencode/active_launch_logs

launch_lane() {
  local name="$1"
  local lr_min_eta="$2"
  local bump_windows="$3"

  local run_name="track3-coldp2-tail-${name}-seed${seed_offset}-${stamp}"
  local log_path=".opencode/active_launch_logs/modal_${run_name}.launch.log"

  echo "===== launching ${run_name} =====" | tee "${log_path}"
  (
    extra_env_json="$(python3 - <<PY
import json

extra = {
    "TRACK3_KDIAG_PROFILE": "post-true-k10-lr2e4-active-poscos",
    "TRACK3_KDIAG_LABEL": "track3_kdiag_post-true-k10-lr2e4-coldp2-tail-${name}",
    "TRACK3_TRAIN_STEPS": "3000",
    "TRACK3_NUM_TRIALS": "1",
    "TRACK3_TARGET_LOSS": "3.28",
    "TRACK3_SOURCE": "records/track_3_optimization/train_gpt_simple.py",
    "TRACK3_MBS": "16",
    "TRACK3_SEED_BASE": "0",
    "TRACK3_SEED_OFFSET": "${seed_offset}",
    "TRACK3_RESUME_CHECKPOINT": "${checkpoint}",
    "TRACK3_RESUME_ADVANCE_DATA": "1",
    "TRACK3_RESUME_RESTORE_RNG": "1",
    "TRACK3_RESUME_LOAD_OPTIMIZERS": "1",
    "TRACK3_COOLDOWN_FRAC": "1.0",
    "TRACK3_LR_SCHEDULE": "power",
    "TRACK3_LR_POWER": "2.0",
    "TRACK3_LR_SCHEDULE_STEPS": "3000",
    "TRACK3_LR_MIN_ETA": "${lr_min_eta}",
    "TRACK3_LR_SWITCH_STEP": "-1",
    "TRACK3_LR_AFTER_SWITCH": "",
    "TRACK3_LR_BUMP_WINDOWS": "${bump_windows}",
    "TRACK3_LOCOM_ENABLED": "1",
    "TRACK3_LOCOM_LAYERS": "all",
    "TRACK3_LOCOM_STEPS": "10",
    "TRACK3_LOCOM_INNER_LR": "2e-4",
    "TRACK3_LOCOM_TARGET_SPACE": "post",
    "TRACK3_LOCOM_TRUE_POST_GRAD": "1",
    "TRACK3_LOCOM_MIN_COS_DESC": "0.0",
    "TRACK3_LOCOM_REQUIRE_LOSS_DECREASE": "1",
    "TRACK3_LOCOM_ALPHA": "1.0",
    "TRACK3_LOCOM_SAMPLE_TOKENS": "1024",
    "TRACK3_LOCOM_NORM_TARGET": "0.0",
    "TRACK3_LOCOM_NORM_TO_BASE": "0",
    "TRACK3_LOCOM_NORM_CAP": "0.20",
    "TRACK3_LOCOM_ACTIVE_WINDOWS": "0:1800",
    "TRACK3_LOCOM_END_STEP": "1800",
    "TRACK3_LOCOM_LOG_STEPS": "1600,1625,1650,1675,1700,1725,1750,1775,1800,1900,2000,2125,2250,2375,2400,2450,2500,2625,2750,2875,3000",
    "TRACK3_LOCOM_DIAG_STEPS": "1,2,4,5,8,10",
    "TRACK3_LOCOM_DIAG_MAX_LAYERS": "12",
    "SCREEN_VAL_EVERY": "25",
    "NPROC_PER_NODE": "1",
}
print(json.dumps(extra, separators=(",", ":")))
PY
)"

    export PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION="${PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION:-python}"
    export NANOGPT_MODAL_GPU="${gpu}"
    export MODAL_GPU="${gpu}"
    export MODAL_NANOGPT_GPU="${gpu}"
    export MODAL_DETACH="${MODAL_DETACH:-1}"
    export MODAL_ENTRYPOINT="${MODAL_ENTRYPOINT:-run_spawn}"
    export MODAL_RUN_NAME="${run_name}"
    export MODAL_RUNNER="tools/run_track3_locom_kdiag_probe.sh"
    export MODAL_DATA_CHUNKS="${MODAL_DATA_CHUNKS:-20}"
    export SCREEN_STEPS="3000"
    export SCREEN_VAL_EVERY="25"
    export NPROC_PER_NODE="1"
    export MODAL_EXTRA_ENV_JSON="${extra_env_json}"

    exec bash tools/run_modal_newtonv_raw_gate.sh
  ) 2>&1 | tee -a "${log_path}"
}

# True eta floors. These are the cleanest test of whether the coldp2 tail simply
# runs out of learning rate after step ~2000.
launch_lane "floor006" "0.06" ""
launch_lane "floor008" "0.08" ""

# Smooth holds that keep the effective eta near 0.10/0.08 through the vulnerable
# 2000-2500 region, then let the run cool again. They are intentionally modest:
# the prior hard rewarm probes hurt when they restored full WR-like LR.
launch_lane "hold010-2000-2400" "0.0" "2000:2125:2400:2600:2.50"
launch_lane "hold008-2000-2500" "0.0" "2000:2125:2500:2750:2.88"
