import json
import os
import re
import shlex
import subprocess
import time
from pathlib import Path

import modal


APP_NAME = "nanogpt-speedrun-newton-muon"
REMOTE_ROOT = Path("/root/speedrun")
CACHE_MOUNT = Path("/root/.cache")
DATA_MOUNT = REMOTE_ROOT / "data" / "fineweb10B"
DEFAULT_GPU = os.environ.get(
    "NANOGPT_MODAL_GPU",
    os.environ.get("MODAL_NANOGPT_GPU", os.environ.get("MODAL_GPU", "H100")),
)
RUN_TIMEOUT = int(os.environ.get("NANOGPT_MODAL_RUN_TIMEOUT", "30000"))
MAX_CONTAINERS = int(os.environ.get("NANOGPT_MODAL_MAX_CONTAINERS", "2"))

if DEFAULT_GPU not in {"H100", "H100!", "GH200", "H100:8", "H100!:8"}:
    raise ValueError("Only H100/H100!/GH200 or 8x H100 specs are allowed for this speedrun runner.")


def _ignore_source(path: Path) -> bool:
    parts = set(path.parts)
    name = path.name
    return (
        ".git" in parts
        or ".opencode" in parts
        or "__pycache__" in parts
        or "tmp" in parts
        or "logs" in parts
        or "fineweb10B" in parts
        or name in {".DS_Store"}
        or name.endswith((".pyc", ".bin"))
    )


cache_volume = modal.Volume.from_name("nanogpt-speedrun-cache", create_if_missing=True)
data_volume = modal.Volume.from_name("nanogpt-speedrun-fineweb10b", create_if_missing=True)

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.10")
    .apt_install("git", "build-essential", "python3.10-dev")
    .pip_install_from_requirements("requirements.txt")
    .pip_install("kernels==0.11.7")
)
if os.environ.get("NANOGPT_MODAL_TORCH"):
    image = image.pip_install(f"torch=={os.environ['NANOGPT_MODAL_TORCH']}")
image = image.add_local_dir(".", str(REMOTE_ROOT), copy=True, ignore=_ignore_source).workdir(str(REMOTE_ROOT))

app = modal.App(
    APP_NAME,
    image=image,
    tags={"project": "nanogpt-speedrun", "optimizer": "newton-muon"},
)


