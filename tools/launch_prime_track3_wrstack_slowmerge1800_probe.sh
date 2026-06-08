#!/usr/bin/env bash
set -euo pipefail

# Launch Prime H100 suffix probes from the saved step-1800 LocoProp/coldp2
# checkpoint. Each lane resumes model+Adam, initializes fresh current-record
# WR optimizer2 state, and slowly ramps optimizer2 LR from alpha_min to 1.0.

workspace="${WORKSPACE:-$(pwd)}"
env_file="${PRIME_ENV_FILE:-/Users/progyan/speedrun/env.local}"
ledger="${PRIME_LEDGER:-${workspace}/.opencode/prime-gpu-ledger.md}"
pod_name="${PRIME_POD_NAME:-oc-main-track3-wrslow1800-h100-$(date -u +%Y%m%d-%H%M)}"
remote_repo="${REMOTE_REPO:-/root/wr-track3-locom-20260606}"
remote_logdir="${REMOTE_LOGDIR:-/root/prime_track3_wrslowmerge1800_logs}"
remote_ckpt_dir="${REMOTE_CKPT_DIR:-/root/.cache/track3_checkpoints}"
known_hosts="${PRIME_KNOWN_HOSTS:-${workspace}/.opencode/prime_known_hosts_wrslow1800}"
disk_size_gb="${PRIME_DISK_SIZE_GB:-500}"
min_balance="${PRIME_MIN_BALANCE_USD:-2.00}"
gpu_type="${PRIME_GPU_TYPE:-H100_80GB}"
gpu_socket_filter="${PRIME_GPU_SOCKET:-}"
allow_spot="${PRIME_ALLOW_SPOT:-1}"
availability_override="${PRIME_AVAILABILITY_ID:-}"
local_ckpt="${LOCAL_CKPT:-/Users/progyan/speedrun/tmp/prime_wrstack_from1800_checkpoints/track3_k5_coldp2_seed3710_to1800_seed3710_step1800.pt}"
remote_ckpt="${remote_ckpt_dir}/track3_k5_coldp2_seed3710_to1800_seed3710_step1800.pt"

if [[ ! -f "${env_file}" ]]; then
  echo "missing env file: ${env_file}" >&2
  exit 2
fi
if [[ ! -f "${local_ckpt}" ]]; then
  echo "missing local checkpoint: ${local_ckpt}" >&2
  exit 2
fi

export PRIME_API_KEY="${PRIME_API_KEY:-$(python3 - "${env_file}" <<'PY'
import sys
from pathlib import Path

values = {}
for line in Path(sys.argv[1]).read_text(errors="replace").splitlines():
    s = line.strip()
    if not s or s.startswith("#") or "=" not in s:
        continue
    k, v = s.split("=", 1)
    values[k.strip().removeprefix("export ").strip()] = v.strip().strip("\"").strip("'")
print(values.get("PRIME_API_KEY") or values.get("PRIME_KEY") or "")
PY
)}"
if [[ -z "${PRIME_API_KEY}" ]]; then
  echo "PRIME_API_KEY/PRIME_KEY is not set" >&2
  exit 2
fi
export PRIME_DISABLE_VERSION_CHECK=1

cd "${workspace}"
head_sha="$(git rev-parse --short HEAD)"

parse_prime_ssh_target() {
  python3 - "$1" <<'PY'
import shlex
import sys

target = sys.argv[1].strip()
parts = shlex.split(target)
if parts and parts[0] == "ssh":
    parts = parts[1:]
host = ""
port = ""
i = 0
while i < len(parts):
    part = parts[i]
    if part in ("-p", "-P") and i + 1 < len(parts):
        port = parts[i + 1]
        i += 2
        continue
    if part.startswith("-p") and len(part) > 2:
        port = part[2:]
        i += 1
        continue
    if part.startswith("-"):
        i += 1
        continue
    if not host:
        host = part
    i += 1
if not host:
    raise SystemExit(f"could not parse ssh host from: {target!r}")
print(host, port)
PY
}

ssh_remote() {
  local host port
  read -r host port < <(parse_prime_ssh_target "$1")
  shift
  if [[ -n "${port}" ]]; then
    ssh -p "${port}" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="${known_hosts}" -o ConnectTimeout=15 "$host" "$@"
  else
    ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="${known_hosts}" -o ConnectTimeout=15 "$host" "$@"
  fi
}

