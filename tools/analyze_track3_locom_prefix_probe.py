#!/usr/bin/env python3
"""Score the Track 3 LocoProp-M 1600->1800 prefix-specificity probe."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from analyze_track3_locom_suffix_probe import (
    Lane,
    _choose_control,
    _fmt,
    _fmt_gain,
    _gain_at,
    parse_log,
)


def _collect_paths(entries: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for entry in entries:
        if entry.is_dir():
            paths.extend(sorted(entry.glob("*.log")))
        else:
            paths.append(entry)
    return [path for path in paths if path.exists()]


def _best_lane(lanes: list[Lane], categories: set[str], control: Lane | None, step: int) -> tuple[Lane | None, float | None]:
    best_lane: Lane | None = None
    best_gain: float | None = None
    for lane in lanes:
        if lane.category not in categories:
            continue
        gain = _gain_at(lane, control, step)
        if gain is None:
            continue
        if best_gain is None or gain > best_gain:
            best_lane = lane
            best_gain = gain
    return best_lane, best_gain


def _slope(values: dict[int, float], start: int, end: int) -> float | None:
    if start not in values or end not in values or end <= start:
        return None
    return (values[start] - values[end]) / (end - start)


def print_report(
    lanes: list[Lane],
    *,
    steps: list[int],
    decision_step: int,
    material_gain: float,
    tie_eps: float,
) -> None:
    print("# Track 3 LocoProp-M Prefix Specificity Decision")
    print()
    if not lanes:
        print("No logs parsed.")
        return

    control = _choose_control(lanes)
    if control is None:
        print("No no-Loco prefix control found; decision is limited.")
    else:
        print(f"Control lane: `{control.name}` from `{control.path}`")
    print()

    print("## Validation Table")
    print()
    print("| lane | category | " + " | ".join(str(step) for step in steps) + " |")
    print("| --- | --- | " + " | ".join("---:" for _ in steps) + " |")
    for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
        values = " | ".join(_fmt(lane.vals.get(step)) for step in steps)
        print(f"| {lane.name} | {lane.category} | {values} |")
    print()

    if control is not None:
        print("## Gain Vs No-Loco")
        print()
        print("| lane | category | " + " | ".join(str(step) for step in steps) + " |")
        print("| --- | --- | " + " | ".join("---:" for _ in steps) + " |")
        for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
            if lane is control:
                continue
            gains = " | ".join(_fmt_gain(_gain_at(lane, control, step)) for step in steps)
            print(f"| {lane.name} | {lane.category} | {gains} |")
        print()

    print("## Slope Table")
    print()
    print("| lane | category | 1600->1700 drop/step | 1700->1800 drop/step |")
    print("| --- | --- | ---: | ---: |")
    for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
        s1 = _slope(lane.vals, 1600, 1700)
        s2 = _slope(lane.vals, 1700, 1800)
        print(f"| {lane.name} | {lane.category} | {_fmt(s1, 7)} | {_fmt(s2, 7)} |")
    print()

    print("## Apply-Scale Summary")
    print()
    print("| lane | category | " + " | ".join(str(step) for step in steps) + " |")
    print("| --- | --- | " + " | ".join("---:" for _ in steps) + " |")
    for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
        values = " | ".join(_fmt(lane.eff_frac_med.get(step), digits=4) for step in steps)
        print(f"| {lane.name} | {lane.category} | {values} |")
    print()

    print("## Decision")
    print()
    if control is None or decision_step not in control.vals:
        print("Read: insufficient validation data; no decision-step control point was parsed.")
        return

    active_lane, active_gain = _best_lane(lanes, {"active", "active_normed"}, control, decision_step)
    random_lane, random_gain = _best_lane(lanes, {"random", "orthogonal", "parallel"}, control, decision_step)

    print(
        f"Best active LocoProp gain @ {decision_step}: {_fmt_gain(active_gain)}"
        + (f" via `{active_lane.name}`." if active_lane else ".")
    )
    print(
        f"Best random/orthogonal/parallel gain @ {decision_step}: {_fmt_gain(random_gain)}"
        + (f" via `{random_lane.name}`." if random_lane else ".")
    )
    print()

    comparable = [
        _gain_at(lane, control, decision_step)
        for lane in lanes
        if lane is not control
    ]
    comparable = [gain for gain in comparable if gain is not None and math.isfinite(gain)]
    if not comparable:
        print("Read: insufficient validation data; no non-control lane shares the decision step.")
        return

    if active_gain is not None and active_gain >= material_gain:
        if random_gain is not None and random_gain >= active_gain - tie_eps:
            print("Read: active LocoProp wins, but perturbation/orthogonal is close; prefix gain is not clearly local-direction-specific.")
        else:
            print("Read: active LocoProp materially beats no-Loco and perturbation controls; c_fc true-post direction matters in the prefix.")
    elif random_gain is not None and random_gain >= material_gain:
        print("Read: perturbation/orthogonal beats no-Loco while active LocoProp does not; prefix gain is not LocoProp-specific.")
    else:
        print("Read: active, random, and orthogonal do not materially beat no-Loco; prefix gain is probably schedule/checkpoint state, not LocoProp.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--steps", default="1600,1625,1650,1675,1700,1725,1750,1775,1800")
    parser.add_argument("--decision-step", type=int, default=1800)
    parser.add_argument("--material-gain", type=float, default=0.0015)
    parser.add_argument("--tie-eps", type=float, default=0.0005)
    args = parser.parse_args()

    steps = [int(step) for step in args.steps.split(",") if step.strip()]
    lanes = [parse_log(path) for path in _collect_paths(args.logs)]
    print_report(
        lanes,
        steps=steps,
        decision_step=args.decision_step,
        material_gain=args.material_gain,
        tie_eps=args.tie_eps,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
