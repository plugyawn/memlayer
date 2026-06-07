#!/usr/bin/env python3
"""Quantify whether the applied Track 3 LocoProp-M prefix correction moved loss.

The prefix-specificity probe can produce a visually strong trajectory even when
the actual LocoProp correction is not the cause. This analyzer compares an
active lane against a same-harness alpha-zero control and reports both validation
loss deltas and the effective correction size.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median


VAL_RE = re.compile(r"step:(?P<step>\d+)/\d+\s+val_loss:(?P<loss>[0-9.]+)")
KDIAG_RE = re.compile(r"locoprop_m_kdiag step=(?P<step>\d+) l(?P<layer>\d+) (?P<body>.*)")
K_ENTRY_RE = re.compile(
    r"k(?P<k>\d+):loss=(?P<loss>[0-9.eE+-]+),ratio=(?P<ratio>[0-9.eE+-]+),"
    r"corr_norm=(?P<corr>[0-9.eE+-]+),raw_cos=(?P<raw_cos>[+-]?[0-9.]+),cos=(?P<cos>[+-]?[0-9.]+)"
)
APPLY_STEP_RE = re.compile(r"locoprop_m_apply step=(?P<step>\d+) ")
APPLY_ENTRY_RE = re.compile(
    r"base_step=(?P<base>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r",corr_norm=(?P<corr>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r",cap=(?P<cap>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r",scale=(?P<scale>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)",
    re.IGNORECASE,
)


@dataclass
class LaneStats:
    path: Path
    vals: dict[int, float] = field(default_factory=dict)
    cos_by_step: dict[int, list[float]] = field(default_factory=dict)
    ratio_by_step: dict[int, list[float]] = field(default_factory=dict)
    eff_frac_by_step: dict[int, list[float]] = field(default_factory=dict)


def _finite_float(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def _fmt(value: float | None, digits: int = 5) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _fmt_sci(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.3e}"


def _median(values: list[float]) -> float | None:
    return float(median(values)) if values else None


def parse_log(path: Path, *, k: int) -> LaneStats:
    stats = LaneStats(path=path)
    for line in path.read_text(errors="replace").splitlines():
        if match := VAL_RE.search(line):
            stats.vals[int(match["step"])] = float(match["loss"])
            continue
        if match := KDIAG_RE.search(line):
            step = int(match["step"])
            for entry in K_ENTRY_RE.finditer(match["body"]):
                if int(entry["k"]) != k:
                    continue
                ratio = _finite_float(entry["ratio"])
                cos = _finite_float(entry["cos"])
                if ratio is not None:
                    stats.ratio_by_step.setdefault(step, []).append(ratio)
                if cos is not None:
                    stats.cos_by_step.setdefault(step, []).append(cos)
            continue
        if step_match := APPLY_STEP_RE.search(line):
            step = int(step_match["step"])
            for entry in APPLY_ENTRY_RE.finditer(line):
                base = _finite_float(entry["base"])
                corr = _finite_float(entry["corr"])
                scale = _finite_float(entry["scale"])
                if base is None or corr is None or scale is None or base <= 0:
                    continue
                stats.eff_frac_by_step.setdefault(step, []).append((corr * scale) / base)
    return stats


def _common_steps(active: LaneStats, control: LaneStats) -> list[int]:
    return sorted(set(active.vals) & set(control.vals))


def print_report(
    active: LaneStats,
    control: LaneStats,
    *,
    k: int,
    decision_step: int,
    material_gain: float,
) -> None:
    steps = _common_steps(active, control)
    print("# Track 3 LocoProp-M Prefix Effect Size")
    print()
    print(f"Active: `{active.path}`")
    print(f"Control: `{control.path}`")
    print(f"Local-step diagnostic: K={k}")
    print()

    print("## Loss Match")
    print()
    print("| step | active | alpha_zero | control-active |")
    print("| ---: | ---: | ---: | ---: |")
    deltas: list[float] = []
    for step in steps:
        delta = control.vals[step] - active.vals[step]
        deltas.append(delta)
        print(f"| {step} | {_fmt(active.vals[step])} | {_fmt(control.vals[step])} | {_fmt(delta, 5)} |")
    print()
    max_abs = max((abs(delta) for delta in deltas), default=float("nan"))
    final_delta = deltas[-1] if deltas else float("nan")
    print(f"Max absolute loss delta on shared screens: `{_fmt(max_abs, 5)}`")
    print(f"Final control-active delta: `{_fmt(final_delta, 5)}`")
    print()

    decision_delta = None
    if decision_step in active.vals and decision_step in control.vals:
        decision_delta = control.vals[decision_step] - active.vals[decision_step]
    elif steps:
        fallback_step = steps[-1]
        decision_delta = control.vals[fallback_step] - active.vals[fallback_step]
    print("## Gate")
    print()
    print(f"Decision step requested: `{decision_step}`")
    if decision_delta is None:
        print("Decision delta: `missing`")
        print("Gate read: `missing shared validation screen`")
    else:
        print(f"Material gain threshold: `{material_gain:.5f}`")
        print(f"Decision delta control-active: `{decision_delta:.5f}`")
        if decision_delta >= material_gain:
            print("Gate read: `active beats alpha-zero materially`")
        elif abs(decision_delta) <= 5e-5:
            print("Gate read: `active matches alpha-zero`")
        elif decision_delta > 0:
            print("Gate read: `active is better, but below material threshold`")
        else:
            print("Gate read: `active is worse than alpha-zero`")
    print()

    print("## Correction Geometry")
    print()
    print("| step | median eff_corr/base_step | median cos | median local loss/loss0 | eff*cos |")
    print("| ---: | ---: | ---: | ---: | ---: |")
    for step in sorted(set(active.eff_frac_by_step) | set(active.cos_by_step) | set(active.ratio_by_step)):
        eff = _median(active.eff_frac_by_step.get(step, []))
        cos = _median(active.cos_by_step.get(step, []))
        ratio = _median(active.ratio_by_step.get(step, []))
        projected = None if eff is None or cos is None else eff * cos
        print(f"| {step} | {_fmt_sci(eff)} | {_fmt(cos, 4)} | {_fmt(ratio, 4)} | {_fmt_sci(projected)} |")
    print()

    print("## Read")
    print()
    if max_abs <= 5e-5 and abs(final_delta) <= 5e-5:
        print(
            "The active and alpha-zero curves are indistinguishable at the logged precision. "
            "The applied LocoProp correction did not measurably move validation loss in this prefix."
        )
    else:
        print(
            "The active and alpha-zero curves diverge beyond the tight precision threshold. "
            "Inspect whether the divergence is persistent and larger than validation/logging noise."
        )
    print()
    print(
        "The `eff*cos` column is the approximate base-descent-aligned component of the applied "
        "correction, as a fraction of the Muon step norm. Values near zero mean the correction "
        "is mostly sideways relative to the base descent direction."
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--active", required=True, type=Path)
    parser.add_argument("--control", required=True, type=Path)
    parser.add_argument("--k", type=int, default=5)
    parser.add_argument("--decision-step", type=int, default=2000)
    parser.add_argument("--material-gain", type=float, default=0.001)
    args = parser.parse_args()

    print_report(
        parse_log(args.active, k=args.k),
        parse_log(args.control, k=args.k),
        k=args.k,
        decision_step=args.decision_step,
        material_gain=args.material_gain,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
