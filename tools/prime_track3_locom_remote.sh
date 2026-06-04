#!/usr/bin/env bash
set -euo pipefail

repo_dir="${REPO_DIR:-/root/wr-fresh-20260526}"
label="${RUN_LABEL:-track3_locom_nm}"
steps="${TRACK3_TRAIN_STEPS:-3300}"
trials="${TRACK3_NUM_TRIALS:-2}"
nproc="${NPROC_PER_NODE:-1}"
data_chunks="${TRACK3_DATA_CHUNKS:-20}"
target_loss="${TRACK3_TARGET_LOSS:-3.28}"
source_script="${TRACK3_SOURCE:-records/track_3_optimization/results/20260505_newton_muon/train_gpt_simple_newton_muon.py}"

export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export HF_HOME="${HF_HOME:-/root/.cache/huggingface}"
export XDG_CACHE_HOME="${XDG_CACHE_HOME:-/root/.cache/xdg}"
export TRITON_CACHE_DIR="${TRITON_CACHE_DIR:-/root/.cache/triton}"
export TORCHINDUCTOR_CACHE_DIR="${TORCHINDUCTOR_CACHE_DIR:-/root/.cache/torchinductor-track3-locom-nm-${nproc}x}"

mkdir -p /root/prime_track3_logs
cd "${repo_dir}"

if [[ ! -x /root/venv/bin/python ]]; then
  apt-get update
  apt-get install -y --no-install-recommends python3 python3-venv python3-pip git ca-certificates curl
  python3 -m venv /root/venv
fi

source /root/venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q --index-url https://download.pytorch.org/whl/cu126 torch==2.7.1
python -m pip install -q numpy tqdm huggingface-hub typing-extensions setuptools

python data/cached_fineweb10B.py "${data_chunks}" > "/root/prime_track3_logs/${label}_cache_fineweb_${data_chunks}.log" 2>&1
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader > "/root/prime_track3_logs/${label}_gpu.txt" 2>&1 || true

generated="/root/prime_track3_logs/${label}_train_gpt_simple_locom.py"
TRACK3_SOURCE="${source_script}" \
TRACK3_GENERATED_SCRIPT="${generated}" \
TRACK3_TRAIN_STEPS="${steps}" \
TRACK3_DRY_RUN=1 \
tools/run_track3_locoprop_m.sh > "/root/prime_track3_logs/${label}_generate.log" 2>&1

run_log="/root/prime_track3_logs/${label}.log"
status_file="/root/prime_track3_logs/${label}.status"
{
  printf 'started %s\n' "$(date -Is)"
  printf 'repo=%s commit=%s\n' "${repo_dir}" "$(git rev-parse --short HEAD 2>/dev/null || true)"
  printf 'label=%s nproc=%s steps=%s trials=%s target=%s data_chunks=%s source=%s\n' \
    "${label}" "${nproc}" "${steps}" "${trials}" "${target_loss}" "${data_chunks}" "${source_script}"
  printf 'locom layers=%s K=%s sample_tokens=%s inner_lr=%s prox=%s alpha=%s norm_cap=%s mbs=%s gather=%s accum=%s\n' \
    "${TRACK3_LOCOM_LAYERS:-all}" "${TRACK3_LOCOM_STEPS:-4}" "${TRACK3_LOCOM_SAMPLE_TOKENS:-1024}" \
    "${TRACK3_LOCOM_INNER_LR:-0.1}" "${TRACK3_LOCOM_PROX:-0.1}" "${TRACK3_LOCOM_ALPHA:-1.0}" \
    "${TRACK3_LOCOM_NORM_CAP:-0.20}" "${TRACK3_MBS:-16}" "${TRACK3_LOCOM_GATHER_SAMPLES:-1}" \
    "${TRACK3_LOCOM_ACCUM_SAMPLES:-0}"
  printf 'locom aux_capture=%s aux_seqs=%s active_windows=%s norm_cap_windows=%s\n' \
    "${TRACK3_LOCOM_AUX_CAPTURE:-0}" "${TRACK3_LOCOM_AUX_SEQS:-16}" \
    "${TRACK3_LOCOM_ACTIVE_WINDOWS:-}" "${TRACK3_LOCOM_NORM_CAP_WINDOWS:-}"
  printf 'locom batched_prep=%s local_opt=%s target_space=%s\n' \
    "${TRACK3_LOCOM_BATCHED_PREP:-0}" "${TRACK3_LOCOM_LOCAL_OPT:-sgd}" \
    "${TRACK3_LOCOM_TARGET_SPACE:-post}"
} | tee "${status_file}"