def _run_streamed(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str, float]:
    started = time.time()
    proc = subprocess.Popen(
        cmd,
        cwd=REMOTE_ROOT,
        env={**os.environ, **(env or {})},
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    assert proc.stdout is not None
    chunks = []
    for line in proc.stdout:
        print(line, end="", flush=True)
        chunks.append(line)
    return proc.wait(), "".join(chunks), time.time() - started


def _parse_training_summary(output: str) -> dict[str, object]:
    matches = re.findall(
        r"step:(\d+)/(\d+) val_loss:([0-9.]+) train_time:([0-9]+)ms step_avg:([0-9.]+)ms",
        output,
    )
    if matches:
        step, total_steps, val_loss, train_ms, step_avg_ms = matches[-1]
        train_time_s = round(int(train_ms) / 1000.0, 3)
    else:
        matches = re.findall(
            r"step:(\d+)/(\d+) val_loss:([0-9.]+) train_time:([0-9.]+)s step_avg:([0-9.]+)ms",
            output,
        )
        if not matches:
            return {}
        step, total_steps, val_loss, train_s, step_avg_ms = matches[-1]
        train_time_s = round(float(train_s), 3)
    return {
        "step": int(step),
        "total_steps": int(total_steps),
        "val_loss": float(val_loss),
        "train_time_s": train_time_s,
        "step_avg_ms": float(step_avg_ms),
    }


def _loads_extra_env(extra_env_json: str) -> dict[str, str]:
    try:
        parsed = json.loads(extra_env_json)
    except json.JSONDecodeError:
        parsed, _ = json.JSONDecoder().raw_decode(extra_env_json)
    if not isinstance(parsed, dict):
        raise ValueError("extra_env_json must decode to an object")
    return {str(k): str(v) for k, v in parsed.items()}


@app.function(
    cpu=4,
    memory=8192,
    timeout=3600,
    volumes={str(CACHE_MOUNT): cache_volume, str(DATA_MOUNT): data_volume},
)
def prepare_data(data_chunks: int = 2) -> dict[str, object]:
    return _ensure_data(data_chunks)


def _ensure_data(data_chunks: int = 2) -> dict[str, object]:
    rc, output, elapsed = _run_streamed(["python3", "data/cached_fineweb10B.py", str(data_chunks)])
    cache_volume.commit()
    data_volume.commit()
    files = sorted(p.name for p in DATA_MOUNT.glob("*.bin"))
    return {
        "returncode": rc,
        "elapsed_s": round(elapsed, 3),
        "data_chunks_requested": data_chunks,
        "data_files": files,
        "tail": output[-2000:],
    }


@app.function(
    gpu=DEFAULT_GPU,
    cpu=16,
    memory=131072,
    ephemeral_disk=524288,
    timeout=RUN_TIMEOUT,
    startup_timeout=1800,
    scaledown_window=60,
    max_containers=MAX_CONTAINERS,
    volumes={str(CACHE_MOUNT): cache_volume, str(DATA_MOUNT): data_volume},
)
def run_screen(
    runner: str = "tools/run_newtonv_raw_v01_gate.sh",
    steps: int = 200,
    val_every: int = 50,
    nproc: int = 1,
    data_chunks: int = 2,
    log_path: str | None = None,
    extra_env: dict[str, str] | None = None,
) -> dict[str, object]:
    prep = _ensure_data(data_chunks)
    if prep["returncode"] != 0:
        return {"prepare": prep, "run": {"returncode": prep["returncode"]}}

    run_env = {
        "CUDA_HOME": "/usr/local/cuda",
        "PATH": f"/usr/local/cuda/bin:{os.environ.get('PATH', '')}",
        "LD_LIBRARY_PATH": f"/usr/local/cuda/lib64:{os.environ.get('LD_LIBRARY_PATH', '')}",
        "HF_HOME": str(CACHE_MOUNT / "huggingface"),
        "XDG_CACHE_HOME": str(CACHE_MOUNT / "xdg"),
        "TRITON_CACHE_DIR": str(CACHE_MOUNT / "triton"),
        "TORCHINDUCTOR_CACHE_DIR": str(CACHE_MOUNT / "torchinductor-speedrun-newtonv"),
        "PYTHONUNBUFFERED": "1",
        "SCREEN_STEPS": str(steps),
        "SCREEN_VAL_EVERY": str(val_every),
        "NPROC_PER_NODE": str(nproc),
    }
    if log_path:
        run_env["LOG_PATH"] = log_path
    if extra_env:
        run_env.update(extra_env)

    rc, output, elapsed = _run_streamed(["bash", runner], env=run_env)
    cache_volume.commit()
    summary = _parse_training_summary(output)
    return {
        "gpu": DEFAULT_GPU,
        "runner": runner,
        "returncode": rc,
        "wall_time_s": round(elapsed, 3),
        "training_summary": summary,
        "tail": output[-4000:],
        "cache_volume": "nanogpt-speedrun-cache",
        "data_volume": "nanogpt-speedrun-fineweb10b",
    }


@app.local_entrypoint()
def prepare(data_chunks: int = 2) -> None:
    print(json.dumps(prepare_data.remote(data_chunks), indent=2, sort_keys=True))


@app.local_entrypoint()
def run(
    runner: str = "tools/run_newtonv_raw_v01_gate.sh",
    steps: int = 200,
    val_every: int = 50,
    nproc: int = 1,
    data_chunks: int = 2,
    log_path: str | None = None,
    extra_env_json: str = "{}",
) -> None:
    extra_env = _loads_extra_env(extra_env_json)
    result = run_screen.remote(runner, steps, val_every, nproc, data_chunks, log_path, extra_env)
    print(json.dumps(result, indent=2, sort_keys=True))


@app.local_entrypoint()
def run_spawn(
    runner: str = "tools/run_newtonv_raw_v01_gate.sh",
    steps: int = 200,
    val_every: int = 50,
    nproc: int = 1,
    data_chunks: int = 2,
    log_path: str | None = None,
    extra_env_json: str = "{}",
) -> None:
    extra_env = _loads_extra_env(extra_env_json)
    call = run_screen.spawn(runner, steps, val_every, nproc, data_chunks, log_path, extra_env)
    print(
        json.dumps(
            {
                "gpu": DEFAULT_GPU,
                "runner": runner,
                "steps": steps,
                "val_every": val_every,
                "nproc": nproc,
                "data_chunks": data_chunks,
                "function_call_id": call.object_id,
                "dashboard_url": call.get_dashboard_url(),
                "mode": "spawn",
            },
            indent=2,
            sort_keys=True,
        )
    )
