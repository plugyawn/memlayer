#!/usr/bin/env python3
"""Score the Track 3 LocoProp-M layer-subset prefix probe.

The correction is active through 1800, then each lane continues without
LocoProp to 2000. The subset decision is made at 2000 so it tests whether a
static layer set can create the useful prefix state, not merely match the
instantaneous 1800 validation point.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path


VAL_RE = re.compile(r"step:(?P<step>\d+)/\d+\s+val_loss:(?P<loss>[0-9.]+)")
HEADER_RE = re.compile(r"LocoM enabled=(?P<enabled>\w+).*?layers=(?P<layers>\S+)")


@dataclass
class Lane:
    path: Path
    name: str
    category: str
    layers: str | None = None
    vals: dict[int, float] | None = None


def _collect_paths(entries: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for entry in entries:
        if entry.is_dir():
            paths.extend(sorted(entry.glob("track3_layersubset_*.log")))
        else:
            paths.append(entry)
    return [path for path in paths if path.exists()]


def _lane_name(path: Path) -> str:
    stem = path.stem
    stem = stem.removeprefix("track3_layersubset_")
    return re.sub(r"_seed\d+$", "", stem)


def _category(name: str) -> str:
    lowered = name.lower()
    if "noloco" in lowered or "control" in lowered:
        return "control"
    if "all" in lowered:
        return "active_all"
    return "subset"


def parse_log(path: Path) -> Lane:
    lane = Lane(path=path, name=_lane_name(path), category=_category(_lane_name(path)), vals={})
    for line in path.read_text(errors="replace").splitlines():
        if match := VAL_RE.search(line):
            lane.vals[int(match["step"])] = float(match["loss"])
            continue
        if match := HEADER_RE.search(line):
            lane.layers = match["layers"]
    return lane


def _fmt(value: float | None, digits: int = 5) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _fmt_gain(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:+.5f}"


def _loss(lane: Lane | None, step: int) -> float | None:
    if lane is None or lane.vals is None:
        return None
    return lane.vals.get(step)


def _gain(lane: Lane, control: Lane | None, step: int) -> float | None:
    lane_loss = _loss(lane, step)
    control_loss = _loss(control, step)
    if lane_loss is None or control_loss is None:
        return None
    return control_loss - lane_loss


def _delta_vs_all(lane: Lane, active_all: Lane | None, step: int) -> float | None:
    lane_loss = _loss(lane, step)
    all_loss = _loss(active_all, step)
    if lane_loss is None or all_loss is None:
        return None
    return lane_loss - all_loss


def _choose_control(lanes: list[Lane]) -> Lane | None:
    controls = [lane for lane in lanes if lane.category == "control"]
    return max(controls, key=lambda lane: len(lane.vals or {})) if controls else None


def _choose_all(lanes: list[Lane]) -> Lane | None:
    active = [lane for lane in lanes if lane.category == "active_all"]
    return max(active, key=lambda lane: len(lane.vals or {})) if active else None


def print_report(
    lanes: list[Lane],
    *,
    steps: list[int],
    decision_step: int,
    expected_all_loss: float | None,
    expected_all_tol: float,
    tie_eps: float,
    material_gain: float,
) -> None:
    print("# Track 3 LocoProp-M Layer-Subset Decision")
    print()
    if not lanes:
        print("No logs parsed.")
        return

    control = _choose_control(lanes)
    active_all = _choose_all(lanes)
    print(f"Control lane: `{control.name if control else 'missing'}`")
    print(f"All-layer active lane: `{active_all.name if active_all else 'missing'}`")
    print()

    print("## Validation Table")
    print()
    print("| lane | category | layers | " + " | ".join(str(step) for step in steps) + " |")
    print("| --- | --- | --- | " + " | ".join("---:" for _ in steps) + " |")
    for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
        values = " | ".join(_fmt(_loss(lane, step)) for step in steps)
        print(f"| {lane.name} | {lane.category} | {lane.layers or 'unknown'} | {values} |")
    print()

    print("## Gain Table")
    print()
    print("| lane | gain vs no-Loco @ decision | delta vs all-layer @ decision |")
    print("| --- | ---: | ---: |")
    for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
        if lane is control:
            continue
        print(
            f"| {lane.name} | {_fmt_gain(_gain(lane, control, decision_step))} | "
            f"{_fmt_gain(_delta_vs_all(lane, active_all, decision_step))} |"
        )
    print()

    print("## Decision")
    print()
    all_loss = _loss(active_all, decision_step)
    if active_all is None or control is None or all_loss is None or _loss(control, decision_step) is None:
        print("Read: insufficient decision-step data.")
        return
    if expected_all_loss is not None:
        delta = all_loss - expected_all_loss
        print(
            f"Known all-layer reproduction check @ {decision_step}: expected {_fmt(expected_all_loss)}, "
            f"actual {_fmt(all_loss)}, delta {_fmt_gain(delta)}."
        )
        print()
        if abs(delta) > expected_all_tol:
            print("Read: all-layer active did not reproduce the known prefix; do not interpret subset lanes.")
            return

    all_gain = _gain(active_all, control, decision_step)
    if all_gain is None or all_gain < material_gain:
        print("Read: all-layer active does not materially beat no-Loco, so subset interpretation is not useful.")
        return

    subset_lanes = [lane for lane in lanes if lane.category == "subset"]
    close = [
        lane
        for lane in subset_lanes
        if (delta := _delta_vs_all(lane, active_all, decision_step)) is not None and delta <= tie_eps
    ]
    better = [
        lane
        for lane in subset_lanes
        if (delta := _delta_vs_all(lane, active_all, decision_step)) is not None and delta < -tie_eps
    ]
    if better:
        names = ", ".join(f"`{lane.name}`" for lane in better)
        print(f"Read: {names} beat all-layer active; weak/risky layers are likely diluting the useful prefix.")
    elif close:
        names = ", ".join(f"`{lane.name}`" for lane in close)
        print(f"Read: {names} match all-layer active within tolerance; use the smallest matching subset for speed.")
    else:
        print("Read: no subset matches all-layer active; the prefix effect is distributed or needs weak layers too.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--steps", default="1600,1625,1650,1675,1700,1725,1750,1775,1800,1900,2000")
    parser.add_argument("--decision-step", type=int, default=2000)
    parser.add_argument("--expected-all-loss", type=float, default=3.37334)
    parser.add_argument("--expected-all-tol", type=float, default=0.003)
    parser.add_argument("--tie-eps", type=float, default=0.0005)
    parser.add_argument("--material-gain", type=float, default=0.0015)
    args = parser.parse_args()

    lanes = [parse_log(path) for path in _collect_paths(args.logs)]
    steps = [int(step) for step in args.steps.split(",") if step.strip()]
    print_report(
        lanes,
        steps=steps,
        decision_step=args.decision_step,
        expected_all_loss=args.expected_all_loss,
        expected_all_tol=args.expected_all_tol,
        tie_eps=args.tie_eps,
        material_gain=args.material_gain,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
