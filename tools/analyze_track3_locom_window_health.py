#!/usr/bin/env python3
"""Summarize Track 3 LocoProp-M validation slope health by time window.

This is a small mechanism tool for the "what makes LocoProp-M tick?" thread.
It answers a narrower question than the prefix/suffix decision analyzers:

* which validation windows are still descending fast enough to reach a target?
* where does the slope break happen?
* does the same checkpoint with random/no-correction preserve the window slope?

The default target line is from step 1800 to 3.28 at step 3000 because that is
the current LocoProp-M prefix handoff point we have been using.
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from analyze_track3_locom_suffix_probe import Lane, _fmt, _fmt_gain, parse_log


def _collect_paths(entries: list[Path]) -> list[Path]:
    paths: list[Path] = []
    for entry in entries:
        if entry.is_dir():
            paths.extend(sorted(entry.glob("*.log")))
        else:
            paths.append(entry)
    return [path for path in paths if path.exists()]


def _parse_steps(text: str) -> list[int] | None:
    if not text:
        return None
    return [int(item) for item in text.split(",") if item.strip()]


def _target_loss_from_start(start_loss: float, start_step: int, step: int, target_step: int, target_loss: float) -> float:
    if target_step <= start_step:
        return target_loss
    frac = (step - start_step) / (target_step - start_step)
    return start_loss + frac * (target_loss - start_loss)


def _drop_per_step(vals: dict[int, float], start: int, end: int) -> float | None:
    if start not in vals or end not in vals or end <= start:
        return None
    return (vals[start] - vals[end]) / (end - start)


def _window_status(fixed_ratio: float | None, rolling_ratio: float | None) -> str:
    ratio = rolling_ratio if rolling_ratio is not None and math.isfinite(rolling_ratio) else fixed_ratio
    if ratio is None or not math.isfinite(ratio):
        return "missing"
    if ratio >= 1.0:
        return "healthy"
    if ratio >= 0.9:
        return "marginal"
    return "cold"


def _format_ratio(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.2f}x"


def _intervals_for(lane: Lane, requested_steps: list[int] | None) -> list[tuple[int, int]]:
    steps = requested_steps if requested_steps is not None else sorted(lane.vals)
    pairs: list[tuple[int, int]] = []
    for start, end in zip(steps, steps[1:]):
        if start in lane.vals and end in lane.vals and end > start:
            pairs.append((start, end))
    return pairs


def print_report(
    lanes: list[Lane],
    *,
    steps: list[int] | None,
    start_step: int,
    target_step: int,
    target_loss: float,
) -> None:
    print("# Track 3 LocoProp-M Window Health")
    print()
    if not lanes:
        print("No logs parsed.")
        return

    print("## Validation Values")
    print()
    all_steps = steps if steps is not None else sorted({step for lane in lanes for step in lane.vals})
    print("| lane | category | " + " | ".join(str(step) for step in all_steps) + " |")
    print("| --- | --- | " + " | ".join("---:" for _ in all_steps) + " |")
    for lane in sorted(lanes, key=lambda item: item.name):
        values = " | ".join(_fmt(lane.vals.get(step)) for step in all_steps)
        print(f"| {lane.name} | {lane.category} | {values} |")
    print()

    print("## Required Line")
    print()
    for lane in sorted(lanes, key=lambda item: item.name):
        if start_step not in lane.vals:
            continue
        start_loss = lane.vals[start_step]
        print(f"`{lane.name}` target line: {start_loss:.5f} @ {start_step} -> {target_loss:.5f} @ {target_step}")
        print()
        print("| step | required | actual | actual - required |")
        print("| ---: | ---: | ---: | ---: |")
        for step in all_steps:
            if step < start_step or step not in lane.vals:
                continue
            required = _target_loss_from_start(start_loss, start_step, step, target_step, target_loss)
            print(f"| {step} | {_fmt(required)} | {_fmt(lane.vals[step])} | {_fmt_gain(lane.vals[step] - required)} |")
        print()

    print("## Window Slopes")
    print()
    print("| lane | category | window | drop | drop/step | fixed-target ratio | rolling-target ratio | status |")
    print("| --- | --- | --- | ---: | ---: | ---: | ---: | --- |")
    for lane in sorted(lanes, key=lambda item: item.name):
        if start_step not in lane.vals:
            continue
        fixed_required = (lane.vals[start_step] - target_loss) / max(target_step - start_step, 1)
        for start, end in _intervals_for(lane, all_steps):
            slope = _drop_per_step(lane.vals, start, end)
            if slope is None:
                continue
            rolling_required = (lane.vals[start] - target_loss) / (target_step - start) if target_step > start else None
            fixed_ratio = slope / fixed_required if fixed_required > 0 else None
            rolling_ratio = slope / rolling_required if rolling_required and rolling_required > 0 else None
            print(
                f"| {lane.name} | {lane.category} | {start}->{end} | "
                f"{_fmt(slope * (end - start))} | {_fmt(slope, 7)} | "
                f"{_format_ratio(fixed_ratio)} | {_format_ratio(rolling_ratio)} | "
                f"{_window_status(fixed_ratio, rolling_ratio)} |"
            )
    print()

    print("## Read")
    print()
    for lane in sorted(lanes, key=lambda item: item.name):
        if start_step not in lane.vals:
            continue
        last_healthy: tuple[int, int] | None = None
        first_cold: tuple[int, int] | None = None
        fixed_required = (lane.vals[start_step] - target_loss) / max(target_step - start_step, 1)
        for start, end in _intervals_for(lane, all_steps):
            slope = _drop_per_step(lane.vals, start, end)
            if slope is None:
                continue
            rolling_required = (lane.vals[start] - target_loss) / (target_step - start) if target_step > start else None
            fixed_ratio = slope / fixed_required if fixed_required > 0 else None
            rolling_ratio = slope / rolling_required if rolling_required and rolling_required > 0 else None
            status = _window_status(fixed_ratio, rolling_ratio)
            if status == "healthy":
                last_healthy = (start, end)
            elif status == "cold" and first_cold is None:
                first_cold = (start, end)
        healthy_text = f"{last_healthy[0]}->{last_healthy[1]}" if last_healthy else "none"
        cold_text = f"{first_cold[0]}->{first_cold[1]}" if first_cold else "none"
        print(f"- `{lane.name}`: last healthy window `{healthy_text}`; first cold window `{cold_text}`.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--steps", default="")
    parser.add_argument("--start-step", type=int, default=1800)
    parser.add_argument("--target-step", type=int, default=3000)
    parser.add_argument("--target-loss", type=float, default=3.28)
    args = parser.parse_args()

    lanes = [parse_log(path) for path in _collect_paths(args.logs)]
    print_report(
        lanes,
        steps=_parse_steps(args.steps),
        start_step=args.start_step,
        target_step=args.target_step,
        target_loss=args.target_loss,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
