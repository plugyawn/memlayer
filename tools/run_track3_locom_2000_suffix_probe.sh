#!/usr/bin/env bash
set -euo pipefail

# Recreate the good Track 3 LocoProp-M step-2000 state and branch tightly
# controlled suffix probes from it. This script assumes the repo, data cache,
# and the step-1600 checkpoint already exist on the GPU machine. It does not
# provision hardware.
#
# Default MODE=save2000 only produces the checkpoint. Run suffixes explicitly:
#
#   MODE=suffixes tools/run_track3_locom_2000_suffix_probe.sh
#   MODE=all      tools/run_track3_locom_2000_suffix_probe.sh
#
# The current mechanism read says 1900->2000 is healthy, then the power tail
# cools from eta=0.111111 @2000 to eta=0.090000 @2100 and the slope turns cold.
# The default suffix lanes therefore focus on preserving the step-2000 LR
# regime and asking whether LocoProp adds anything after that schedule control.

mode="${MODE:-save2000}"
base_checkpoint="${TRACK3_BASE_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
checkpoint_dir="${TRACK3_CHECKPOINT_DIR:-/root/.cache/track3_checkpoints}"
log_dir="${TRACK3_2000_LOG_DIR:-/root/prime_track3_locom_2000_suffix_logs}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"
generated_dir="${TRACK3_GENERATED_DIR:-/tmp}"
save_prefix="${TRACK3_2000_PREFIX:-track3_locom_good2000}"
state2000="${TRACK3_2000_CHECKPOINT:-${checkpoint_dir}/${save_prefix}_seed${seed_offset}_step2000.pt}"
suffix_steps="${TRACK3_SUFFIX_STEPS:-2400}"
suffix_active_end="${TRACK3_SUFFIX_ACTIVE_END:-2250}"
suffix_lanes="${TRACK3_SUFFIX_LANES:-control,floor111,floor111_norm002,floor111_random002,ramp111}"

mkdir -p "${log_dir}" "${checkpoint_dir}"
python3 tools/check_track3_locom_suffix_manifest.py --manifest-only \
  | tee "${log_dir}/track3_locom_2000_suffix_manifest.md"

run_direct() {
  local label="$1"
  local logfile="${log_dir}/${label}.log"
  shift
  echo "===== ${label} =====" | tee -a "${log_dir}/sequence.status"
  env \
    TRACK3_KDIAG_LABEL="${label}" \
    TRACK3_SOURCE="${source_script}" \
    TRACK3_GENERATED_SCRIPT="${generated_dir}/${label}.py" \
    TRACK3_NUM_TRIALS=1 \
    TRACK3_TARGET_LOSS=3.28 \
    TRACK3_MBS=16 \
    TRACK3_SEED_BASE=0 \
    TRACK3_SEED_OFFSET="${seed_offset}" \
    TRACK3_RESUME_ADVANCE_DATA=1 \
    TRACK3_RESUME_RESTORE_RNG=1 \
    TRACK3_RESUME_LOAD_OPTIMIZERS=1 \
    TRACK3_COOLDOWN_FRAC=1.0 \
    TRACK3_LR_SCHEDULE=power \
    TRACK3_LR_POWER=2.0 \
    TRACK3_LR_SCHEDULE_STEPS=3000 \
    TRACK3_LR_MIN_ETA=0.0 \
    TRACK3_LR_SWITCH_STEP=-1 \
    TRACK3_LR_AFTER_SWITCH= \
    TRACK3_LR_BUMP_WINDOWS= \
    TRACK3_LOCOM_LAYERS=all \
    TRACK3_LOCOM_STEPS=5 \
    TRACK3_LOCOM_INNER_LR=2e-4 \
    TRACK3_LOCOM_TARGET_SPACE=post \
    TRACK3_LOCOM_TRUE_POST_GRAD=1 \
    TRACK3_LOCOM_MIN_COS_DESC=0.0 \
    TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=1 \
    TRACK3_LOCOM_ALPHA=1.0 \
    TRACK3_LOCOM_SAMPLE_TOKENS=1024 \
    TRACK3_LOCOM_NORM_TO_BASE=0 \
    TRACK3_LOCOM_NORM_TARGET=0.0 \
    TRACK3_LOCOM_NORM_CAP=0.20 \
    TRACK3_LOCOM_LOCAL_OPT=sgd \
    TRACK3_LOCOM_RANDOM_CORRECTION=0 \
    TRACK3_LOCOM_CORRECTION_MODE=normal \
    TRACK3_LOCOM_DIAG_STEPS="1,2,4,5,8,10" \
    TRACK3_LOCOM_DIAG_MAX_LAYERS=12 \
    SCREEN_VAL_EVERY=25 \
    NPROC_PER_NODE="${NPROC_PER_NODE:-1}" \
    "$@" \
    bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${logfile}"

  python3 tools/analyze_locom_kdiag.py "${logfile}" > "${log_dir}/${label}.kdiag.md" || true
  python3 tools/analyze_locom_apply_scale.py "${logfile}" > "${log_dir}/${label}.apply_scale.md" || true
}

