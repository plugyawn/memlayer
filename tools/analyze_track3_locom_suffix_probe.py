#!/usr/bin/env python3
"""Score Track 3 LocoProp-M suffix probes against a no-correction control.

The 2000-suffix experiment is meant to answer a mechanism question, not just
print a curve:

* does true-post c_fc LocoProp beat the exact no-correction suffix?
* does random or orthogonal correction match it?
* does a small LR hold explain the gain better than LocoProp direction?

This script parses the generated training logs and prints a compact Markdown
decision report.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median


VAL_RE = re.compile(r"step:(?P<step>\d+)/\d+\s+val_loss:(?P<loss>[0-9.]+)")
HEADER_RE = re.compile(
    r"LocoM enabled=(?P<enabled>\w+).*?"
    r"local_opt=(?P<local_opt>\S+).*?"
    r"random_correction=(?P<random>\w+).*?"
    r"correction_mode=(?P<mode>\S+).*?"
    r"norm_target=(?P<norm_target>[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?)"
    r".*?lr_bump_windows=(?P<lr_bump>\S*)"
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
class Lane:
    path: Path
    name: str
    category: str
    vals: dict[int, float] = field(default_factory=dict)
    enabled: str | None = None
    local_opt: str | None = None
    random: str | None = None
    mode: str | None = None
    norm_target: float | None = None
    lr_bump: str = ""
    eff_frac_med: dict[int, float] = field(default_factory=dict)


def _float_or_none(text: str) -> float | None:
    try:
        value = float(text)
    except ValueError:
        return None
    return value if math.isfinite(value) else None


def _fmt(value: float | None, digits: int = 5) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.{digits}f}"


def _fmt_gain(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:+.5f}"


def _infer_category(name: str, lane: Lane) -> str:
    lowered = name.lower()
    if "control" in lowered or "noloco" in lowered:
        return "control"
    if "hold" in lowered or "bump" in lowered or "floor" in lowered or "eta" in lowered or lane.lr_bump:
        return "scheduler"
    if "random" in lowered or lane.local_opt == "random" or lane.random == "True":
        return "random"
    if "orthogonal" in lowered:
        return "orthogonal"
    if "parallel" in lowered:
        return "parallel"
    if "norm" in lowered:
        return "active_normed"
    if "active" in lowered or "natural" in lowered or "locom" in lowered:
        return "active"
    return "unknown"


def _lane_name(path: Path) -> str:
    stem = path.stem
    return (
        stem.removeprefix("track3_locom_2000_")
        .removeprefix("track3_from2000_")
        .removeprefix("track3_prefix_")
        .removesuffix("_seed3710")
    )


def parse_log(path: Path) -> Lane:
    lane = Lane(path=path, name=_lane_name(path), category="unknown")
    apply_entries: dict[int, list[float]] = {}
    for line in path.read_text(errors="replace").splitlines():
        if match := VAL_RE.search(line):
            lane.vals[int(match["step"])] = float(match["loss"])
            continue
        if match := HEADER_RE.search(line):
            lane.enabled = match["enabled"]
            lane.local_opt = match["local_opt"]
            lane.random = match["random"]
            lane.mode = match["mode"]
            lane.norm_target = _float_or_none(match["norm_target"])
            lane.lr_bump = match["lr_bump"]
            continue
        if step_match := APPLY_STEP_RE.search(line):
            step = int(step_match["step"])
            for entry in APPLY_ENTRY_RE.finditer(line):
                base = _float_or_none(entry["base"])
                corr = _float_or_none(entry["corr"])
                scale = _float_or_none(entry["scale"])
                if base is None or corr is None or scale is None or base <= 0:
                    continue
                apply_entries.setdefault(step, []).append((corr * scale) / base)
    for step, values in apply_entries.items():
        finite = [value for value in values if math.isfinite(value)]
        if finite:
            lane.eff_frac_med[step] = float(median(finite))
    lane.category = _infer_category(lane.name, lane)
    return lane


def _choose_control(lanes: list[Lane]) -> Lane | None:
    controls = [lane for lane in lanes if lane.category == "control"]
    if not controls:
        return None
    return max(controls, key=lambda lane: len(lane.vals))


def _common_steps(lanes: list[Lane], requested: list[int] | None) -> list[int]:
    if requested:
        return requested
    steps: set[int] = set()
    for lane in lanes:
        steps.update(lane.vals)
    return sorted(steps)


def _gain_at(lane: Lane, control: Lane | None, step: int) -> float | None:
    if control is None:
        return None
    if step not in lane.vals or step not in control.vals:
        return None
    return control.vals[step] - lane.vals[step]


def _best_gain(lanes: list[Lane], control: Lane | None, categories: set[str], steps: list[int]) -> tuple[Lane | None, int | None, float | None]:
    best_lane: Lane | None = None
    best_step: int | None = None
    best_gain: float | None = None
    for lane in lanes:
        if lane.category not in categories:
            continue
        for step in steps:
            gain = _gain_at(lane, control, step)
            if gain is None:
                continue
            if best_gain is None or gain > best_gain:
                best_lane, best_step, best_gain = lane, step, gain
    return best_lane, best_step, best_gain


def _required_target(start_step: int, start_loss: float, step: int, *, target_step: int, target_loss: float) -> float | None:
    if target_step <= start_step:
        return None
    slope = (start_loss - target_loss) / (target_step - start_step)
    return start_loss - slope * (step - start_step)


def _parse_slope_windows(spec: str) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.replace("->", ":").split(":")
        if len(fields) != 2:
            continue
        start, end = (int(fields[0]), int(fields[1]))
        if end > start:
            windows.append((start, end))
    return windows


def _drop_per_100(lane: Lane, start: int, end: int) -> float | None:
    if start not in lane.vals or end not in lane.vals or end <= start:
        return None
    return (lane.vals[start] - lane.vals[end]) * 100.0 / (end - start)


def _required_drop_per_100(lane: Lane, start: int, *, target_step: int, target_loss: float) -> float | None:
    if start not in lane.vals or target_step <= start:
        return None
    required = (lane.vals[start] - target_loss) * 100.0 / (target_step - start)
    return required if required > 0 else None


def _fmt_ratio(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.2f}x"


def _slope_status(ref_ratio: float | None, required_ratio: float | None, preserve_threshold: float) -> str:
    if ref_ratio is not None and math.isfinite(ref_ratio) and ref_ratio >= preserve_threshold:
        return "preserved"
    if required_ratio is not None and math.isfinite(required_ratio) and required_ratio >= 1.0:
        return "enough"
    if required_ratio is not None and math.isfinite(required_ratio) and required_ratio >= 0.9:
        return "marginal"
    return "cold"


def print_report(
    lanes: list[Lane],
    *,
    steps: list[int],
    material_gain: float,
    tie_eps: float,
    target_step: int,
    target_loss: float,
    reference_drop_per_100: float,
    preserve_threshold: float,
    slope_windows: list[tuple[int, int]],
) -> None:
    if not lanes:
        print("No logs parsed.")
        return
    control = _choose_control(lanes)
    print("# Track 3 LocoProp-M 2000 Suffix Decision")
    print()
    if control is None:
        print("No no-correction control lane found; deltas and decisions are limited.")
    else:
        print(f"Control lane: `{control.name}` from `{control.path}`")
    print()

    print("## Validation Table")
    print()
    header = "| lane | category | " + " | ".join(str(step) for step in steps) + " |"
    sep = "| --- | --- | " + " | ".join("---:" for _ in steps) + " |"
    print(header)
    print(sep)
    for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
        values = " | ".join(_fmt(lane.vals.get(step)) for step in steps)
        print(f"| {lane.name} | {lane.category} | {values} |")
    print()

    if control is not None:
        print("## Gain Vs Control")
        print()
        print("| lane | category | " + " | ".join(str(step) for step in steps) + " |")
        print("| --- | --- | " + " | ".join("---:" for _ in steps) + " |")
        for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
            if lane is control:
                continue
            gains = " | ".join(_fmt_gain(_gain_at(lane, control, step)) for step in steps)
            print(f"| {lane.name} | {lane.category} | {gains} |")
        print()

    print("## Required-Line Check")
    print()
    if control is None or not control.vals:
        print("No control start loss available.")
    else:
        start_step = min(control.vals)
        start_loss = control.vals[start_step]
        print(f"Target line: from `{start_loss:.5f} @ {start_step}` to `{target_loss:.5f} @ {target_step}`.")
        print()
        print("| step | required | control | control - required |")
        print("| ---: | ---: | ---: | ---: |")
        for step in steps:
            required = _required_target(start_step, start_loss, step, target_step=target_step, target_loss=target_loss)
            control_loss = control.vals.get(step)
            diff = None if required is None or control_loss is None else control_loss - required
            print(f"| {step} | {_fmt(required)} | {_fmt(control_loss)} | {_fmt_gain(diff)} |")
    print()

    print("## Slope Preservation")
    print()
    print(
        f"Reference healthy slope: `{reference_drop_per_100:.5f}` loss per 100 steps "
        "from the observed 1900->2000 window."
    )
    print()
    print("| lane | category | window | drop/100 | vs reference | vs required | status |")
    print("| --- | --- | --- | ---: | ---: | ---: | --- |")
    best_preserve_lane: Lane | None = None
    best_preserve_window: tuple[int, int] | None = None
    best_preserve_ratio: float | None = None
    for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
        for start, end in slope_windows:
            drop100 = _drop_per_100(lane, start, end)
            if drop100 is None:
                continue
            ref_ratio = drop100 / reference_drop_per_100 if reference_drop_per_100 > 0 else None
            required100 = _required_drop_per_100(lane, start, target_step=target_step, target_loss=target_loss)
            required_ratio = drop100 / required100 if required100 and required100 > 0 else None
            if ref_ratio is not None and (best_preserve_ratio is None or ref_ratio > best_preserve_ratio):
                best_preserve_lane = lane
                best_preserve_window = (start, end)
                best_preserve_ratio = ref_ratio
            print(
                f"| {lane.name} | {lane.category} | {start}->{end} | {_fmt(drop100)} | "
                f"{_fmt_ratio(ref_ratio)} | {_fmt_ratio(required_ratio)} | "
                f"{_slope_status(ref_ratio, required_ratio, preserve_threshold)} |"
            )
    print()

    print("## Apply-Scale Summary")
    print()
    print("| lane | category | " + " | ".join(str(step) for step in steps) + " |")
    print("| --- | --- | " + " | ".join("---:" for _ in steps) + " |")
    for lane in sorted(lanes, key=lambda item: (item.category, item.name)):
        values = " | ".join(_fmt(lane.eff_frac_med.get(step), digits=4) for step in steps)
        print(f"| {lane.name} | {lane.category} | {values} |")
    print()

    active_lane, active_step, active_gain = _best_gain(
        lanes,
        control,
        {"active", "active_normed"},
        steps,
    )
    random_lane, random_step, random_gain = _best_gain(
        lanes,
        control,
        {"random", "orthogonal", "parallel"},
        steps,
    )
    scheduler_lane, scheduler_step, scheduler_gain = _best_gain(
        lanes,
        control,
        {"scheduler"},
        steps,
    )

    print("## Decision")
    print()
    if control is None or not control.vals:
        print("Read: insufficient validation data; no control curve was parsed.")
        return
    comparable = [
        _gain_at(lane, control, step)
        for lane in lanes
        if lane is not control
        for step in steps
    ]
    comparable = [gain for gain in comparable if gain is not None]
    if not comparable:
        print("Read: insufficient validation data; no non-control lane shares validation steps with the control.")
        return

    print(
        f"Best active LocoProp gain: {_fmt_gain(active_gain)}"
        + (f" at {active_step} via `{active_lane.name}`." if active_lane and active_step else ".")
    )
    print(
        f"Best random/orthogonal/parallel gain: {_fmt_gain(random_gain)}"
        + (f" at {random_step} via `{random_lane.name}`." if random_lane and random_step else ".")
    )
    print(
        f"Best scheduler-only gain: {_fmt_gain(scheduler_gain)}"
        + (f" at {scheduler_step} via `{scheduler_lane.name}`." if scheduler_lane and scheduler_step else ".")
    )
    print(
        f"Best slope preservation: {_fmt_ratio(best_preserve_ratio)}"
        + (
            f" on {best_preserve_window[0]}->{best_preserve_window[1]} via `{best_preserve_lane.name}`."
            if best_preserve_lane and best_preserve_window
            else "."
        )
    )
    print()

    if active_gain is not None and active_gain >= material_gain:
        if random_gain is not None and random_gain >= active_gain - tie_eps:
            print("Read: active LocoProp improves, but random/orthogonal is close; the effect is not clearly local-descent-specific.")
        else:
            print("Read: active LocoProp materially beats control and perturbation controls; c_fc true-post direction still matters in this suffix.")
    elif scheduler_gain is not None and scheduler_gain >= material_gain:
        print("Read: scheduler-only beats control while LocoProp does not; the post-2000 failure is mainly LR/velocity, not local-solve direction.")
    elif random_gain is not None and random_gain >= material_gain:
        print("Read: perturbation controls beat control while active LocoProp does not; treat the effect as state/noise exploration, not LocoProp.")
    else:
        print("Read: no lane materially beats control; the 2000 state has likely lost c_fc LocoProp-specific leverage.")
    if best_preserve_ratio is not None and best_preserve_ratio < preserve_threshold:
        print("Slope read: no lane preserves the 1900->2000 descent rate; this is still a slope-starvation result.")
    elif best_preserve_lane is not None:
        print("Slope read: at least one lane preserves the 1900->2000 descent-rate target; inspect its validation gain before promoting.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path, help="log files or directories containing .log files")
    parser.add_argument("--steps", default="", help="comma-separated validation steps to report; default uses all parsed steps")
    parser.add_argument("--material-gain", type=float, default=0.0015)
    parser.add_argument("--tie-eps", type=float, default=0.0005)
    parser.add_argument("--target-step", type=int, default=3000)
    parser.add_argument("--target-loss", type=float, default=3.28)
    parser.add_argument("--reference-drop-per-100", type=float, default=0.01140)
    parser.add_argument("--preserve-threshold", type=float, default=0.90)
    parser.add_argument("--slope-windows", default="2000:2100,2100:2125,2000:2250")
    args = parser.parse_args()

    paths: list[Path] = []
    for entry in args.logs:
        if entry.is_dir():
            paths.extend(sorted(entry.glob("*.log")))
        else:
            paths.append(entry)
    lanes = [parse_log(path) for path in paths if path.exists()]
    requested_steps = [int(step) for step in args.steps.split(",") if step.strip()] if args.steps else None
    steps = _common_steps(lanes, requested_steps)
    print_report(
        lanes,
        steps=steps,
        material_gain=args.material_gain,
        tie_eps=args.tie_eps,
        target_step=args.target_step,
        target_loss=args.target_loss,
        reference_drop_per_100=args.reference_drop_per_100,
        preserve_threshold=args.preserve_threshold,
        slope_windows=_parse_slope_windows(args.slope_windows),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
