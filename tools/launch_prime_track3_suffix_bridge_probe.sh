#!/usr/bin/env bash
set -euo pipefail

# Launch one Prime H100 suffix-bridge screen from an existing post-prefix
# checkpoint. This intentionally does not recreate the 1600->2000 prefix.

workspace="${WORKSPACE:-$(pwd)}"
env_file="${PRIME_ENV_FILE:-/Users/progyan/speedrun/env.local}"
ledger="${PRIME_LEDGER:-${workspace}/.opencode/prime-gpu-ledger.md}"
pod_name="${PRIME_POD_NAME:-oc-main-track3-suffixbridge-h100-$(date -u +%Y%m%d-%H%M)}"
remote_repo="${REMOTE_REPO:-/root/wr-track3-locom-20260606}"
remote_logdir="${REMOTE_LOGDIR:-/root/prime_track3_suffix_bridge_logs}"
remote_ckpt_dir="${REMOTE_CKPT_DIR:-/root/.cache/track3_checkpoints}"
known_hosts="${PRIME_KNOWN_HOSTS:-${workspace}/.opencode/prime_known_hosts_suffixbridge}"
disk_size_gb="${PRIME_DISK_SIZE_GB:-500}"
min_balance="${PRIME_MIN_BALANCE_USD:-4.00}"
gpu_type="${PRIME_GPU_TYPE:-H100_80GB}"
gpu_socket_filter="${PRIME_GPU_SOCKET:-SXM}"
local_ckpt="${LOCAL_CKPT:-/Users/progyan/speedrun/tmp/prime_ckpt_transfer/track3_noloco_ckpt2125_seed3710_seed3710_step2125.pt}"
remote_ckpt="${remote_ckpt_dir}/track3_noloco_ckpt2125_seed3710_seed3710_step2125.pt"
suffix_lanes="${TRACK3_SUFFIX_LANES:-bump150_2250_2650,blend_p15_2250_2650}"
train_steps="${TRACK3_TRAIN_STEPS:-2400}"
gate_step="${TRACK3_GATE_STEP:-2400}"
gate_loss="${TRACK3_GATE_LOSS:-3.3365}"

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
    raise SystemExit(f"personal wallet balance ${balance:.4f} is below minimum ${minimum:.2f}; not launching")
PY

pods_json="$(prime --plain pods list --output json)"
active_count="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["total_count"])' <<<"${pods_json}")"
if [[ "${active_count}" != "0" ]]; then
  echo "Prime personal context already has ${active_count} active pod(s); inspect before launching." >&2
  exit 3
fi

availability_json="$(prime --plain availability list --gpu-type "${gpu_type}" --gpu-count 1 --output json)"
availability_id="$(
  python3 -c '
import json, sys
socket_filter = sys.argv[1].upper()
rows = json.load(sys.stdin).get("gpu_resources", [])
rows = [
    r for r in rows
    if r.get("stock_status") == "Available"
    and (not socket_filter or str(r.get("socket", "")).upper().startswith(socket_filter))
]
if not rows:
    raise SystemExit("no available GPU rows matching socket filter")
rows.sort(key=lambda r: (float(r.get("price_value", 1e9)), not bool(r.get("is_spot"))))
print(rows[0]["id"])
' "${gpu_socket_filter}" <<<"${availability_json}"
)"
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

pod_id=""
run_started=0
cleanup_pod_on_error() {
  local ec=$?
  trap - ERR
  if [[ "${run_started}" != "1" && -n "${pod_id}" ]]; then
    echo "setup failed; terminating owned pod ${pod_id}" >&2
    prime --plain pods terminate "${pod_id}" >/dev/null 2>&1 || true
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
cat >>"${ledger}" <<EOF

- pod_id: ${pod_id}
  name: ${pod_name}
  owner: current-agent
  purpose: Track 3 suffix-only bridge screen from step2125 checkpoint; lanes=${suffix_lanes}
  gpu: ${availability_desc}
  price_per_hour: selected by availability id ${availability_id}
  created_at: ${created_at}
  expected_stop: after 2400 gate artifacts are pulled, setup failure, or spot interruption
  status: launched_by_${0##*/}_head_${head_sha}
  termination_policy: terminate after gated suffix screen unless a lane clears the gate and user approves continuation
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
  prime --plain pods terminate "${pod_id}" >/dev/null 2>&1 || true
  exit 4
fi

echo "syncing git HEAD ${head_sha} to ${ssh_target}:${remote_repo}"
git archive --format=tar HEAD | ssh_remote "${ssh_target}" \
  "rm -rf '${remote_repo}' && mkdir -p '${remote_repo}' && tar -xf - -C '${remote_repo}'"

echo "copying checkpoint to ${ssh_target}:${remote_ckpt}"
ssh_remote "${ssh_target}" "mkdir -p '${remote_ckpt_dir}' '${remote_logdir}'"
scp_to_remote "${ssh_target}" "${local_ckpt}" "${remote_ckpt}"

echo "writing remote suffix-bridge run"
ssh_remote "${ssh_target}" "cat > '${remote_logdir}/run_suffix_bridge.sh'" <<REMOTE_SCRIPT
#!/usr/bin/env bash
set -euo pipefail

repo=${remote_repo}
logdir=${remote_logdir}
ckpt_dir=${remote_ckpt_dir}

export DEBIAN_FRONTEND=noninteractive
export PYTHONUNBUFFERED=1
export HF_HOME=/root/.cache/huggingface
export XDG_CACHE_HOME=/root/.cache/xdg
export TRITON_CACHE_DIR=/root/.cache/triton
export TORCHINDUCTOR_CACHE_DIR=/root/.cache/torchinductor-track3-suffixbridge

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
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader > "\${logdir}/gpu.txt" 2>&1 || true

TRACK3_SUFFIX_CHECKPOINT=${remote_ckpt} \\
TRACK3_SUFFIX_FROM_STEP=2125 \\
TRACK3_SUFFIX_LOG_DIR="\${logdir}" \\
TRACK3_CHECKPOINT_DIR="\${ckpt_dir}" \\
TRACK3_SUFFIX_LANES=${suffix_lanes} \\
TRACK3_TRAIN_STEPS=${train_steps} \\
TRACK3_GATE_STEP=${gate_step} \\
TRACK3_GATE_LOSS=${gate_loss} \\
TRACK3_ANALYZE_STEPS=2125,2250,2400 \\
bash tools/run_track3_suffix_bridge_probe.sh

touch "\${logdir}/DONE"
REMOTE_SCRIPT

ssh_remote "${ssh_target}" "chmod +x '${remote_logdir}/run_suffix_bridge.sh' && nohup '${remote_logdir}/run_suffix_bridge.sh' > '${remote_logdir}/run.nohup.log' 2>&1 & echo \$! > '${remote_logdir}/run.pid'"
run_started=1

cat <<EOF
started_pod=${pod_id}
name=${pod_name}
gpu=${availability_desc}
ssh_target=${ssh_target}
remote_logdir=${remote_logdir}
lanes=${suffix_lanes}
train_steps=${train_steps}
gate=${gate_step}:${gate_loss}
EOF
