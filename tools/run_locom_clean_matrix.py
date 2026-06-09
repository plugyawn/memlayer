#!/usr/bin/env python3
"""Run clean LocoProp-M matrix rows without Modal.

This is intended for Prime/local GPU pods where the checkout, environment, and
FineWeb cache already exist. It mirrors the Modal row presets but avoids any
provider-specific side effects.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


TRAIN_SCRIPT = (
    "records/track_3_optimization/results/20260608_locom_clean/"
    "train_gpt_simple_locom_clean.py"
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


def _to_float(value: str) -> float | None:
    try:
        return float(value)
    except ValueError:
        return None


def _run_streamed(cmd: list[str], env: dict[str, str] | None = None) -> tuple[int, str, float]:
    started = time.time()
    proc = subprocess.Popen(
        cmd,
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
                "train_time_ms": int(match.group(4)),
                "step_avg_ms": float(match.group(5)),
            }
        )
    return rows


def _parse_locom_layer_chunk(chunk: str) -> dict[str, object] | None:
    name, sep, rest = chunk.partition(":")
    if not sep:
        return None
    match = re.fullmatch(r"([A-Za-z_]+)l(\d+)", name)
    if not match:
        return None
    layer: dict[str, object] = {
        "surface": match.group(1),
        "layer": int(match.group(2)),
    }
    for key, value in re.findall(r"([A-Za-z_][A-Za-z0-9_]*)=([^,|]+)", rest):
        value = value.strip()
        if key in {"accepted", "skipped"}:
            layer[key] = int(value)
        elif key == "mom":
            mode, _, beta = value.partition(":")
            layer["momentum_mode"] = mode
            parsed_beta = _to_float(beta)
            if parsed_beta is not None:
                layer["momentum_beta"] = parsed_beta
        else:
            parsed = _to_float(value)
            layer[key] = parsed if parsed is not None else value
    return layer


def _summarize_prepare_layers(layers: list[dict[str, object]]) -> dict[str, object]:
    cosines = [x["cos_desc"] for x in layers if isinstance(x.get("cos_desc"), float)]
    loss_pairs = [
        (x["loss0"], x["lossK"])
        for x in layers
        if isinstance(x.get("loss0"), float) and isinstance(x.get("lossK"), float)
    ]
    corr_norms = [x["corr_norm"] for x in layers if isinstance(x.get("corr_norm"), float)]
    return {
        "layers": len(layers),
        "accepted": sum(int(x.get("accepted", 0)) for x in layers),
        "negative_cos": sum(1 for x in cosines if x < 0),
        "mean_cos_desc": round(sum(cosines) / len(cosines), 6) if cosines else None,
        "min_cos_desc": min(cosines) if cosines else None,
        "max_corr_norm": max(corr_norms) if corr_norms else None,
        "loss_decreased": sum(1 for loss0, loss_k in loss_pairs if loss_k <= loss0),
        "max_loss_ratio": max((loss_k / max(loss0, 1e-30) for loss0, loss_k in loss_pairs), default=None),
    }


def _summarize_apply_layers(layers: list[dict[str, object]]) -> dict[str, object]:
    scales = [x["scale"] for x in layers if isinstance(x.get("scale"), float)]
    ratios = [
        x["corr_norm"] / max(x["base_step"], 1e-30)
        for x in layers
        if isinstance(x.get("corr_norm"), float) and isinstance(x.get("base_step"), float)
    ]
    return {
        "layers": len(layers),
        "skipped": sum(int(x.get("skipped", 0)) for x in layers),
        "mean_scale": round(sum(scales) / len(scales), 12) if scales else None,
        "min_scale": min(scales) if scales else None,
        "max_scale": max(scales) if scales else None,
        "max_corr_to_base": max(ratios) if ratios else None,
    }


def _parse_locom_diagnostics(output: str) -> dict[str, object]:
    diagnostics: dict[str, list[dict[str, object]]] = {"prepare": [], "apply": []}
    for line in output.splitlines():
        for kind in ("prepare", "apply"):
            prefix = f"locoprop_m_{kind} step="
            if not line.startswith(prefix):
                continue
            step_text, _, rest = line[len(prefix) :].partition(" ")
            try:
                step = int(step_text)
            except ValueError:
                continue
            layers = [
                parsed
                for chunk in rest.split(" | ")
                if (parsed := _parse_locom_layer_chunk(chunk)) is not None
            ]
            summary = (
                _summarize_prepare_layers(layers)
                if kind == "prepare"
                else _summarize_apply_layers(layers)
            )
            diagnostics[kind].append({"step": step, "summary": summary, "layers": layers})
    return diagnostics


def _base_env(args: argparse.Namespace) -> dict[str, str]:
    return {
        "PYTHONUNBUFFERED": "1",
        "TRACK3_TRAIN_STEPS": str(args.train_steps),
        "TRACK3_COOLDOWN_FRAC": str(args.cooldown_frac),
        "TRACK3_LOCOM_LOG_STEPS": args.log_steps,
    }


def _load_rows(args: argparse.Namespace) -> list[dict[str, object]]:
    rows = list(ROW_PRESETS[args.preset])
    if args.rows_json:
        loaded = json.loads(args.rows_json)
        if not isinstance(loaded, list):
            raise SystemExit("--rows-json must be a JSON list")
        rows = loaded
    if args.max_rows is not None:
        rows = rows[: args.max_rows]
    return rows


def run_rows(args: argparse.Namespace) -> dict[str, object]:
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    label = args.run_label or f"locom-clean-{args.preset}-{int(time.time())}"
    jsonl_path = output_dir / f"{label}.jsonl"
    json_path = output_dir / f"{label}.json"
    rows = _load_rows(args)

    if args.prepare_data_chunks > 0:
        rc, data_output, elapsed = _run_streamed(
            ["python3", "data/cached_fineweb10B.py", str(args.prepare_data_chunks)]
        )
        if rc != 0:
            return {
                "prepare": {
                    "returncode": rc,
                    "elapsed_s": round(elapsed, 3),
                    "tail": data_output[-4000:],
                },
                "runs": [],
            }

    gpu_rc, gpu_output, _ = _run_streamed(["bash", "-lc", "nvidia-smi -L || true"])
    results = []
    for row in rows:
        row_id = str(row["id"])
        row_env = {str(k): str(v) for k, v in dict(row.get("env", {})).items()}
        env = _base_env(args)
        env.update(row_env)
        print(f"\n===== {row_id} env={json.dumps(row_env, sort_keys=True)} =====\n", flush=True)
        rc, output, elapsed = _run_streamed(
            [
                "torchrun",
                "--standalone",
                "--nproc_per_node=1",
                TRAIN_SCRIPT,
            ],
            env=env,
        )
        parsed_rows = _parse_training_rows(output)
        result = {
            "id": row_id,
            "env": row_env,
            "returncode": rc,
            "wall_time_s": round(elapsed, 3),
            "gates": parsed_rows,
            "final": parsed_rows[-1] if parsed_rows else {},
            "locoprop_diagnostics": _parse_locom_diagnostics(output),
            "tail": output[-4000:],
        }
        results.append(result)
        with jsonl_path.open("a") as f:
            print(json.dumps(result, sort_keys=True), file=f)
        if rc != 0 and not args.continue_on_error:
            break

    summary = {
        "run_label": label,
        "preset": args.preset,
        "gpu_probe": {"returncode": gpu_rc, "output": gpu_output.strip()},
        "result_jsonl": str(jsonl_path),
        "result_json": str(json_path),
        "runs": results,
    }
    json_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--preset", choices=sorted(ROW_PRESETS), default="c")
    parser.add_argument("--rows-json", default="", help="override preset with explicit row list")
    parser.add_argument("--run-label", default="")
    parser.add_argument("--output-dir", default=".opencode/locom_clean_results")
    parser.add_argument("--train-steps", type=int, default=500)
    parser.add_argument("--cooldown-frac", type=float, default=0.7)
    parser.add_argument("--log-steps", default="0,1,2,10,50,125,250,375,500")
    parser.add_argument("--prepare-data-chunks", type=int, default=0)
    parser.add_argument("--max-rows", type=int)
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    rows = _load_rows(args)
    if args.dry_run:
        print(json.dumps({"preset": args.preset, "rows": rows}, indent=2, sort_keys=True))
        return 0

    result = run_rows(args)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