env \
  TRACK3_SOURCE="${source_script}" \
  TRACK3_GENERATED_SCRIPT="${generated}" \
  TRACK3_TRAIN_STEPS="${steps}" \
  TRACK3_NUM_TRIALS="${trials}" \
  TRACK3_TARGET_LOSS="${target_loss}" \
  TRACK3_MBS="${TRACK3_MBS:-16}" \
  TRACK3_LOCOM_LAYERS="${TRACK3_LOCOM_LAYERS:-all}" \
  TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-4}" \
  TRACK3_LOCOM_SAMPLE_TOKENS="${TRACK3_LOCOM_SAMPLE_TOKENS:-1024}" \
  TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-0.1}" \
  TRACK3_LOCOM_TARGET_GAMMA="${TRACK3_LOCOM_TARGET_GAMMA:-1.0}" \
  TRACK3_LOCOM_PROX="${TRACK3_LOCOM_PROX:-0.1}" \
  TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-1.0}" \
  TRACK3_LOCOM_NORM_CAP="${TRACK3_LOCOM_NORM_CAP:-0.20}" \
  TRACK3_LOCOM_NORM_TO_BASE="${TRACK3_LOCOM_NORM_TO_BASE:-0}" \
  TRACK3_LOCOM_NORM_TARGET="${TRACK3_LOCOM_NORM_TARGET:-0.0}" \
  TRACK3_LOCOM_GATHER_SAMPLES="${TRACK3_LOCOM_GATHER_SAMPLES:-1}" \
  TRACK3_LOCOM_ACCUM_SAMPLES="${TRACK3_LOCOM_ACCUM_SAMPLES:-0}" \
  TRACK3_LOCOM_MICRO_SAMPLE_TOKENS="${TRACK3_LOCOM_MICRO_SAMPLE_TOKENS:-32}" \
  TRACK3_LOCOM_AUX_CAPTURE="${TRACK3_LOCOM_AUX_CAPTURE:-0}" \
  TRACK3_LOCOM_AUX_SEQS="${TRACK3_LOCOM_AUX_SEQS:-16}" \
  TRACK3_LOCOM_BATCHED_PREP="${TRACK3_LOCOM_BATCHED_PREP:-0}" \
  TRACK3_LOCOM_ACTIVE_WINDOWS="${TRACK3_LOCOM_ACTIVE_WINDOWS:-}" \
  TRACK3_LOCOM_NORM_CAP_WINDOWS="${TRACK3_LOCOM_NORM_CAP_WINDOWS:-}" \
  TRACK3_LOCOM_START_STEP="${TRACK3_LOCOM_START_STEP:-0}" \
  TRACK3_LOCOM_END_STEP="${TRACK3_LOCOM_END_STEP:-1000000000}" \
  TRACK3_LOCOM_INTERVAL="${TRACK3_LOCOM_INTERVAL:-1}" \
  TRACK3_LOCOM_LOCAL_OPT="${TRACK3_LOCOM_LOCAL_OPT:-sgd}" \
  TRACK3_LOCOM_TARGET_SPACE="${TRACK3_LOCOM_TARGET_SPACE:-post}" \
  TRACK3_LOCOM_RANDOM_CORRECTION="${TRACK3_LOCOM_RANDOM_CORRECTION:-0}" \
  TRACK3_LOCOM_LOCAL_LR_DECAY="${TRACK3_LOCOM_LOCAL_LR_DECAY:-0}" \
  TRACK3_LOCOM_RMS_BETA1="${TRACK3_LOCOM_RMS_BETA1:-0.999}" \
  TRACK3_LOCOM_RMS_BETA2="${TRACK3_LOCOM_RMS_BETA2:-0.9}" \
  TRACK3_LOCOM_RMS_EPS="${TRACK3_LOCOM_RMS_EPS:-1e-5}" \
  TRACK3_LOCOM_RMS_RESET_EACH_STEP="${TRACK3_LOCOM_RMS_RESET_EACH_STEP:-0}" \
  TRACK3_LOCOM_REQUIRE_LOSS_DECREASE="${TRACK3_LOCOM_REQUIRE_LOSS_DECREASE:-0}" \
  TRACK3_LOCOM_MIN_COS_DESC="${TRACK3_LOCOM_MIN_COS_DESC:--inf}" \
  TRACK3_LOCOM_LOG_STEPS="${TRACK3_LOCOM_LOG_STEPS:-0,1,2,10,50,125,250,500}" \
  TRACK3_SEED_BASE="${TRACK3_SEED_BASE:-0}" \
  TRACK3_SEED_OFFSET="${TRACK3_SEED_OFFSET:-0}" \
  TRACK3_RESET_TRIAL_SEED="${TRACK3_RESET_TRIAL_SEED:-1}" \
  TRACK3_COOLDOWN_FRAC="${TRACK3_COOLDOWN_FRAC:-0.7}" \
  TRACK3_LR_SCHEDULE="${TRACK3_LR_SCHEDULE:-linear}" \
  TRACK3_LR_POWER="${TRACK3_LR_POWER:-1.0}" \
  TRACK3_LR_SCHEDULE_STEPS="${TRACK3_LR_SCHEDULE_STEPS:-0}" \
  TRACK3_LR_MIN_ETA="${TRACK3_LR_MIN_ETA:-0.0}" \
  TRACK3_LR_BUMP_WINDOWS="${TRACK3_LR_BUMP_WINDOWS:-}" \
  TRACK3_LR_SWITCH_STEP="${TRACK3_LR_SWITCH_STEP:--1}" \
  TRACK3_LR_AFTER_SWITCH="${TRACK3_LR_AFTER_SWITCH:-}" \
  TRACK3_LR_AFTER_SWITCH_POWER="${TRACK3_LR_AFTER_SWITCH_POWER:-${TRACK3_LR_POWER:-1.0}}" \
  TRACK3_LR_AFTER_SWITCH_STEPS="${TRACK3_LR_AFTER_SWITCH_STEPS:-0}" \
  TRACK3_LR_BLEND_START="${TRACK3_LR_BLEND_START:--1}" \
  TRACK3_LR_BLEND_END="${TRACK3_LR_BLEND_END:--1}" \
  TRACK3_LR_BLEND_TARGET="${TRACK3_LR_BLEND_TARGET:-}" \
  TRACK3_LR_BLEND_TARGET_POWER="${TRACK3_LR_BLEND_TARGET_POWER:-${TRACK3_LR_POWER:-1.0}}" \
  TRACK3_LR_BLEND_TARGET_STEPS="${TRACK3_LR_BLEND_TARGET_STEPS:-0}" \
  TRACK3_SOFT_MUON="${TRACK3_SOFT_MUON:-0}" \
  TRACK3_SOFT_MUON_BLEND="${TRACK3_SOFT_MUON_BLEND:-1.0}" \
  TRACK3_SOFT_MUON_NORM_RESTORE="${TRACK3_SOFT_MUON_NORM_RESTORE:-1}" \
  TRACK3_SOFT_MUON_START_STEP="${TRACK3_SOFT_MUON_START_STEP:--1}" \
  TRACK3_SOFT_MUON_END_STEP="${TRACK3_SOFT_MUON_END_STEP:--1}" \
  TRACK3_SOFT_MUON_CEIL="${TRACK3_SOFT_MUON_CEIL:-1.0}" \
  TRACK3_CHECKPOINT_STEPS="${TRACK3_CHECKPOINT_STEPS:-}" \
  TRACK3_CHECKPOINT_DIR="${TRACK3_CHECKPOINT_DIR:-}" \
  TRACK3_CHECKPOINT_PREFIX="${TRACK3_CHECKPOINT_PREFIX:-track3_locom}" \
  TRACK3_CHECKPOINT_EXIT_AFTER="${TRACK3_CHECKPOINT_EXIT_AFTER:-0}" \
  TRACK3_RESUME_CHECKPOINT="${TRACK3_RESUME_CHECKPOINT:-}" \
  TRACK3_RESUME_ADVANCE_DATA="${TRACK3_RESUME_ADVANCE_DATA:-1}" \
  TRACK3_RESUME_RESTORE_RNG="${TRACK3_RESUME_RESTORE_RNG:-1}" \
  TRACK3_RESUME_LOAD_OPTIMIZERS="${TRACK3_RESUME_LOAD_OPTIMIZERS:-1}" \
  SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-125}" \
  NPROC_PER_NODE="${nproc}" \
  bash tools/run_track3_locoprop_m.sh > "${run_log}" 2>&1

rc=$?
printf 'finished %s rc=%s\n' "$(date -Is)" "${rc}" | tee -a "${status_file}"
touch "/root/prime_track3_logs/${label}.DONE"
exit "${rc}"
