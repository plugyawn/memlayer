import json
import os
import re
import subprocess
import time
from pathlib import Path

import modal


APP_NAME = "track3-locom-clean-cmatrix-20260609"
REMOTE_ROOT = Path("/root/modded-nanogpt-locom-clean")
CACHE_MOUNT = Path("/root/.cache")
DATA_MOUNT = REMOTE_ROOT / "data" / "fineweb10B"
RESULTS_MOUNT = Path("/root/track3_locom_clean_results")
TRAIN_SCRIPT = (
    "records/track_3_optimization/results/20260608_locom_clean/"
    "train_gpt_simple_locom_clean.py"
)
DEFAULT_GPU = os.environ.get("TRACK3_LOCOM_MODAL_GPU", os.environ.get("MODAL_GPU", "H100"))
RUN_TIMEOUT = int(os.environ.get("TRACK3_LOCOM_MODAL_TIMEOUT", "7200"))


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
        or name == ".DS_Store"
        or name.endswith((".pyc", ".bin"))
    )


cache_volume = modal.Volume.from_name("nanogpt-speedrun-cache", create_if_missing=True)
data_volume = modal.Volume.from_name("nanogpt-speedrun-fineweb10b", create_if_missing=True)
results_volume = modal.Volume.from_name("track3-locom-clean-results", create_if_missing=True)

image = (
    modal.Image.from_registry("nvidia/cuda:12.8.0-devel-ubuntu22.04", add_python="3.10")
    .apt_install("git", "build-essential", "python3.10-dev")
    .pip_install_from_requirements("requirements.txt")
    .pip_install("kernels==0.11.7")
    .add_local_dir(".", str(REMOTE_ROOT), copy=True, ignore=_ignore_source)
    .workdir(str(REMOTE_ROOT))
)

app = modal.App(
    APP_NAME,
    image=image,
    tags={"project": "nanogpt-speedrun", "optimizer": "locoprop-clean"},
)


C_ROWS = [
    {
        "id": "L500-C0",
        "env": {
            "TRACK3_LOCOM_SURFACES": "fc",
            "TRACK3_LOCOM_TARGET_GAMMA": "0.5",
            "TRACK3_LOCOM_NORM_CAP": "0.20",
        },
    },
    {
        "id": "L500-C1",
        "env": {
            "TRACK3_LOCOM_SURFACES": "fc",
            "TRACK3_LOCOM_TRUE_RELU2_GRAD": "1",
        },
    },
    {
        "id": "L500-C2",
        "env": {
            "TRACK3_LOCOM_SURFACES": "fc",
            "TRACK3_LOCOM_TRUE_RELU2_GRAD": "1",
            "TRACK3_LOCOM_TARGET_GAMMA": "0.5",
        },
    },
]

D_ROWS = [
    {
        "id": "L500-D0",
        "env": {
            "TRACK3_LOCOM_SURFACES": "v",
            "TRACK3_LOCOM_TARGET_GAMMA": "0.5",
            "TRACK3_LOCOM_NORM_CAP": "0.20",
        },
    },
    {
        "id": "L500-D1",
        "env": {
            "TRACK3_LOCOM_SURFACES": "o",
            "TRACK3_LOCOM_TARGET_GAMMA": "0.5",
            "TRACK3_LOCOM_NORM_CAP": "0.20",
        },
    },
    {
        "id": "L500-D2",
        "env": {
            "TRACK3_LOCOM_SURFACES": "v,o",
            "TRACK3_LOCOM_TARGET_GAMMA": "0.5",
            "TRACK3_LOCOM_NORM_CAP": "0.10",
        },
    },
]

E_ROWS = [
    {
        "id": "L500-E0",
        "env": {
            "TRACK3_LOCOM_SURFACES": "q",
            "TRACK3_LOCOM_TARGET_GAMMA": "0.25",
            "TRACK3_LOCOM_NORM_CAP": "0.10",
        },
    },
    {
        "id": "L500-E1",
        "env": {
            "TRACK3_LOCOM_SURFACES": "k",
            "TRACK3_LOCOM_TARGET_GAMMA": "0.25",
            "TRACK3_LOCOM_NORM_CAP": "0.10",
        },
    },
    {
        "id": "L500-E2",
        "env": {
            "TRACK3_LOCOM_SURFACES": "q,k",
            "TRACK3_LOCOM_TARGET_GAMMA": "0.25",
            "TRACK3_LOCOM_NORM_CAP": "0.05",
        },
    },
]

ROW_PRESETS = {
    "c": C_ROWS,
    "d": D_ROWS,
    "e": E_ROWS,
    "cd": C_ROWS + D_ROWS,
    "cde": C_ROWS + D_ROWS + E_ROWS,
}


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


def _parse_training_rows(output: str) -> list[dict[str, object]]:
    rows = []
    for match in re.finditer(
        r"step:(\d+)/(\d+) val_loss:([0-9.]+) train_time:([0-9]+)ms step_avg:([0-9.]+)ms",
        output,
    ):
        rows.append(
            {
                "step": int(match.group(1)),
                "total_steps": int(match.group(2)),
                "val_loss": float(match.group(3)),
                "train_time_s": round(int(match.group(4)) / 1000.0, 3),
                "step_avg_ms": float(match.group(5)),
            }
        )
    if rows:
        return rows
    for match in re.finditer(
        r"step:(\d+)/(\d+) val_loss:([0-9.]+) train_time:([0-9.]+)s step_avg:([0-9.]+)ms",
        output,
    ):
        rows.append(
            {
                "step": int(match.group(1)),
                "total_steps": int(match.group(2)),
                "val_loss": float(match.group(3)),
                "train_time_s": round(float(match.group(4)), 3),
                "step_avg_ms": float(match.group(5)),
            }
        )
    return rows