save2000() {
  if [[ -f "${state2000}" && "${FORCE_2000:-0}" != "1" ]]; then
    echo "state2000_exists ${state2000}" | tee -a "${log_dir}/sequence.status"
    return
  fi
  run_direct "track3_locom_save2000_seed${seed_offset}" \
    TRACK3_TRAIN_STEPS=2000 \
    TRACK3_RESUME_CHECKPOINT="${base_checkpoint}" \
    TRACK3_LOCOM_ENABLED=1 \
    TRACK3_LOCOM_ACTIVE_WINDOWS="0:1800" \
    TRACK3_LOCOM_END_STEP=1800 \
    TRACK3_LOCOM_LOG_STEPS="1600,1625,1700,1750,1800,1900,2000" \
    TRACK3_CHECKPOINT_DIR="${checkpoint_dir}" \
    TRACK3_CHECKPOINT_PREFIX="${save_prefix}" \
    TRACK3_CHECKPOINT_STEPS=2000 \
    TRACK3_CHECKPOINT_EXIT_AFTER=1
  if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
    return
  fi
  if [[ ! -f "${state2000}" ]]; then
    echo "expected checkpoint was not created: ${state2000}" >&2
    exit 1
  fi
}

want_lane() {
  local needle="$1"
  [[ ",${suffix_lanes}," == *",${needle},"* ]]
}

suffix_common() {
  local name="$1"
  shift
  run_direct "track3_locom_2000_${name}_seed${seed_offset}" \
    TRACK3_TRAIN_STEPS="${suffix_steps}" \
    TRACK3_RESUME_CHECKPOINT="${state2000}" \
    TRACK3_LOCOM_LOG_STEPS="2000,2025,2050,2075,2100,2125,2200,2250,2325,2400" \
    TRACK3_CHECKPOINT_DIR="${checkpoint_dir}" \
    TRACK3_CHECKPOINT_PREFIX="track3_locom_2000_${name}_seed${seed_offset}" \
    TRACK3_CHECKPOINT_STEPS="${TRACK3_SUFFIX_CHECKPOINT_STEPS:-2125,2250,2400}" \
    "$@"
}

