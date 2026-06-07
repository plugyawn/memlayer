#!/usr/bin/env bash
set -euo pipefail

# Guarded Track 3 LocoProp-M mechanism ladder.
#
# This script intentionally does not provision hardware. Run it on an already
# prepared GPU machine with the step-1600 checkpoint and data cache present.
# It executes the remaining "what makes LocoProp tick?" gates in order and
# stops when the evidence says the next stage would be wasteful.

log_root="${TRACK3_TICK_LOG_ROOT:-/root/prime_track3_locom_tick_ladder}"
stop_after="${TRACK3_TICK_STOP_AFTER:-layer_subset}"  # prefix | layer_subset | suffix

mkdir -p "${log_root}"
status_file="${log_root}/tick_ladder.status"

log_status() {
  echo "$*" | tee -a "${status_file}"
}

require_decision() {
  local decision="$1"
  if [[ ! -f "${decision}" ]]; then
    log_status "missing_decision ${decision}"
    exit 2
  fi
}

stage_enabled() {
  local stage="$1"
  case "${stop_after}" in
    prefix)
      [[ "${stage}" == "prefix" ]]
      ;;
    layer_subset)
      [[ "${stage}" == "prefix" || "${stage}" == "layer_subset" ]]
      ;;
    suffix)
      [[ "${stage}" == "prefix" || "${stage}" == "layer_subset" || "${stage}" == "suffix" ]]
      ;;
    *)
      echo "unknown TRACK3_TICK_STOP_AFTER=${stop_after}; expected prefix, layer_subset, or suffix" >&2
      exit 2
      ;;
  esac
}

log_status "tick_ladder_start $(date -u +%Y-%m-%dT%H:%M:%SZ) stop_after=${stop_after}"

if stage_enabled prefix; then
  prefix_dir="${TRACK3_PREFIX_SPEC_LOG_DIR:-${log_root}/prefix_specificity}"
  log_status "stage_start prefix_specificity dir=${prefix_dir}"
  TRACK3_PREFIX_SPEC_LOG_DIR="${prefix_dir}" \
    bash tools/run_track3_locom_prefix_specificity.sh
  if [[ "${TRACK3_DRY_RUN:-0}" == "1" ]]; then
    log_status "dry_run_stop_after_prefix_generation"
    exit 0
  fi
  prefix_decision="${prefix_dir}/track3_prefix_specificity_decision.md"
  require_decision "${prefix_decision}"
  if grep -q "c_fc true-post direction matters in the prefix" "${prefix_decision}"; then
    log_status "stage_pass prefix_specificity"
  else
    log_status "stage_stop prefix_specificity_not_direction_specific decision=${prefix_decision}"
    exit 0
  fi
fi

if [[ "${stop_after}" == "prefix" ]]; then
  log_status "tick_ladder_done_after_prefix $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit 0
fi

if stage_enabled layer_subset; then
  subset_dir="${TRACK3_LAYER_SUBSET_LOG_DIR:-${log_root}/layer_subset}"
  log_status "stage_start layer_subset dir=${subset_dir}"
  TRACK3_LAYER_SUBSET_LOG_DIR="${subset_dir}" \
    bash tools/run_track3_locom_layer_subset_probe.sh
  subset_decision="${subset_dir}/track3_layer_subset_decision.md"
  require_decision "${subset_decision}"
  if grep -Eq "match all-layer active|beat all-layer active" "${subset_decision}"; then
    log_status "stage_pass layer_subset"
  else
    log_status "stage_stop no_static_subset_match decision=${subset_decision}"
    exit 0
  fi
fi

if [[ "${stop_after}" == "layer_subset" ]]; then
  log_status "tick_ladder_done_after_layer_subset $(date -u +%Y-%m-%dT%H:%M:%SZ)"
  exit 0
fi

if stage_enabled suffix; then
  suffix_dir="${TRACK3_2000_LOG_DIR:-${log_root}/suffix_2000}"
  log_status "stage_start suffix_save2000 dir=${suffix_dir}"
  TRACK3_2000_LOG_DIR="${suffix_dir}" \
    MODE=save2000 bash tools/run_track3_locom_2000_suffix_probe.sh
  log_status "stage_start suffix_lanes dir=${suffix_dir}"
  TRACK3_2000_LOG_DIR="${suffix_dir}" \
    MODE=suffixes bash tools/run_track3_locom_2000_suffix_probe.sh
  suffix_decision="${suffix_dir}/track3_locom_2000_suffix_decision.md"
  require_decision "${suffix_decision}"
  if grep -q "Slope read: at least one lane preserves" "${suffix_decision}"; then
    log_status "stage_pass suffix_preserves_slope"
  else
    log_status "stage_stop suffix_does_not_preserve_slope decision=${suffix_decision}"
    exit 0
  fi
fi

log_status "tick_ladder_complete $(date -u +%Y-%m-%dT%H:%M:%SZ)"
