#!/usr/bin/env bash
set -euo pipefail

# Package a Track 3 LocoProp-M tick-ladder log directory for copy-back.
# The archive is written next to the log directory by default, so it does not
# recursively include itself.

log_root="${1:-${TRACK3_TICK_LOG_ROOT:-/root/prime_track3_locom_tick_ladder}}"
if [[ ! -d "${log_root}" ]]; then
  echo "missing tick log root: ${log_root}" >&2
  exit 2
fi

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
log_root_abs="$(cd "${log_root}" && pwd)"
parent="$(dirname "${log_root_abs}")"
base="$(basename "${log_root_abs}")"
archive="${TRACK3_TICK_ARCHIVE:-${parent}/${base}_${timestamp}.tar.gz}"
manifest="${log_root_abs}/tick_artifact_manifest.txt"

{
  echo "created_utc=${timestamp}"
  echo "log_root=${log_root_abs}"
  echo "archive=${archive}"
  echo "cwd=$(pwd)"
  if git rev-parse --show-toplevel >/dev/null 2>&1; then
    echo "git_root=$(git rev-parse --show-toplevel)"
    echo "git_head=$(git rev-parse HEAD)"
    echo "git_branch=$(git rev-parse --abbrev-ref HEAD)"
    echo "git_status_short_begin"
    git status --short
    echo "git_status_short_end"
  fi
  echo "uname=$(uname -a)"
  if command -v nvidia-smi >/dev/null 2>&1; then
    echo "nvidia_smi_query_begin"
    nvidia-smi --query-gpu=name,pci.bus_id,memory.total,driver_version --format=csv,noheader || true
    echo "nvidia_smi_query_end"
  fi
  echo "files_begin"
  (
    cd "${log_root_abs}"
    find . -type f | sed 's#^\./##' | LC_ALL=C sort
  )
  echo "files_end"
} > "${manifest}"

tar -C "${parent}" -czf "${archive}" "${base}"
echo "${archive}"
