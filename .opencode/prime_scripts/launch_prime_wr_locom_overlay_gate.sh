#!/usr/bin/env bash
set -euo pipefail

# Launch the committed WR-stack LocoProp-M overlay gate on one Prime H100.
# This script intentionally ships the current git HEAD via `git archive` so the
# remote run is exactly reproducible from the pushed branch, without depending on
# remote GitHub auth.

workspace="${WORKSPACE:-$(pwd)}"
env_file="${PRIME_ENV_FILE:-/Users/progyan/speedrun/env.local}"
ledger="${PRIME_LEDGER:-${workspace}/.opencode/prime-gpu-ledger.md}"
pod_name="${PRIME_POD_NAME:-oc-main-wr-locom-overlay-$(date -u +%Y%m%d-%H%M)}"
remote_repo="${REMOTE_REPO:-/root/wr-fresh-20260526}"
remote_script="${REMOTE_SCRIPT:-.opencode/prime_scripts/wr_record_locom_aux_k5_lr1e3_nogate2000_seed3710_gated.sh}"
min_balance="${PRIME_MIN_BALANCE_USD:-4.00}"
known_hosts="${PRIME_KNOWN_HOSTS:-${workspace}/.opencode/prime_known_hosts_wr_locom_overlay}"

if [[ ! -f "$env_file" ]]; then
  echo "missing env file: $env_file" >&2
  exit 2
fi

export PRIME_API_KEY="${PRIME_API_KEY:-$(python3 - "$env_file" <<'PY'
import sys
path = sys.argv[1]
values = {}
with open(path) as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        values[k.strip()] = v.strip().strip('"').strip("'")
print(values.get("PRIME_API_KEY") or values.get("PRIME_KEY") or "")
PY
)}"
if [[ -z "${PRIME_API_KEY}" ]]; then
  echo "PRIME_API_KEY/PRIME_KEY is not set" >&2
  exit 2
fi
export PRIME_DISABLE_VERSION_CHECK=1

cd "$workspace"
head_sha="$(git rev-parse --short HEAD)"
pod_id=""
run_started=0

cleanup_pod_on_error() {
  local ec=$?
  trap - ERR
  if [[ "$run_started" != "1" && -n "$pod_id" ]]; then
    echo "setup failed; terminating owned pod ${pod_id}" >&2
    prime --plain pods terminate "$pod_id" >/dev/null 2>&1 || true
  fi
  exit "$ec"
}
trap cleanup_pod_on_error ERR

wallet_json="$(prime --plain wallet --limit 1 --output json)"
balance="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["balance_usd"])' <<<"$wallet_json")"
python3 - "$balance" "$min_balance" <<'PY'
import sys
balance = float(sys.argv[1])
minimum = float(sys.argv[2])
if balance < minimum:
    raise SystemExit(f"wallet balance ${balance:.4f} is below minimum ${minimum:.2f}; not launching")
PY

pods_json="$(prime --plain pods list --output json)"
active_count="$(python3 -c 'import json,sys; print(json.load(sys.stdin)["total_count"])' <<<"$pods_json")"
if [[ "$active_count" != "0" ]]; then
  echo "Prime already has ${active_count} active pod(s); inspect before launching a new one." >&2
  exit 3
fi

availability_json="$(prime --plain availability list --gpu-type H100_80GB --gpu-count 1 --output json)"
availability_id="$(
  python3 -c '
import json, sys
rows = json.load(sys.stdin).get("gpu_resources", [])
rows = [
    r for r in rows
    if r.get("stock_status") == "Available"
    and str(r.get("socket", "")).upper().startswith("SXM")
]
if not rows:
    raise SystemExit("no available SXM H100 rows")
rows.sort(key=lambda r: (float(r.get("price_value", 1e9)), not bool(r.get("is_spot"))))
print(rows[0]["id"])
  ' <<<"$availability_json"
)"
availability_desc="$(
  python3 -c '
