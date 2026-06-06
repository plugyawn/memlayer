#!/usr/bin/env bash
set -euo pipefail

# Run a narrow LocoProp-M K-ladder probe from the known step-1600 Track 3
# checkpoint. This assumes the repo, data cache, and checkpoint already exist on
# the machine. It intentionally does not provision GPUs.

profile="${TRACK3_KDIAG_PROFILE:-post-approx-k10-alpha0}"
label="${TRACK3_KDIAG_LABEL:-track3_locom_kdiag_${profile}}"
log_dir="${TRACK3_KDIAG_LOG_DIR:-/root/prime_track3_logs}"
mkdir -p "${log_dir}"

export TRACK3_SOURCE="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"
export TRACK3_GENERATED_SCRIPT="${TRACK3_GENERATED_SCRIPT:-/tmp/${label}.py}"
export TRACK3_NUM_TRIALS="${TRACK3_NUM_TRIALS:-1}"
export TRACK3_TRAIN_STEPS="${TRACK3_TRAIN_STEPS:-1625}"
export TRACK3_TARGET_LOSS="${TRACK3_TARGET_LOSS:-3.28}"
export TRACK3_MBS="${TRACK3_MBS:-16}"
export TRACK3_SEED_BASE="${TRACK3_SEED_BASE:-0}"
export TRACK3_SEED_OFFSET="${TRACK3_SEED_OFFSET:-3710}"
export TRACK3_RESUME_CHECKPOINT="${TRACK3_RESUME_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
export TRACK3_RESUME_ADVANCE_DATA="${TRACK3_RESUME_ADVANCE_DATA:-1}"
export TRACK3_RESUME_RESTORE_RNG="${TRACK3_RESUME_RESTORE_RNG:-1}"
export TRACK3_RESUME_LOAD_OPTIMIZERS="${TRACK3_RESUME_LOAD_OPTIMIZERS:-1}"
export TRACK3_LOCOM_ENABLED="${TRACK3_LOCOM_ENABLED:-1}"
export TRACK3_LOCOM_LAYERS="${TRACK3_LOCOM_LAYERS:-all}"
export TRACK3_LOCOM_SAMPLE_TOKENS="${TRACK3_LOCOM_SAMPLE_TOKENS:-1024}"
export TRACK3_LOCOM_PROX="${TRACK3_LOCOM_PROX:-0.1}"
export TRACK3_LOCOM_NORM_CAP="${TRACK3_LOCOM_NORM_CAP:-0.20}"
export TRACK3_LOCOM_ACTIVE_WINDOWS="${TRACK3_LOCOM_ACTIVE_WINDOWS:-0:1800}"
export TRACK3_LOCOM_END_STEP="${TRACK3_LOCOM_END_STEP:-1800}"
export TRACK3_LOCOM_LOG_STEPS="${TRACK3_LOCOM_LOG_STEPS:-1600,1625,1750,1800,2000,2125}"
export TRACK3_LOCOM_DIAG_STEPS="${TRACK3_LOCOM_DIAG_STEPS:-1,2,4,5,8,10}"
export TRACK3_LOCOM_DIAG_MAX_LAYERS="${TRACK3_LOCOM_DIAG_MAX_LAYERS:-12}"
export SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-25}"
export NPROC_PER_NODE="${NPROC_PER_NODE:-1}"

case "${profile}" in
  post-approx-k10-alpha0)
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-0.1}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-0}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-0.0}"
    ;;
  post-true-k10-alpha0)
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-1e-5}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-1}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-0.0}"
    ;;
  post-true-k10-lr1e4-alpha0)
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-1e-4}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-1}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-0.0}"
    ;;
  post-true-k10-lr2e4-alpha0)
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-2e-4}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-1}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-0.0}"
    ;;
  post-true-k10-lr3e4-alpha0)
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-3e-4}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-1}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-0.0}"
    ;;
  post-true-k10-lr1e3-alpha0)
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-1e-3}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-1}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-0.0}"
    ;;
  pre-k10-alpha0)
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-0.1}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-pre}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-0}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-0.0}"
    ;;
  post-approx-k10-fixedtime-active)
    export TRACK3_TRAIN_STEPS="${TRACK3_TRAIN_STEPS:-1800}"
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-0.04}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-0}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-1.0}"
    ;;
  pre-k10-fixedtime-active)
    export TRACK3_TRAIN_STEPS="${TRACK3_TRAIN_STEPS:-1800}"
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-0.04}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-pre}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-0}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-1.0}"
    ;;
  post-true-k10-lr3e4-active-poscos)
    export TRACK3_TRAIN_STEPS="${TRACK3_TRAIN_STEPS:-1800}"
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-3e-4}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-1}"
    export TRACK3_LOCOM_MIN_COS_DESC="${TRACK3_LOCOM_MIN_COS_DESC:-0.0}"
    export TRACK3_LOCOM_REQUIRE_LOSS_DECREASE="${TRACK3_LOCOM_REQUIRE_LOSS_DECREASE:-1}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-1.0}"
    ;;
  post-true-k10-lr2e4-active-poscos)
    export TRACK3_TRAIN_STEPS="${TRACK3_TRAIN_STEPS:-1800}"
    export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-10}"
    export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-2e-4}"
    export TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}"
    export TRACK3_LOCOM_TRUE_POST_GRAD="${TRACK3_LOCOM_TRUE_POST_GRAD:-1}"
    export TRACK3_LOCOM_MIN_COS_DESC="${TRACK3_LOCOM_MIN_COS_DESC:-0.0}"
    export TRACK3_LOCOM_REQUIRE_LOSS_DECREASE="${TRACK3_LOCOM_REQUIRE_LOSS_DECREASE:-1}"
    export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-1.0}"
    ;;
  *)
    echo "unsupported TRACK3_KDIAG_PROFILE=${profile}" >&2
    echo "profiles: post-approx-k10-alpha0 post-true-k10-alpha0 post-true-k10-lr1e4-alpha0 post-true-k10-lr2e4-alpha0 post-true-k10-lr3e4-alpha0 post-true-k10-lr1e3-alpha0 pre-k10-alpha0 post-approx-k10-fixedtime-active pre-k10-fixedtime-active post-true-k10-lr2e4-active-poscos post-true-k10-lr3e4-active-poscos" >&2
    exit 2
    ;;
esac

echo "track3_locom_kdiag_profile=${profile} label=${label}"
echo "log=${log_dir}/${label}.log"
bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${log_dir}/${label}.log"
python3 tools/analyze_locom_kdiag.py "${log_dir}/${label}.log" | tee "${log_dir}/${label}.kdiag.md"
