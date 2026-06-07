#!/usr/bin/env bash
set -euo pipefail

# Focused Track 3 suffix probe from the saved step-2000 state.
#
# Hypothesis: the late tail is starving Muon matrices specifically. Preserve a
# Muon-only eta floor around the step-2250 band while leaving Adam-like groups
# on the cold power schedule. Run matched alpha-zero controls before spending
# on a LocoProp-M correction.

checkpoint="${TRACK3_SUFFIX_CHECKPOINT:-/home/ubuntu/.cache/track3_checkpoints/track3_locom_good2000_seed3710_step2000.pt}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
log_dir="${TRACK3_SUFFIX_LOG_DIR:-/home/ubuntu/prime_track3_muon_budget_from2000_logs}"
train_steps="${TRACK3_TRAIN_STEPS:-2600}"
checkpoint_dir="${TRACK3_CHECKPOINT_DIR:-/home/ubuntu/.cache/track3_checkpoints}"
checkpoint_steps="${TRACK3_CHECKPOINT_STEPS:-2250,2400,2500,2600}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"
lanes="${TRACK3_SUFFIX_LANES:-cold_control,muon_floor006,muon_floor006_locom002}"
gate_step="${TRACK3_GATE_STEP:-2400}"
gate_loss="${TRACK3_GATE_LOSS:-3.34480}"
stop_locom_on_floor_fail="${TRACK3_STOP_LOCOM_ON_FLOOR_FAIL:-1}"

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
  TRACK3_LR_MIN_ETA_WINDOWS=
  TRACK3_LR_ADAM_MIN_ETA_WINDOWS=
  TRACK3_LR_MUON_MIN_ETA_WINDOWS=
  TRACK3_LR_BUMP_WINDOWS=
  TRACK3_LR_ADAM_BUMP_WINDOWS=
  TRACK3_LR_MUON_BUMP_WINDOWS=
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

gate_lane() {
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
    ok = vals[gate_step] <= gate_loss
    print(f"gate_{'PASS' if ok else 'FAIL'} {path.stem} step={gate_step} val={vals[gate_step]:.5f} threshold={gate_loss:.5f}")
    sys.exit(0 if ok else 10)
last = max(vals) if vals else -1
print(f"gate_MISSING {path.stem} step={gate_step} last_step={last}")
sys.exit(11)
PY
}

run_lane() {
  local lane="$1"
  shift
  local label="track3_muon_budget_${lane}_from2000_seed${seed_offset}_to${train_steps}"
  local logfile="${log_dir}/${label}.log"

  echo "===== ${label} =====" | tee -a "${log_dir}/sequence.status"
  env \
    "${common_env[@]}" \
    TRACK3_KDIAG_LABEL="${label}" \
    TRACK3_GENERATED_SCRIPT="/tmp/${label}.py" \
    TRACK3_CHECKPOINT_PREFIX="${label}" \
    "$@" \
    bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${logfile}"
  gate_lane "${logfile}"
}

muon_floor_window="${TRACK3_MUON_FLOOR_WINDOW:-2000:2125:2600:3000:0.06}"
floor_ok=0

IFS=',' read -r -a lane_array <<< "${lanes}"
for lane in "${lane_array[@]}"; do
  case "${lane}" in
    cold_control)
      run_lane "${lane}" || true
      ;;
    muon_floor006)
      if run_lane "${lane}" TRACK3_LR_MUON_MIN_ETA_WINDOWS="${muon_floor_window}"; then
        floor_ok=1
      else
        floor_ok=0
      fi
      ;;
    muon_floor006_locom002)
      if [[ "${stop_locom_on_floor_fail}" == "1" && "${floor_ok}" != "1" ]]; then
        echo "skip ${lane}: muon_floor006 failed gate" | tee -a "${log_dir}/sequence.status"
        continue
      fi
      run_lane "${lane}" \
        TRACK3_LR_MUON_MIN_ETA_WINDOWS="${muon_floor_window}" \
        TRACK3_LOCOM_ENABLED=1 \
        TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${train_steps}" \
        TRACK3_LOCOM_END_STEP="${train_steps}" \
        TRACK3_LOCOM_NORM_TARGET=0.02 \
        TRACK3_LOCOM_LOG_STEPS=2000,2125,2250,2400,2500,2600 \
        TRACK3_LOCOM_DIAG_STEPS=2000,2125,2250,2400,2500,2600 || true
      ;;
    muon_floor006_locom005)
      if [[ "${stop_locom_on_floor_fail}" == "1" && "${floor_ok}" != "1" ]]; then
        echo "skip ${lane}: muon_floor006 failed gate" | tee -a "${log_dir}/sequence.status"
        continue
      fi
      run_lane "${lane}" \
        TRACK3_LR_MUON_MIN_ETA_WINDOWS="${muon_floor_window}" \
        TRACK3_LOCOM_ENABLED=1 \
        TRACK3_LOCOM_ACTIVE_WINDOWS="2000:${train_steps}" \
        TRACK3_LOCOM_END_STEP="${train_steps}" \
        TRACK3_LOCOM_NORM_TARGET=0.05 \
        TRACK3_LOCOM_LOG_STEPS=2000,2125,2250,2400,2500,2600 \
        TRACK3_LOCOM_DIAG_STEPS=2000,2125,2250,2400,2500,2600 || true
      ;;
    *)
      echo "unknown lane: ${lane}" >&2
      exit 3
      ;;
  esac
done

python3 tools/analyze_track3_locom_lr_slope.py \
  --steps "${TRACK3_ANALYZE_STEPS:-2000,2125,2250,2400,2500,2600}" \
  --target-step "${TRACK3_TARGET_STEP:-3000}" \
  --target-loss 3.28 \
  "${log_dir}" | tee "${log_dir}/lr_slope.md" || true

echo "track3_muon_budget_probe_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | tee -a "${log_dir}/sequence.status"