run_suffixes() {
  if [[ ! -f "${state2000}" ]]; then
    if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
      echo "missing_step2000_checkpoint_dry_run_ok ${state2000}" | tee -a "${log_dir}/sequence.status"
    else
      echo "missing step-2000 checkpoint: ${state2000}" >&2
      echo "run MODE=save2000 first, or set TRACK3_2000_CHECKPOINT" >&2
      exit 1
    fi
  fi

  if want_lane control; then
    suffix_common "control" \
      TRACK3_LOCOM_ENABLED=0 \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}"
  fi

  if want_lane natural; then
    suffix_common "natural_k5" \
      TRACK3_LOCOM_ENABLED=1 \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LOCOM_NORM_TARGET=0.0
  fi

  if want_lane norm002; then
    suffix_common "norm002_k5" \
      TRACK3_LOCOM_ENABLED=1 \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LOCOM_NORM_TARGET=0.02
  fi

  if want_lane random; then
    suffix_common "random_norm002" \
      TRACK3_LOCOM_ENABLED=1 \
      TRACK3_LOCOM_LOCAL_OPT=random \
      TRACK3_LOCOM_RANDOM_CORRECTION=1 \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LOCOM_NORM_TARGET=0.02
  fi

  if want_lane orthogonal; then
    suffix_common "orthogonal_norm002" \
      TRACK3_LOCOM_ENABLED=1 \
      TRACK3_LOCOM_CORRECTION_MODE=orthogonal \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LOCOM_NORM_TARGET=0.02
  fi

  if want_lane parallel; then
    suffix_common "parallel_norm002" \
      TRACK3_LOCOM_ENABLED=1 \
      TRACK3_LOCOM_CORRECTION_MODE=parallel \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LOCOM_NORM_TARGET=0.02
  fi

  if want_lane hold115; then
    suffix_common "hold115" \
      TRACK3_LOCOM_ENABLED=0 \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LR_BUMP_WINDOWS="2000:2050:2250:2400:1.15"
  fi

  if want_lane floor111; then
    suffix_common "floor111" \
      TRACK3_LOCOM_ENABLED=0 \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LR_MIN_ETA=0.1111111111
  fi

  if want_lane floor111_norm002; then
    suffix_common "floor111_norm002_k5" \
      TRACK3_LOCOM_ENABLED=1 \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LOCOM_NORM_TARGET=0.02 \
      TRACK3_LR_MIN_ETA=0.1111111111
  fi

  if want_lane floor111_random002; then
    suffix_common "floor111_random002" \
      TRACK3_LOCOM_ENABLED=1 \
      TRACK3_LOCOM_LOCAL_OPT=random \
      TRACK3_LOCOM_RANDOM_CORRECTION=1 \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LOCOM_NORM_TARGET=0.02 \
      TRACK3_LR_MIN_ETA=0.1111111111
  fi

  if want_lane floor111_orthogonal002; then
    suffix_common "floor111_orthogonal002" \
      TRACK3_LOCOM_ENABLED=1 \
      TRACK3_LOCOM_CORRECTION_MODE=orthogonal \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LOCOM_NORM_TARGET=0.02 \
      TRACK3_LR_MIN_ETA=0.1111111111
  fi

  if want_lane ramp111; then
    suffix_common "ramp111" \
      TRACK3_LOCOM_ENABLED=0 \
      TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${suffix_active_end}" \
      TRACK3_LOCOM_END_STEP="${suffix_active_end}" \
      TRACK3_LR_BUMP_WINDOWS="2000:2250:2250:2400:1.7777777778"
  fi

  local suffix_logs=("${log_dir}"/track3_locom_2000_*.log)
  if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
    echo "suffix_probe_dry_run_no_decision_analysis" | tee -a "${log_dir}/sequence.status"
  elif [[ -e "${suffix_logs[0]}" ]]; then
    python3 tools/check_track3_locom_suffix_manifest.py \
      "${suffix_logs[@]}" | tee "${log_dir}/track3_locom_2000_suffix_manifest_check.md"
    python3 tools/analyze_track3_locom_suffix_probe.py \
      --steps "2000,2025,2050,2075,2100,2125,2200,2250,2325,2400" \
      "${suffix_logs[@]}" | tee "${log_dir}/track3_locom_2000_suffix_decision.md" || true
  fi
}

case "${mode}" in
  save2000)
    save2000
    ;;
  suffixes)
    run_suffixes
    ;;
  all)
    save2000
    run_suffixes
    ;;
  *)
    echo "unsupported MODE=${mode}; use save2000, suffixes, or all" >&2
    exit 2
    ;;
esac

echo "track3_locom_2000_suffix_probe_done mode=${mode} $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | tee -a "${log_dir}/sequence.status"
