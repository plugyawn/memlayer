#!/usr/bin/env bash
set -euo pipefail

# Late Track 3 suffix probes from a saved 2400 checkpoint.
#
# This deliberately avoids 1600->2000 replay. It tests whether the missing
# 3.34/3.32 -> 3.28 movement is primarily a tail schedule problem. The first
# lane should normally be `linear3000_noloco`; only run the LocoProp/random
# controls if that lane is close enough to the 2500/2600 gate.

checkpoint="${TRACK3_SUFFIX_CHECKPOINT:-/home/ubuntu/.cache/track3_checkpoints/track3_short2000_wr3105p120_mult035_hold2400_seed3710_step2400.pt}"
from_step="${TRACK3_SUFFIX_FROM_STEP:-2400}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
log_dir="${TRACK3_SUFFIX_LOG_DIR:-/home/ubuntu/prime_track3_late_linear_probe_logs}"
train_steps="${TRACK3_TRAIN_STEPS:-2600}"
schedule_steps="${TRACK3_LR_SCHEDULE_STEPS:-3000}"
checkpoint_dir="${TRACK3_CHECKPOINT_DIR:-/home/ubuntu/.cache/track3_checkpoints}"
checkpoint_steps="${TRACK3_CHECKPOINT_STEPS:-2500,2600}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"
lanes="${TRACK3_SUFFIX_LANES:-linear3000_noloco}"
gate_step="${TRACK3_GATE_STEP:-2500}"
gate_loss="${TRACK3_GATE_LOSS:-3.3345}"

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
  TRACK3_COOLDOWN_FRAC=0.7
  TRACK3_LR_SCHEDULE=linear
  TRACK3_LR_POWER=1.0
  TRACK3_LR_SCHEDULE_STEPS="${schedule_steps}"
  TRACK3_LR_MIN_ETA=0.0
  TRACK3_LR_BUMP_WINDOWS=
  TRACK3_LR_SWITCH_STEP=-1
  TRACK3_LR_AFTER_SWITCH=
  TRACK3_LR_BLEND_START=-1
  TRACK3_LR_BLEND_END=-1
  TRACK3_LR_BLEND_TARGET=
  TRACK3_LOCOM_LAYERS=all
  TRACK3_LOCOM_STEPS=4
  TRACK3_LOCOM_INNER_LR=0.1
  TRACK3_LOCOM_TARGET_GAMMA=1.0
  TRACK3_LOCOM_PROX=0.1
  TRACK3_LOCOM_TARGET_SPACE=post
  TRACK3_LOCOM_TRUE_POST_GRAD=0
  TRACK3_LOCOM_MIN_COS_DESC=-inf
  TRACK3_LOCOM_REQUIRE_LOSS_DECREASE=0
  TRACK3_LOCOM_ALPHA=1.0
  TRACK3_LOCOM_SAMPLE_TOKENS=1024
  TRACK3_LOCOM_NORM_TO_BASE=0
  TRACK3_LOCOM_NORM_TARGET=0.0
  TRACK3_LOCOM_NORM_CAP=0.20
  TRACK3_LOCOM_LOCAL_OPT=sgd
  TRACK3_LOCOM_RANDOM_CORRECTION=0
  TRACK3_LOCOM_CORRECTION_MODE=normal
  TRACK3_LOCOM_ACTIVE_WINDOWS="${from_step}:3000"
  TRACK3_LOCOM_END_STEP=3000
  TRACK3_LOCOM_LOG_STEPS="${from_step},2425,2450,2475,2500,2550,2600,2700,2750,2800,2875,3000"
  TRACK3_LOCOM_DIAG_STEPS=
  TRACK3_LOCOM_DIAG_MAX_LAYERS=4
  TRACK3_CHECKPOINT_DIR="${checkpoint_dir}"
  TRACK3_CHECKPOINT_STEPS="${checkpoint_steps}"
  SCREEN_VAL_EVERY=25
  NPROC_PER_NODE="${NPROC_PER_NODE:-1}"
)

