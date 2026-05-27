#!/usr/bin/env bash
set -euo pipefail

if [[ -n "${MODAL_KEY_ID:-}" && -z "${MODAL_TOKEN_ID:-}" ]]; then
  export MODAL_TOKEN_ID="${MODAL_KEY_ID}"
elif [[ -n "${MODAL_KEY:-}" && -z "${MODAL_TOKEN_ID:-}" ]]; then
  export MODAL_TOKEN_ID="${MODAL_KEY}"
fi
if [[ -n "${MODAL_SECRET:-}" && -z "${MODAL_TOKEN_SECRET:-}" ]]; then
  export MODAL_TOKEN_SECRET="${MODAL_SECRET}"
fi

gpu="${NANOGPT_MODAL_GPU:-${MODAL_GPU:-${MODAL_NANOGPT_GPU:-H100}}}"
case "${gpu}" in
  H100|H100!|GH200) ;;
  *) echo "Only H100/H100! or GH200 are allowed; got MODAL_GPU=${gpu}" >&2; exit 2 ;;
esac
export MODAL_GPU="${gpu}"
export MODAL_NANOGPT_GPU="${gpu}"
export NANOGPT_MODAL_GPU="${gpu}"

if ! command -v modal >/dev/null 2>&1; then
  if [[ -x "tmp/modal-venv/bin/modal" ]]; then
    # shellcheck source=/dev/null
    source tmp/modal-venv/bin/activate
  else
    python3 -m venv tmp/modal-venv
    # shellcheck source=/dev/null
    source tmp/modal-venv/bin/activate
    python -m pip install -q --upgrade pip
    python -m pip install -q modal
  fi
fi

steps="${SCREEN_STEPS:-200}"
val_every="${SCREEN_VAL_EVERY:-50}"
data_chunks="${MODAL_DATA_CHUNKS:-2}"
nproc="${NPROC_PER_NODE:-1}"
runner="${MODAL_RUNNER:-tools/run_newtonv_raw_v01_gate.sh}"
log_path="${LOG_PATH:-}"
extra_env_json="${MODAL_EXTRA_ENV_JSON:-{}}"

args=(
  tools/modal_nanogpt_runner.py::run
  --runner "${runner}"
  --steps "${steps}"
  --val-every "${val_every}"
  --nproc "${nproc}"
  --data-chunks "${data_chunks}"
  --extra-env-json "${extra_env_json}"
)
if [[ -n "${log_path}" ]]; then
  args+=(--log-path "${log_path}")
fi

modal run "${args[@]}"
