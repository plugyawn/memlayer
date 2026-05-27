import json
import os
import subprocess
import time

import modal


GPU_SPEC = os.environ.get("MODAL_GPU", "H100")
IMAGE = modal.Image.from_registry(
    os.environ.get("MODAL_CUDA_IMAGE", "nvidia/cuda:12.8.0-devel-ubuntu22.04"),
    add_python=os.environ.get("MODAL_PYTHON_VERSION", "3.11"),
)
APP = modal.App(
    "nanogpt-speedrun-h100-probe",
    image=IMAGE,
    tags={"project": "nanogpt-speedrun", "purpose": "h100-probe"},
)


def _run(cmd: list[str]) -> dict[str, object]:
    started = time.time()
    proc = subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    return {
        "cmd": cmd,
        "returncode": proc.returncode,
        "elapsed_s": round(time.time() - started, 3),
        "output": proc.stdout.strip(),
    }


@APP.function(
    gpu=GPU_SPEC,
    cpu=2,
    memory=4096,
    timeout=300,
    scaledown_window=5,
    max_containers=1,
)
def h100_probe() -> dict[str, object]:
    return {
        "gpu_spec": GPU_SPEC,
        "modal_cloud_provider": os.environ.get("MODAL_CLOUD_PROVIDER"),
        "modal_region": os.environ.get("MODAL_REGION"),
        "modal_task_id_present": bool(os.environ.get("MODAL_TASK_ID")),
        "nvidia_smi": _run(
            [
                "nvidia-smi",
                "--query-gpu=name,memory.total,driver_version,pci.bus_id",
                "--format=csv,noheader",
            ]
        ),
        "nvcc": _run(["bash", "-lc", "command -v nvcc && nvcc --version | tail -n 1"]),
    }


@APP.local_entrypoint()
def main() -> None:
    print(json.dumps(h100_probe.remote(), indent=2, sort_keys=True))

