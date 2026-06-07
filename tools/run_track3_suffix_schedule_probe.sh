#!/usr/bin/env bash
set -euo pipefail

# Schedule-only Track 3 suffix probes from an existing checkpoint.
#
# This intentionally disables LocoProp-M. It is for testing whether the
# already-good 2000/2125 state can be carried to the target by a better tail
# schedule, without re-spending runs on the 1600-2000 bracket.

checkpoint="${TRACK3_SUFFIX_CHECKPOINT:-/home/ubuntu/.cache/track3_checkpoints/track3_locom_2000_control_seed3710_seed3710_step2125.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
log_dir="${TRACK3_SUFFIX_LOG_DIR:-/home/ubuntu/prime_track3_suffix_schedule_probe_logs}"
train_steps="${TRACK3_TRAIN_STEPS:-2400}"
checkpoint_dir="${TRACK3_CHECKPOINT_DIR:-/home/ubuntu/.cache/track3_checkpoints}"
checkpoint_steps="${TRACK3_CHECKPOINT_STEPS:-2400}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"
lanes="${TRACK3_SUFFIX_LANES:-floor004,floor006,floor008,h3200p2}"

mkdir -p "${log_dir}" "${checkpoint_dir}"

if [[ -f /home/ubuntu/venv/bin/activate ]]; then
  # Prime pods use this venv in our Track 3 setup.
  # shellcheck disable=SC1091
  source /home/ubuntu/venv/bin/activate
fi

if [[ ! -f "${checkpoint}" ]]; then
  echo "missing checkpoint: ${checkpoint}" >&2
  exit 2
fi

common_env=(
  TRACK3_SOURCE="${source_script}"
  TRACK3_NUM_TRIALS=1
  TRACK3_TARGET_LOSS=3.28
  TRACK3_MBS=16
  TRACK3_SEED_BASE=0
  TRACK3_SEED_OFFSET="${seed_offset}"
  TRACK3_RESUME_CHECKPOINT="${checkpoint}"
  TRACK3_RESUME_ADVANCE_DATA=1
  TRACK3_RESUME_RESTORE_RNG=1
  TRACK3_RESUME_LOAD_OPTIMIZERS=1
  TRACK3_TRAIN_STEPS="${train_steps}"
  TRACK3_COOLDOWN_FRAC=1.0
  TRACK3_LR_SCHEDULE=power
  TRACK3_LR_POWER=2.0
  TRACK3_LR_SCHEDULE_STEPS=3000
  TRACK3_LR_MIN_ETA=0.0
  TRACK3_LR_BUMP_WINDOWS=
  TRACK3_LR_SWITCH_STEP=-1
  TRACK3_LR_AFTER_SWITCH=
  TRACK3_LR_BLEND_START=-1
  TRACK3_LR_BLEND_END=-1
  TRACK3_LR_BLEND_TARGET=
  TRACK3_LOCOM_ENABLED=0
  TRACK3_LOCOM_ACTIVE_WINDOWS=
  TRACK3_LOCOM_END_STEP=0
  TRACK3_LOCOM_LAYERS=all
  TRACK3_LOCOM_STEPS=5
  TRACK3_LOCOM_INNER_LR=2e-4
  TRACK3_LOCOM_TARGET_SPACE=post
  TRACK3_LOCOM_TRUE_POST_GRAD=1
  TRACK3_LOCOM_SAMPLE_TOKENS=1024
  TRACK3_LOCOM_DIAG_MAX_LAYERS=0
  TRACK3_CHECKPOINT_DIR="${checkpoint_dir}"
  TRACK3_CHECKPOINT_STEPS="${checkpoint_steps}"
  SCREEN_VAL_EVERY=25
  NPROC_PER_NODE="${NPROC_PER_NODE:-1}"
)

run_lane() {
  local lane="$1"
  shift
  local label="track3_suffix_${lane}_from${TRACK3_SUFFIX_FROM_STEP:-2125}_seed${seed_offset}_to${train_steps}"
  local logfile="${log_dir}/${label}.log"

  echo "===== ${label} =====" | tee -a "${log_dir}/sequence.status"
  env \
    "${common_env[@]}" \
    TRACK3_KDIAG_LABEL="${label}" \
    TRACK3_GENERATED_SCRIPT="/tmp/${label}.py" \
    TRACK3_CHECKPOINT_PREFIX="${label}" \
    "$@" \
    bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${logfile}"
}

IFS=',' read -r -a lane_array <<< "${lanes}"
for lane in "${lane_array[@]}"; do
  case "${lane}" in
    cold3000)
      run_lane "${lane}"
      ;;
    floor004)
      run_lane "${lane}" TRACK3_LR_MIN_ETA=0.04
      ;;
    floor006)
      run_lane "${lane}" TRACK3_LR_MIN_ETA=0.06
      ;;
    floor008)
      run_lane "${lane}" TRACK3_LR_MIN_ETA=0.08
      ;;
    floor010)
      run_lane "${lane}" TRACK3_LR_MIN_ETA=0.10
      ;;
    h3200p2)
      run_lane "${lane}" TRACK3_LR_SCHEDULE_STEPS=3200
      ;;
    h3200p2_floor004)
      run_lane "${lane}" TRACK3_LR_SCHEDULE_STEPS=3200 TRACK3_LR_MIN_ETA=0.04
      ;;
    h3300p2)
      run_lane "${lane}" TRACK3_LR_SCHEDULE_STEPS=3300
      ;;
    h3300p2_floor004)
      run_lane "${lane}" TRACK3_LR_SCHEDULE_STEPS=3300 TRACK3_LR_MIN_ETA=0.04
      ;;
    pr287_h3075p110)
      run_lane "${lane}" TRACK3_LR_SCHEDULE=pr287 TRACK3_LR_SCHEDULE_STEPS=3075 TRACK3_LR_POWER=1.10
      ;;
    pr287_h3105p120)
      run_lane "${lane}" TRACK3_LR_SCHEDULE=pr287 TRACK3_LR_SCHEDULE_STEPS=3105 TRACK3_LR_POWER=1.20
      ;;
    *)
      echo "unknown lane: ${lane}" >&2
      exit 3
      ;;
  esac
done

python3 - <<'PY' "${log_dir}" "${train_steps}" | tee "${log_dir}/summary.tsv"
import re
import sys
from pathlib import Path

log_dir = Path(sys.argv[1])
target_step = int(sys.argv[2])
pat = re.compile(r"step:(\d+)/\d+ val_loss:([0-9.]+)")
print("lane\tlast_step\tlast_val\tval_2200\tval_2250\tval_2300\tval_2400")
for path in sorted(log_dir.glob("track3_suffix_*.log")):
    vals = {}
    for line in path.read_text(errors="ignore").splitlines():
        m = pat.search(line)
        if m:
            vals[int(m.group(1))] = float(m.group(2))
    if not vals:
        continue
    last = max(vals)
    lane = path.stem
    print(
        lane,
        last,
        f"{vals[last]:.5f}",
        f"{vals.get(2200, float('nan')):.5f}",
        f"{vals.get(2250, float('nan')):.5f}",
        f"{vals.get(2300, float('nan')):.5f}",
        f"{vals.get(2400, float('nan')):.5f}",
        sep="\t",
    )
PY

echo "track3_suffix_schedule_probe_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | tee -a "${log_dir}/sequence.status"
