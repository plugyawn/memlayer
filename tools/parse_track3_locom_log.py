#!/usr/bin/env python3
"""Parse Track 3 LocoProp-M screen logs into a compact summary."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from statistics import mean


VAL_RE = re.compile(
    r"step:(?P<step>\d+)/(?P<total>\d+)\s+val_loss:(?P<loss>[0-9.eE+-]+)\s+"
    r"train_time:(?P<time>[0-9.]+)(?P<unit>ms|s)\s+step_avg:(?P<avg>[0-9.]+)ms"
)
PROGRESS_RE = re.compile(
    r"step:(?P<step>\d+)/(?P<total>\d+)\s+train_time:(?P<time>[0-9.]+)(?P<unit>ms|s)\s+"
    r"step_avg:(?P<avg>[0-9.]+)ms"
)
KEYVAL_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)=([^ \n]+)")
PREP_RE = re.compile(r"locoprop_m_prepare step=(?P<step>\d+)\s+(?P<body>.*)")
APPLY_RE = re.compile(r"locoprop_m_apply step=(?P<step>\d+)\s+(?P<body>.*)")


def _time_seconds(value: str, unit: str) -> float:
    parsed = float(value)
    return parsed / 1000.0 if unit == "ms" else parsed


def parse_one(path: Path) -> dict[str, object]:
    text = path.read_text(errors="replace")
    vals = []
    progresses = []
    prepare_steps: list[int] = []
    apply_steps: list[int] = []
    config: dict[str, str] = {}
    runner: dict[str, str] = {}
    source_sha: dict[str, str] = {}
    saw_batched_diag = False

    for line in text.splitlines():
        if "track3_locom_runner " in line:
            runner.update(dict(KEYVAL_RE.findall(line)))
        if "track3_locom_source_sha " in line:
            source_sha.update(dict(KEYVAL_RE.findall(line)))
        if (
            "LocoM enabled=" in line
            or "track3_locom_fused_screen " in line
            or line.startswith("locom ")
        ):
            config.update(dict(KEYVAL_RE.findall(line)))
        match = VAL_RE.search(line)
        if match:
            vals.append(
                {
                    "step": int(match["step"]),
                    "total_steps": int(match["total"]),
                    "val_loss": float(match["loss"]),
                    "train_time_s": _time_seconds(match["time"], match["unit"]),
                    "step_avg_ms": float(match["avg"]),
                }
            )
            continue
        match = PROGRESS_RE.search(line)
        if match:
            progresses.append(
                {
                    "step": int(match["step"]),
                    "total_steps": int(match["total"]),
                    "train_time_s": _time_seconds(match["time"], match["unit"]),
                    "step_avg_ms": float(match["avg"]),
                }
            )
            continue
        match = PREP_RE.search(line)
        if match:
            prepare_steps.append(int(match["step"]))
            saw_batched_diag = saw_batched_diag or "batched=1" in match["body"]
            continue
        match = APPLY_RE.search(line)
        if match:
            apply_steps.append(int(match["step"]))

    nonval_progress = [
        p["step_avg_ms"]
        for p in progresses
        if not any(v["step"] == p["step"] for v in vals)
    ]
    recent_nonval = nonval_progress[-20:]
    summary = {
        "path": str(path),
        "runner": runner,
        "source_sha": source_sha,
        "config": config,
        "final_val": vals[-1] if vals else None,
        "num_val_points": len(vals),
        "val_points": vals,
        "last_progress": progresses[-1] if progresses else None,
        "recent_nonval_step_avg_ms": None if not recent_nonval else mean(recent_nonval),
        "locoprop_prepare_steps": prepare_steps,
        "locoprop_apply_steps": apply_steps,
        "locoprop_prepare_count": len(prepare_steps),
        "locoprop_apply_count": len(apply_steps),
        "saw_aux_capture": config.get("aux_capture") == "True" or config.get("aux_capture") == "1",
        "saw_batched_prep_config": config.get("batched_prep") == "True" or config.get("batched_prep") == "1",
        "saw_batched_prep_diag": saw_batched_diag,
    }
    return summary


def print_markdown(items: list[dict[str, object]]) -> None:
    for item in items:
        final_val = item["final_val"]
        print(f"## {item['path']}")
        if final_val:
            print(
                f"- final_val: {final_val['val_loss']:.5f} @ {final_val['step']}/{final_val['total_steps']} "
                f"({final_val['step_avg_ms']:.2f} ms/step including eval)"
            )
        else:
            print("- final_val: not found")
        if item["last_progress"]:
            progress = item["last_progress"]
            print(f"- last_progress: step {progress['step']} avg {progress['step_avg_ms']:.2f} ms")
        if item["recent_nonval_step_avg_ms"] is not None:
            print(f"- recent_nonval_step_avg_ms: {item['recent_nonval_step_avg_ms']:.2f}")
        print(
            f"- flags: aux_capture={item['saw_aux_capture']} "
            f"batched_config={item['saw_batched_prep_config']} "
            f"batched_diag={item['saw_batched_prep_diag']}"
        )
        print(
            f"- locoprop: prepare_count={item['locoprop_prepare_count']} "
            f"apply_count={item['locoprop_apply_count']}"
        )
        print()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--json", action="store_true", help="emit JSON instead of Markdown")
    args = parser.parse_args()

    parsed = [parse_one(path) for path in args.logs]
    if args.json:
        print(json.dumps(parsed, indent=2, sort_keys=True))
    else:
        print_markdown(parsed)


if __name__ == "__main__":
    main()