scp_to_remote() {
  local target="$1"
  local src="$2"
  local dst="$3"
  local host port
  read -r host port < <(parse_prime_ssh_target "${target}")
  if [[ -n "${port}" ]]; then
    scp -P "${port}" -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="${known_hosts}" "${src}" "${host}:${dst}"
  else
    scp -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="${known_hosts}" "${src}" "${host}:${dst}"
  fi
}

prime --plain switch personal >/dev/null

wallet_json="$(prime --plain wallet --limit 1 --output json)"
balance="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["balance_usd"])' <<<"${wallet_json}")"
python3 - "${balance}" "${min_balance}" <<'PY'
import sys
balance = float(sys.argv[1])
minimum = float(sys.argv[2])
if balance < minimum:
    raise SystemExit(f"personal wallet balance {balance:.4f} is below minimum {minimum:.2f}; not launching")
PY

pods_json="$(prime --plain pods list --output json)"
active_count="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["total_count"])' <<<"${pods_json}")"
if [[ "${active_count}" != "0" ]]; then
  echo "Prime personal context already has ${active_count} active pod(s); inspect before launching." >&2
  exit 3
fi

availability_json="$(prime --plain availability list --gpu-type "${gpu_type}" --gpu-count 1 --output json)"
if [[ -n "${availability_override}" ]]; then
  availability_id="${availability_override}"
else
  availability_id="$(
    python3 -c '
import json, sys
socket_filter = sys.argv[1].upper()
allow_spot = sys.argv[2] != "0"
rows = json.load(sys.stdin).get("gpu_resources", [])
rows = [
    r for r in rows
    if r.get("stock_status") == "Available"
    and (not socket_filter or str(r.get("socket", "")).upper().startswith(socket_filter))
    and (allow_spot or not bool(r.get("is_spot")))
]
if not rows:
    raise SystemExit("no available GPU rows matching socket filter")
rows.sort(key=lambda r: (float(r.get("price_value", 1e9)), not bool(r.get("is_spot"))))
print(rows[0]["id"])
' "${gpu_socket_filter}" "${allow_spot}" <<<"${availability_json}"
  )"
fi
availability_desc="$(
  python3 -c '
import json, sys
target = sys.argv[1]
for r in json.load(sys.stdin).get("gpu_resources", []):
    if r.get("id") == target:
        print("{} {} {} {}".format(r.get("gpu_type"), r.get("socket"), r.get("provider"), r.get("price_per_hour")))
        break
' "${availability_id}" <<<"${availability_json}"
)"
if [[ -z "${availability_desc}" ]]; then
  echo "availability id ${availability_id} was not present in availability list" >&2
  exit 2
fi

pod_id=""
run_started=0
cleanup_pod_on_error() {
  local ec=$?
  trap - ERR
  if [[ "${run_started}" != "1" && -n "${pod_id}" ]]; then
    echo "setup failed; terminating owned pod ${pod_id}" >&2
    prime --plain pods terminate "${pod_id}" --yes >/dev/null 2>&1 || true
  fi
  exit "${ec}"
}
trap cleanup_pod_on_error ERR

echo "launching pod name=${pod_name} availability=${availability_id} ${availability_desc} disk=${disk_size_gb}GB head=${head_sha}"
prime --plain pods create --id "${availability_id}" --name "${pod_name}" --disk-size "${disk_size_gb}" --yes

pod_id="$(
  prime --plain pods list --output json | python3 -c '
import json, sys
name = sys.argv[1]
matches = [p for p in json.load(sys.stdin).get("pods", []) if p.get("name") == name]
if not matches:
    raise SystemExit(f"pod named {name!r} not found after create")
print(matches[0]["id"])
' "${pod_name}"
)"

created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
mkdir -p "$(dirname "${ledger}")"
cat >>"${ledger}" <<EOF