summarize_gate() {
  python3 - <<'PY' "$1" "${gate_step}" "${gate_loss}" | tee -a "${log_dir}/sequence.status"
import re
import sys
from pathlib import Path

path = Path(sys.argv[1])
gate_step = int(sys.argv[2])
gate_loss = float(sys.argv[3])
pat = re.compile(r"step:(\d+)/\d+ val_loss:([0-9.]+)")
vals = {}
for line in path.read_text(errors="ignore").splitlines():
    m = pat.search(line)
    if m:
        vals[int(m.group(1))] = float(m.group(2))
if gate_step in vals:
    status = "PASS" if vals[gate_step] <= gate_loss else "FAIL"
    print(f"gate_{status} {path.stem} step={gate_step} val={vals[gate_step]:.5f} threshold={gate_loss:.5f}")
else:
    last = max(vals) if vals else -1
    print(f"gate_MISSING {path.stem} step={gate_step} last_step={last}")
PY
}

run_lane() {
  local lane="$1"
  shift
  local label="track3_late_${lane}_h${schedule_steps}_from${from_step}_seed${seed_offset}_to${train_steps}"
  local logfile="${log_dir}/${label}.log"

  echo "===== ${label} =====" | tee -a "${log_dir}/sequence.status"
  env \
    "${common_env[@]}" \
    TRACK3_KDIAG_LABEL="${label}" \
    TRACK3_GENERATED_SCRIPT="/tmp/${label}.py" \
    TRACK3_CHECKPOINT_PREFIX="${label}" \
    "$@" \
    bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${logfile}"
  summarize_gate "${logfile}"
}

IFS=',' read -r -a lane_array <<< "${lanes}"
for lane in "${lane_array[@]}"; do
  case "${lane}" in
    linear3000_noloco)
      run_lane "${lane}" TRACK3_LOCOM_ENABLED=0 TRACK3_LOCOM_ACTIVE_WINDOWS="${from_step}:${from_step}" TRACK3_LOCOM_END_STEP="${from_step}"
      ;;
    linear3000_k4)
      run_lane "${lane}" TRACK3_LOCOM_ENABLED=1 TRACK3_LOCOM_LOCAL_OPT=sgd TRACK3_LOCOM_RANDOM_CORRECTION=0
      ;;
    linear3000_random)
      run_lane "${lane}" TRACK3_LOCOM_ENABLED=1 TRACK3_LOCOM_LOCAL_OPT=random TRACK3_LOCOM_RANDOM_CORRECTION=1
      ;;
    linear3100_noloco)
      run_lane "${lane}" TRACK3_LOCOM_ENABLED=0 TRACK3_LOCOM_ACTIVE_WINDOWS="${from_step}:${from_step}" TRACK3_LOCOM_END_STEP="${from_step}" TRACK3_TRAIN_STEPS=3100 TRACK3_LR_SCHEDULE_STEPS=3100
      ;;
    linear3100_k4)
      run_lane "${lane}" TRACK3_LOCOM_ENABLED=1 TRACK3_TRAIN_STEPS=3100 TRACK3_LR_SCHEDULE_STEPS=3100
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
print("lane\tlast_step\tlast_val\tval_2400\tval_2450\tval_2500\tval_2550\tval_2600")
for path in sorted(log_dir.glob("track3_late_*.log")):
    vals = {}
    for line in path.read_text(errors="ignore").splitlines():
        m = pat.search(line)
        if m:
            vals[int(m.group(1))] = float(m.group(2))
    if not vals:
        continue
    last = max(vals)
    fields = [
        path.stem,
        str(last),
        f"{vals[last]:.5f}",
        f"{vals.get(2400, float('nan')):.5f}",
        f"{vals.get(2450, float('nan')):.5f}",
        f"{vals.get(2500, float('nan')):.5f}",
        f"{vals.get(2550, float('nan')):.5f}",
        f"{vals.get(2600, float('nan')):.5f}",
    ]
    print("\t".join(fields))
PY

echo "track3_late_linear_probe_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | tee -a "${log_dir}/sequence.status"