def _base_env() -> dict[str, str]:
    return {
        "CUDA_HOME": "/usr/local/cuda",
        "PATH": f"/usr/local/cuda/bin:{os.environ.get('PATH', '')}",
        "LD_LIBRARY_PATH": f"/usr/local/cuda/lib64:{os.environ.get('LD_LIBRARY_PATH', '')}",
        "HF_HOME": str(CACHE_MOUNT / "huggingface"),
        "XDG_CACHE_HOME": str(CACHE_MOUNT / "xdg"),
        "TRITON_CACHE_DIR": str(CACHE_MOUNT / "triton-locom-clean"),
        "TORCHINDUCTOR_CACHE_DIR": str(CACHE_MOUNT / "torchinductor-locom-clean"),
        "PYTHONUNBUFFERED": "1",
        "TRACK3_TRAIN_STEPS": "500",
        "TRACK3_COOLDOWN_FRAC": "0.7",
        "TRACK3_LOCOM_LOG_STEPS": "0,1,2,10,50,125,250,375,500",
    }


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
    volumes={
        str(CACHE_MOUNT): cache_volume,
        str(DATA_MOUNT): data_volume,
        str(RESULTS_MOUNT): results_volume,
    },
)
def run_queue(rows: list[dict[str, object]], data_chunks: int = 2, run_label: str = "") -> dict[str, object]:
    RESULTS_MOUNT.mkdir(parents=True, exist_ok=True)
    label = run_label or f"queue-{int(time.time())}"
    result_jsonl = RESULTS_MOUNT / f"{label}.jsonl"
    result_json = RESULTS_MOUNT / f"{label}.json"
    prep = _ensure_data(data_chunks)
    if prep["returncode"] != 0:
        return {"gpu": DEFAULT_GPU, "prepare": prep, "runs": []}

    gpu_rc, gpu_output, _ = _run_streamed(["bash", "-lc", "nvidia-smi -L || true"])
    results = []
    for row in rows:
        row_id = str(row["id"])
        row_env = {str(k): str(v) for k, v in dict(row.get("env", {})).items()}
        run_env = _base_env()
        run_env.update(row_env)
        print(f"\\n===== {row_id} env={json.dumps(row_env, sort_keys=True)} =====\\n", flush=True)
        rc, output, elapsed = _run_streamed(
            [
                "torchrun",
                "--standalone",
                "--nproc_per_node=1",
                TRAIN_SCRIPT,
            ],
            env=run_env,
        )
        parsed_rows = _parse_training_rows(output)
        results.append(
            {
                "id": row_id,
                "env": row_env,
                "returncode": rc,
                "wall_time_s": round(elapsed, 3),
                "gates": parsed_rows,
                "final": parsed_rows[-1] if parsed_rows else {},
                "tail": output[-4000:],
            }
        )
        with result_jsonl.open("a") as f:
            print(json.dumps(results[-1], sort_keys=True), file=f)
        results_volume.commit()
        cache_volume.commit()
        if rc != 0:
            break
    result = {
        "gpu": DEFAULT_GPU,
        "gpu_probe": {"returncode": gpu_rc, "output": gpu_output.strip()},
        "prepare": prep,
        "runs": results,
        "cache_volume": "nanogpt-speedrun-cache",
        "data_volume": "nanogpt-speedrun-fineweb10b",
        "results_volume": "track3-locom-clean-results",
        "result_jsonl": str(result_jsonl),
        "result_json": str(result_json),
    }
    result_json.write_text(json.dumps(result, indent=2, sort_keys=True))
    results_volume.commit()
    return result


def _loads_rows(rows_json: str, preset: str) -> list[dict[str, object]]:
    if not rows_json.strip():
        if preset not in ROW_PRESETS:
            raise ValueError(f"unknown preset {preset!r}; expected one of {sorted(ROW_PRESETS)}")
        return ROW_PRESETS[preset]
    rows = json.loads(rows_json)
    if not isinstance(rows, list):
        raise ValueError("rows_json must decode to a list")
    return rows


@app.local_entrypoint()
def queue(rows_json: str = "", preset: str = "c", data_chunks: int = 2, run_label: str = "") -> None:
    rows = _loads_rows(rows_json, preset)
    result = run_queue.remote(rows, data_chunks, run_label)
    print(json.dumps(result, indent=2, sort_keys=True))


@app.local_entrypoint()
def queue_spawn(rows_json: str = "", preset: str = "c", data_chunks: int = 2, run_label: str = "") -> None:
    rows = _loads_rows(rows_json, preset)
    call = run_queue.spawn(rows, data_chunks, run_label)
    print(
        json.dumps(
            {
                "app": APP_NAME,
                "gpu": DEFAULT_GPU,
                "rows": [row["id"] for row in rows],
                "run_label": run_label,
                "results_volume": "track3-locom-clean-results",
                "function_call_id": call.object_id,
                "dashboard_url": call.get_dashboard_url(),
            },
            indent=2,
            sort_keys=True,
        )
    )