- pod_id: ${pod_id}
  name: ${pod_name}
  owner: current-agent
  purpose: Track 3 WR optimizer2 slow-merge from saved step1800 checkpoint, lanes alpha20/alpha00/alpha35
  gpu: ${availability_desc}
  price_per_hour: selected by availability id ${availability_id}
  created_at: ${created_at}
  expected_stop: after slow-merge logs/state diagnostics through 2500 are pulled
  status: launched_by_${0##*/}_head_${head_sha}
  termination_policy: terminate after comparison artifacts are collected; do not leave idle
EOF

ssh_target=""
for _ in $(seq 1 150); do
  status_json="$(prime --plain pods status "${pod_id}" --output json 2>/dev/null || true)"
  ssh_target="$(
    python3 -c '
import json, sys
text = sys.stdin.read()
if not text.strip():
    raise SystemExit
data = json.loads(text)
ssh = data.get("ssh") or ""
ip = data.get("ip") or ""
if ssh and ssh != "N/A":
    print(ssh)
elif ip and ip != "N/A":
    print(f"root@{ip}")
' <<<"${status_json}"
  )" || true
  if [[ -n "${ssh_target}" ]]; then
    if ssh_remote "${ssh_target}" true >/dev/null 2>&1; then
      break
    fi
  fi
  sleep 10
done

if [[ -z "${ssh_target}" ]]; then
  echo "pod ${pod_id} did not become SSH-ready; terminating owned pod" >&2
  prime --plain pods terminate "${pod_id}" --yes >/dev/null 2>&1 || true
  exit 4
fi

status_dir="${workspace}/.opencode/current_track3_ledger_20260608_logs/wrslowmerge1800_${pod_id}"
mkdir -p "${status_dir}"
cat >"${status_dir}/pod.env" <<EOF
pod_id=${pod_id}
name=${pod_name}
gpu=${availability_desc}
ssh_target=${ssh_target}
remote_logdir=${remote_logdir}
remote_ckpt_dir=${remote_ckpt_dir}
known_hosts=${known_hosts}
head=${head_sha}
EOF

echo "syncing git HEAD ${head_sha} to ${ssh_target}:${remote_repo}"
git archive --format=tar HEAD | ssh_remote "${ssh_target}" \
  "rm -rf '${remote_repo}' && mkdir -p '${remote_repo}' && tar -xf - -C '${remote_repo}'"

echo "copying checkpoint to ${ssh_target}:${remote_ckpt}"
ssh_remote "${ssh_target}" "mkdir -p '${remote_ckpt_dir}' '${remote_logdir}'"
scp_to_remote "${ssh_target}" "${local_ckpt}" "${remote_ckpt}"

echo "writing remote slow-merge run"
ssh_remote "${ssh_target}" "cat > '${remote_logdir}/run_wrslowmerge1800.sh'" <<REMOTE_SCRIPT
#!/usr/bin/env bash
set -euo pipefail

repo=${remote_repo}
logdir=${remote_logdir}
ckpt_dir=${remote_ckpt_dir}
ckpt1800=${remote_ckpt}

export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export HF_HOME=/root/.cache/huggingface
export XDG_CACHE_HOME=/root/.cache/xdg
export TRITON_CACHE_DIR=/root/.cache/triton
export TORCHINDUCTOR_CACHE_DIR=/root/.cache/torchinductor-track3-wrslow1800

mkdir -p "\${logdir}" "\${ckpt_dir}"
cd "\${repo}"

if [[ ! -x /root/venv/bin/python ]]; then
  apt-get update
  apt-get install -y --no-install-recommends python3 python3-dev python3-venv python3-pip build-essential git ca-certificates curl
  python3 -m venv /root/venv
fi

source /root/venv/bin/activate
python -m pip install -q --upgrade pip
python -m pip install -q --index-url https://download.pytorch.org/whl/cu126 torch==2.7.1
python -m pip install -q numpy tqdm huggingface-hub typing-extensions setuptools

python data/cached_fineweb10B.py 20 > "\${logdir}/cache_fineweb.log" 2>&1
nvidia-smi --query-gpu=name,memory.total,pci.bus_id --format=csv,noheader > "\${logdir}/gpu.txt" 2>&1 || true
python - <<'PY' > "\${logdir}/torch_env.txt"
import torch
print("torch", torch.__version__)
print("cuda", torch.version.cuda)
print("device", torch.cuda.get_device_name(0))
print("capability", torch.cuda.get_device_capability(0))
PY

