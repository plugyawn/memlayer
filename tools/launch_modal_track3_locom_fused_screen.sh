#!/usr/bin/env bash
set -euo pipefail

steps="${TRACK3_TRAIN_STEPS:-${SCREEN_STEPS:-500}}"
seed_offset="${TRACK3_SEED_OFFSET:-3710}"
aux_seqs="${TRACK3_LOCOM_AUX_SEQS:-16}"
mbs="${TRACK3_MBS:-64}"
run_name="${MODAL_RUN_NAME:-track3-locom-fused${steps}-seed${seed_offset}-$(date -u +%Y%m%d%H%M%S)}"

export TRACK3_TRAIN_STEPS="${steps}"
export SCREEN_STEPS="${steps}"
export TRACK3_NUM_TRIALS="${TRACK3_NUM_TRIALS:-1}"
export TRACK3_SEED_OFFSET="${seed_offset}"
export TRACK3_MBS="${mbs}"
export SCREEN_VAL_EVERY="${SCREEN_VAL_EVERY:-125}"
export TRACK3_LOCOM_ENABLED="${TRACK3_LOCOM_ENABLED:-1}"
export TRACK3_LOCOM_LAYERS="${TRACK3_LOCOM_LAYERS:-all}"
export TRACK3_LOCOM_STEPS="${TRACK3_LOCOM_STEPS:-4}"
export TRACK3_LOCOM_SAMPLE_TOKENS="${TRACK3_LOCOM_SAMPLE_TOKENS:-1024}"
export TRACK3_LOCOM_INNER_LR="${TRACK3_LOCOM_INNER_LR:-0.1}"
export TRACK3_LOCOM_TARGET_GAMMA="${TRACK3_LOCOM_TARGET_GAMMA:-1.0}"
export TRACK3_LOCOM_PROX="${TRACK3_LOCOM_PROX:-0.1}"
export TRACK3_LOCOM_ALPHA="${TRACK3_LOCOM_ALPHA:-1.0}"
export TRACK3_LOCOM_NORM_CAP="${TRACK3_LOCOM_NORM_CAP:-0.20}"
export TRACK3_LOCOM_AUX_CAPTURE="${TRACK3_LOCOM_AUX_CAPTURE:-1}"
export TRACK3_LOCOM_AUX_SEQS="${aux_seqs}"
export TRACK3_LOCOM_BATCHED_PREP="${TRACK3_LOCOM_BATCHED_PREP:-1}"
export TRACK3_LOCOM_LOG_STEPS="${TRACK3_LOCOM_LOG_STEPS:-0,1,2,10,50,125,250,375,500,750,1000,1250,1500,1750,2000,2250,2500,2750,2875,3000}"
export MODAL_RUN_NAME="${run_name}"
export MODAL_DETACH="${MODAL_DETACH:-1}"
export NANOGPT_MODAL_GPU="${NANOGPT_MODAL_GPU:-H100}"

echo "track3_locom_fused_screen run_name=${run_name} steps=${steps} seed_offset=${seed_offset} mbs=${mbs} aux_seqs=${aux_seqs}"
echo "track3_locom_fused_screen aux_capture=${TRACK3_LOCOM_AUX_CAPTURE} batched_prep=${TRACK3_LOCOM_BATCHED_PREP}"

if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
  export TRACK3_GENERATED_SCRIPT="${TRACK3_GENERATED_SCRIPT:-/tmp/train_gpt_simple_locoprop_m_fused_${steps}.py}"
  exec bash tools/run_track3_locoprop_m.sh
fi

exec bash tools/launch_modal_track3_locom_3000_seed.sh
