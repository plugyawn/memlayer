#!/usr/bin/env bash
set -euo pipefail

# Run short LocoProp-M tick diagnostics from the known-flat Track 3 step-2500
# checkpoint.  This is intentionally checkpoint-native and short-gated: it asks
# whether a larger, ungated LocoProp correction can move the late flat tail at
# all, without re-spending the 1600-2500 prefix.

cd "${TRACK3_REMOTE_REPO:-/root/wr-track3-locom-20260606}"
source .venv/bin/activate

checkpoint="${TRACK3_TAIL2500_CHECKPOINT:-/root/.cache/track3_checkpoints/track3_suffix_cold3000_from2000_seed3710_to2500_seed3710_step2500.pt}"
log_dir="${TRACK3_TAIL2500_LOG_DIR:-/root/prime_track3_locom_tail2500_tick_logs_43ad37}"
checkpoint_dir="${TRACK3_CHECKPOINT_DIR:-/root/.cache/track3_checkpoints}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
train_steps="${TRACK3_TRAIN_STEPS:-2600}"
lanes="${TRACK3_TAIL2500_LANES:-ungated_norm005}"

mkdir -p "${log_dir}" "${checkpoint_dir}"

if [[ ! -f "${checkpoint}" ]]; then
  echo "missing checkpoint: ${checkpoint}" >&2
  exit 2
fi

run_lane() {
  local lane="$1"
  shift
  local label="track3_locom_tail2500_${lane}_seed${seed_offset}_to${train_steps}"
  local logfile="${log_dir}/${label}.log"
  echo "===== ${label} =====" | tee -a "${log_dir}/sequence.status"
  env \
    TRACK3_KDIAG_LABEL="${label}" \
    TRACK3_SOURCE=records/track_3_optimization/train_gpt_simple.py \
    TRACK3_GENERATED_SCRIPT="/tmp/${label}.py" \
    TRACK3_NUM_TRIALS=1 \
    TRACK3_TARGET_LOSS=3.28 \
    TRACK3_MBS=16 \
    TRACK3_SEED_BASE=0 \
    TRACK3_SEED_OFFSET="${seed_offset}" \
    TRACK3_RESUME_CHECKPOINT="${checkpoint}" \
    TRACK3_RESUME_ADVANCE_DATA=1 \
    TRACK3_RESUME_RESTORE_RNG=1 \
    TRACK3_RESUME_LOAD_OPTIMIZERS=1 \
    TRACK3_TRAIN_STEPS="${train_steps}" \
    TRACK3_COOLDOWN_FRAC=1.0 \
    TRACK3_LR_SCHEDULE=power \
    TRACK3_LR_POWER=2.0 \
    TRACK3_LR_SCHEDULE_STEPS=3000 \
    TRACK3_LR_MIN_ETA=0.0 \
    TRACK3_LR_BUMP_WINDOWS= \
    TRACK3_LR_SWITCH_STEP=-1 \
    TRACK3_LR_AFTER_SWITCH= \
    TRACK3_LR_BLEND_START=-1 \
    TRACK3_LR_BLEND_END=-1 \
    TRACK3_LR_BLEND_TARGET= \
    TRACK3_LOCOM_ENABLED=1 \
    TRACK3_LOCOM_LAYERS=all \
    TRACK3_LOCOM_STEPS=5 \
    TRACK3_LOCOM_INNER_LR=2e-4 \
    TRACK3_LOCOM_TARGET_SPACE=post \
    TRACK3_LOCOM_TRUE_POST_GRAD=1 \
    TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=0 \
    TRACK3_LOCOM_MIN_COS_DESC=-inf \
    TRACK3_LOCOM_ALPHA=1.0 \
    TRACK3_LOCOM_SAMPLE_TOKENS=1024 \
    TRACK3_LOCOM_NORM_TO_BASE=0 \
    TRACK3_LOCOM_NORM_TARGET=0.05 \
    TRACK3_LOCOM_NORM_CAP=0.20 \
    TRACK3_LOCOM_LOCAL_OPT=sgd \
    TRACK3_LOCOM_RANDOM_CORRECTION=0 \
    TRACK3_LOCOM_CORRECTION_MODE=normal \
    TRACK3_LOCOM_ACTIVE_WINDOWS=2500:2600 \
    TRACK3_LOCOM_END_STEP=2600 \
    TRACK3_LOCOM_LOG_STEPS=2500,2501,2525,2550,2575,2600 \
    TRACK3_LOCOM_DIAG_STEPS=1,2,4,5 \
    TRACK3_LOCOM_DIAG_MAX_LAYERS=12 \
    TRACK3_CHECKPOINT_DIR="${checkpoint_dir}" \
    TRACK3_CHECKPOINT_PREFIX="${label}" \
    TRACK3_CHECKPOINT_STEPS=2600 \
    SCREEN_VAL_EVERY=25 \
    NPROC_PER_NODE=1 \
    "$@" \
    bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${logfile}"

  python3 tools/analyze_locom_kdiag.py "${logfile}" > "${log_dir}/${label}.kdiag.md" || true
  python3 tools/analyze_locom_apply_scale.py "${logfile}" > "${log_dir}/${label}.apply_scale.md" || true
}

IFS=',' read -r -a lane_array <<< "${lanes}"
for lane in "${lane_array[@]}"; do
  case "${lane}" in
    ungated_norm005)
      run_lane "${lane}"
      ;;
    ungated_softpolar_norm005)
      run_lane "${lane}" TRACK3_LOCOM_CORRECTION_MODE=softpolar
      ;;
    ungated_polar_norm005)
      run_lane "${lane}" TRACK3_LOCOM_CORRECTION_MODE=polar
      ;;
    random_norm005)
      run_lane "${lane}" TRACK3_LOCOM_LOCAL_OPT=random TRACK3_LOCOM_RANDOM_CORRECTION=1
      ;;
    *)
      echo "unknown lane: ${lane}" >&2
      exit 3
      ;;
  esac
done

python3 - <<'PY' "${log_dir}" | tee "${log_dir}/summary.tsv"
import re
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
pat = re.compile(r"step:(\d+)/\d+ val_loss:([0-9.]+)")
print("lane\tlast_step\tlast_val\tval_2525\tval_2550\tval_2575\tval_2600")
for path in sorted(log_dir.glob("track3_locom_tail2500_*.log")):
    vals = {}
    for line in path.read_text(errors="ignore").splitlines():
        m = pat.search(line)
        if m:
            vals[int(m.group(1))] = float(m.group(2))
    if not vals:
        continue
    last = max(vals)
    print(
        path.stem,
        last,
        f"{vals[last]:.5f}",
        f"{vals.get(2525, float('nan')):.5f}",
        f"{vals.get(2550, float('nan')):.5f}",
        f"{vals.get(2575, float('nan')):.5f}",
        f"{vals.get(2600, float('nan')):.5f}",
        sep="\t",
    )
PY

echo "track3_locom_tail2500_tick_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | tee -a "${log_dir}/sequence.status"