run_lane() {
  local label="\$1"
  local alpha_min="\$2"
  local ramp_end="\$3"
  echo "stage=\${label} start=\$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee "\${logdir}/RUNNING"
  WR_TRAIN_STEPS=2500 \\
  WR_SCHEDULE_STEPS=3105 \\
  WR_SEED=3710 \\
  WR_RESUME_CHECKPOINT="\${ckpt1800}" \\
  WR_RESUME_LOAD_ADAM=1 \\
  WR_RESUME_LOAD_OPTIMIZERS=0 \\
  WR_RESUME_ADVANCE_DATA=1 \\
  WR_RESUME_RESTORE_RNG=1 \\
  WR_OPT2_LR_MULT_START=1800 \\
  WR_OPT2_LR_MULT_END="\${ramp_end}" \\
  WR_OPT2_LR_MULT_MIN="\${alpha_min}" \\
  WR_OPT2_LR_MULT_MAX=1.0 \\
  WR_SAVE_CHECKPOINT="\${ckpt_dir}/wrslow_\${label}_seed3710_step{step}.pt" \\
  WR_SAVE_CHECKPOINT_STEPS=2000,2125,2250,2375,2500 \\
  WR_TARGET_LOSS=0 \\
  NPROC_PER_NODE=1 \\
  bash tools/run_wr_record_resume.sh > "\${logdir}/\${label}.log" 2>&1
}

run_lane alpha20_1800_2250 0.20 2250
run_lane alpha00_1800_2250 0.00 2250
run_lane alpha35_1800_2125 0.35 2125

python - <<'PY' > "\${logdir}/val_summary.tsv"
import glob
import os
import re
print("label\\tstep\\ttotal\\tval_loss\\tstep_avg_ms")
for path in sorted(glob.glob("/root/prime_track3_wrslowmerge1800_logs/*.log")):
    label = os.path.basename(path).replace(".log", "")
    if not label.startswith("alpha"):
        continue
    for line in open(path, errors="replace"):
        m = re.search(r"step:(\\d+)/(\\d+) val_loss:([0-9.]+).*step_avg:([0-9.]+)ms", line)
        if m:
            print(f"{label}\\t{m.group(1)}\\t{m.group(2)}\\t{float(m.group(3)):.5f}\\t{float(m.group(4)):.2f}")
PY

python - <<'PY' > "\${logdir}/state_counts.txt"
import glob
import json
import math
import os
import re
import torch

paths = glob.glob("/root/.cache/track3_checkpoints/wrslow_*_step*.pt")
def sort_key(path):
    m = re.search(r"step(\\d+)", os.path.basename(path))
    return (os.path.basename(path), int(m.group(1)) if m else -1)
for path in sorted(paths, key=sort_key):
    ckpt = torch.load(path, map_location="cpu")
    entry = {"path": path, "step": ckpt.get("step"), "val_loss": ckpt.get("val_loss"), "optimizers": []}
    for opt_idx, opt in enumerate(ckpt.get("optimizers", [])):
        count = 0
        norm2 = 0.0
        keys = {}
        for state in opt.get("state", {}).values():
            for k, v in state.items():
                keys[k] = keys.get(k, 0) + 1
                if torch.is_tensor(v) and v.is_floating_point():
                    count += 1
                    n = float(v.float().norm().item())
                    norm2 += n * n
        entry["optimizers"].append({
            "index": opt_idx,
            "float_tensor_count": count,
            "float_tensor_norm": math.sqrt(norm2),
            "state_keys": dict(sorted(keys.items())),
        })
    print(json.dumps(entry, sort_keys=True))
PY

echo "done=\$(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee "\${logdir}/DONE"
rm -f "\${logdir}/RUNNING"
REMOTE_SCRIPT

ssh_remote "${ssh_target}" "chmod +x '${remote_logdir}/run_wrslowmerge1800.sh' && nohup '${remote_logdir}/run_wrslowmerge1800.sh' > '${remote_logdir}/run.nohup.log' 2>&1 & echo \$! > '${remote_logdir}/run.pid'"
run_started=1

cat <<EOF
started_pod=${pod_id}
name=${pod_name}
gpu=${availability_desc}
ssh_target=${ssh_target}
remote_logdir=${remote_logdir}
status_dir=${status_dir}
checkpoint_source=${local_ckpt}
lanes=alpha20_1800_2250,alpha00_1800_2250,alpha35_1800_2125
EOF
