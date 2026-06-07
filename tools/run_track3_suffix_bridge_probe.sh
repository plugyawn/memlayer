#!/usr/bin/env bash
set -euo pipefail

# Track 3 suffix bridge probes from an existing post-prefix checkpoint.
#
# This runner intentionally does not recreate the 1600->2000 prefix. It starts
# from a saved 2000/2125/2400/2600 checkpoint and tests whether a delayed,
# smooth LR bridge can carry the already-good state to 3.28.

checkpoint="${TRACK3_SUFFIX_CHECKPOINT:-/home/ubuntu/.cache/track3_checkpoints/track3_noloco_ckpt2125_seed3710_seed3710_step2125.pt}"
from_step="${TRACK3_SUFFIX_FROM_STEP:-2125}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
log_dir="${TRACK3_SUFFIX_LOG_DIR:-/home/ubuntu/prime_track3_suffix_bridge_probe_logs}"
train_steps="${TRACK3_TRAIN_STEPS:-3000}"
checkpoint_dir="${TRACK3_CHECKPOINT_DIR:-/home/ubuntu/.cache/track3_checkpoints}"
checkpoint_steps="${TRACK3_CHECKPOINT_STEPS:-2400,2600,2800,3000}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/train_gpt_simple.py}"
lanes="${TRACK3_SUFFIX_LANES:-cold3000,bump125_2250_2650,bump150_2250_2650,blend_p15_2250_2650,blend_p13_2300_2750,pulse175_2400_2750}"
gate_step="${TRACK3_GATE_STEP:-2400}"
gate_loss="${TRACK3_GATE_LOSS:-3.3365}"

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
  TRACK3_LR_BLEND_TARGET_POWER=2.0
  TRACK3_LR_BLEND_TARGET_STEPS=3000
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
  local label="track3_suffix_bridge_${lane}_from${from_step}_seed${seed_offset}_to${train_steps}"
  local logfile="${log_dir}/${label}.log"

  echo "===== ${label} =====" | tee -a "${log_dir}/sequence.status"
  env \
    "${common_env[@]}" \
    TRACK3_KDIAG_LABEL="${label}" \
    TRACK3_GENERATED_SCRIPT="/tmp/${label}.py" \
    TRACK3_CHECKPOINT_PREFIX="${label}" \
    "$@" \
    bash tools/run_track3_locoprop_m.sh 2>&1 | tee "${logfile}"

  python3 - <<'PY' "${logfile}" "${gate_step}" "${gate_loss}" | tee -a "${log_dir}/sequence.status"
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

IFS=',' read -r -a lane_array <<< "${lanes}"
for lane in "${lane_array[@]}"; do
  case "${lane}" in
    cold3000)
      run_lane "${lane}"
      ;;
    bump125_2250_2650)
      run_lane "${lane}" TRACK3_LR_BUMP_WINDOWS="2250:2400:2650:3000:1.25"
      ;;
    bump150_2250_2650)
      run_lane "${lane}" TRACK3_LR_BUMP_WINDOWS="2250:2400:2650:3000:1.50"
      ;;
    bump175_2300_2700)
      run_lane "${lane}" TRACK3_LR_BUMP_WINDOWS="2300:2450:2700:3000:1.75"
      ;;
    pulse175_2400_2750)
      run_lane "${lane}" TRACK3_LR_BUMP_WINDOWS="2400:2500:2750:3000:1.75"
      ;;
    blend_p15_2250_2650)
      run_lane "${lane}" \
        TRACK3_LR_BLEND_START=2250 \
        TRACK3_LR_BLEND_END=2650 \
        TRACK3_LR_BLEND_TARGET=power \
        TRACK3_LR_BLEND_TARGET_POWER=1.50 \
        TRACK3_LR_BLEND_TARGET_STEPS=3000
      ;;
    blend_p13_2300_2750)
      run_lane "${lane}" \
        TRACK3_LR_BLEND_START=2300 \
        TRACK3_LR_BLEND_END=2750 \
        TRACK3_LR_BLEND_TARGET=power \
        TRACK3_LR_BLEND_TARGET_POWER=1.30 \
        TRACK3_LR_BLEND_TARGET_STEPS=3000
      ;;
    blend_p15_2400_2800)
      run_lane "${lane}" \
        TRACK3_LR_BLEND_START=2400 \
        TRACK3_LR_BLEND_END=2800 \
        TRACK3_LR_BLEND_TARGET=power \
        TRACK3_LR_BLEND_TARGET_POWER=1.50 \
        TRACK3_LR_BLEND_TARGET_STEPS=3000
      ;;
    *)
      echo "unknown lane: ${lane}" >&2
      exit 3
      ;;
  esac
done

python3 tools/analyze_track3_locom_lr_slope.py \
  --steps "${TRACK3_ANALYZE_STEPS:-${from_step},2250,2400,2600,2800,3000}" \
  --target-step "${TRACK3_TARGET_STEP:-3000}" \
  --target-loss 3.28 \
  "${log_dir}" | tee "${log_dir}/lr_slope.md" || true

echo "track3_suffix_bridge_probe_done $(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | tee -a "${log_dir}/sequence.status"