import json, sys
target = sys.argv[1]
rows = json.load(sys.stdin).get("gpu_resources", [])
for r in rows:
    if r.get("id") == target:
        print("{} {} {} {}".format(r.get("gpu_type"), r.get("socket"), r.get("provider"), r.get("price_per_hour")))
        break
  ' "$availability_id" <<<"$availability_json"
)"

echo "launching pod name=${pod_name} availability=${availability_id} ${availability_desc} head=${head_sha}"
create_out="$(prime --plain pods create --id "$availability_id" --name "$pod_name" --yes 2>&1 || true)"
echo "$create_out"

pod_id="$(
  prime --plain pods list --output json | python3 -c '
import json, sys
name = sys.argv[1]
pods = json.load(sys.stdin).get("pods", [])
matches = [p for p in pods if p.get("name") == name]
if not matches:
    raise SystemExit(f"pod named {name!r} not found after create")
print(matches[0]["id"])
  ' "$pod_name"
)"

created_at="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
cat >>"$ledger" <<EOF

- pod_id: ${pod_id}
  name: ${pod_name}
  owner: current-agent
  purpose: WR-stack LocoProp-M aux overlay gate through 2000 with automatic loss gates
  gpu: ${availability_desc}
  price_per_hour: selected by availability id ${availability_id}
  created_at: ${created_at}
  expected_stop: after gate failure, step 2000 completion, setup failure, or artifact pull
  status: launched_by_${0##*/}_head_${head_sha}
  termination_policy: terminate after workload/failure unless user asks to keep alive
EOF

ssh_target=""
for _ in $(seq 1 120); do
  status_json="$(prime --plain pods status "$pod_id" --output json 2>/dev/null || true)"
  ssh_target="$(
    python3 -c '
import json, sys
text = sys.stdin.read()
if not text.strip():
    raise SystemExit
data = json.loads(text)
ssh = data.get("ssh") or ""
ip = data.get("ip") or ""
if ssh:
    print(ssh)
elif ip:
    print(f"root@{ip}")
    ' <<<"$status_json"
  )" || true
  if [[ -n "$ssh_target" ]]; then
    if ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="$known_hosts" -o ConnectTimeout=8 "$ssh_target" true >/dev/null 2>&1; then
      break
    fi
  fi
  sleep 10
done

if [[ -z "$ssh_target" ]]; then
  echo "pod ${pod_id} did not become SSH-ready; terminating owned pod" >&2
  prime --plain pods terminate "$pod_id" >/dev/null 2>&1 || true
  exit 4
fi

echo "syncing git HEAD ${head_sha} to ${ssh_target}:${remote_repo}"
git archive --format=tar HEAD | ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="$known_hosts" "$ssh_target" \
  "rm -rf '$remote_repo' && mkdir -p '$remote_repo' && tar -xf - -C '$remote_repo'"

echo "starting remote gated run"
ssh -o StrictHostKeyChecking=accept-new -o UserKnownHostsFile="$known_hosts" "$ssh_target" \
  "mkdir -p /root/prime_track3_logs && cd '$remote_repo' && nohup bash '$remote_script' >/root/prime_track3_logs/wr_locom_overlay_gate.nohup.log 2>&1 & echo \\\$! > /root/prime_track3_logs/wr_locom_overlay_gate.launcher.pid"
run_started=1

cat <<EOF
launched:
  pod_id: ${pod_id}
  name: ${pod_name}
  ssh: ${ssh_target}
  remote_repo: ${remote_repo}
  remote_log: /root/prime_track3_logs/wr_record_locom_aux_k5_lr1e3_nogate_2000_seed3710_h100_mbs64.log
  remote_gate_status: /root/prime_track3_logs/wr_record_locom_aux_k5_lr1e3_nogate_2000_seed3710_h100_mbs64.gate.status

poll:
  ssh -o UserKnownHostsFile='${known_hosts}' '${ssh_target}' 'tail -n 80 /root/prime_track3_logs/wr_record_locom_aux_k5_lr1e3_nogate_2000_seed3710_h100_mbs64.gate.status /root/prime_track3_logs/wr_record_locom_aux_k5_lr1e3_nogate_2000_seed3710_h100_mbs64.log'
EOF
