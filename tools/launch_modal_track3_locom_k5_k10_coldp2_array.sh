#!/usr/bin/env bash
set -euo pipefail

# Isolate the "what makes LocoProp-M tick?" question with a cheap 1600->1800
# screen from the known good checkpoint.
#
# The prior K-ladder says true-post K10 at inner_lr=2e-4 is locally sane and
# externally useful, but it does not prove that ten local steps are required.
# These lanes separate:
#   - K count: 5 vs 8 vs 10
#   - correction scale/local time: K5 at 2e-4 vs K5 at 3e-4
#
# Stop at 1800 by default. If a K5 lane matches K10 at 1800, it is the first
# speed path because the hook path is dominated by local-solve work.

checkpoint="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
gpu="${NANOGPT_MODAL_GPU:-H100}"
steps="${TRACK3_TRAIN_STEPS:-1800}"
stamp="${KSCREEN_STAMP:-$(date -u +%Y%m%d%H%M%S)}"

mkdir -p .opencode/active_launch_logs

launch_lane() {
  local name="$1"
  local local_steps="$2"
  local inner_lr="$3"

  local run_name="track3-locom-${name}-coldp2-screen${steps}-seed${seed_offset}-${stamp}"
  local log_path=".opencode/active_launch_logs/modal_${run_name}.launch.log"

  echo "===== launching ${run_name} =====" | tee "${log_path}"
  (
    extra_env_json="$(python3 - <<PY
import json

extra = {
    "TRACK3_KDIAG_PROFILE": "post-true-k10-lr2e4-active-poscos",
    "TRACK3_KDIAG_LABEL": "track3_kdiag_post-true-${name}-coldp2-screen${steps}",
    "TRACK3_TRAIN_STEPS": "${steps}",
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
    "TRACK3_LR_MIN_ETA": "0.0",
    "TRACK3_LR_SWITCH_STEP": "-1",
    "TRACK3_LR_AFTER_SWITCH": "",
    "TRACK3_LR_BUMP_WINDOWS": "",
    "TRACK3_LOCOM_ENABLED": "1",
    "TRACK3_LOCOM_LAYERS": "all",
    "TRACK3_LOCOM_STEPS": "${local_steps}",
    "TRACK3_LOCOM_INNER_LR": "${inner_lr}",
    "TRACK3_LOCOM_TARGET_SPACE": "post",
    "TRACK3_LOCOM_TRUE_POST_GRAD": "1",
    "TRACK3_LOCOM_MIN_COS_DESC": "0.0",
    "TRACK3_LOCOM_REQUIRE_LOSS_DECREASE": "1",
    "TRACK3_LOCOM_ALPHA": "1.0",
    "TRACK3_LOCOM_SAMPLE_TOKENS": "1024",
    "TRACK3_LOCOM_NORM_TARGET": "0.0",
    "TRACK3_LOCOM_NORM_TO_BASE": "0",
    "TRACK3_LOCOM_NORM_CAP": "0.20",
    "TRACK3_LOCOM_ACTIVE_WINDOWS": "0:${steps}",
    "TRACK3_LOCOM_END_STEP": "${steps}",
    "TRACK3_LOCOM_LOG_STEPS": "1600,1625,1650,1675,1700,1725,1750,1775,1800",
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
    export SCREEN_STEPS="${steps}"
    export SCREEN_VAL_EVERY="25"
    export NPROC_PER_NODE="1"
    export MODAL_EXTRA_ENV_JSON="${extra_env_json}"

    exec bash tools/run_modal_newtonv_raw_gate.sh
  ) 2>&1 | tee -a "${log_path}"
}

# Controls and scale-matched variants.
launch_lane "k10-lr2e4" "10" "2e-4"
launch_lane "k8-lr2e4" "8" "2e-4"
launch_lane "k5-lr2e4" "5" "2e-4"
launch_lane "k5-lr3e4" "5" "3e-4"
