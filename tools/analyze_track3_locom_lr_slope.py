#!/usr/bin/env python3
"""Join Track 3 LocoProp-M validation slopes with the logged LR schedule.

This is a mechanism helper for the LocoProp-M thread. It is intentionally
small: parse generated training logs, compute validation-window slopes, and
print the learning-rate fraction implied by the schedule header for each
window. This helps separate "LocoProp stopped helping" from "the suffix simply
ran out of LR".
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from analyze_track3_locom_suffix_probe import Lane, _fmt, parse_log


HEADER_PREFIX = "LocoM enabled="


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


def _parse_header(path: Path) -> dict[str, str]:
    for line in path.read_text(errors="replace").splitlines():
        if not line.startswith(HEADER_PREFIX):
            continue
        out: dict[str, str] = {}
        for token in line.split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            out[key] = value
        return out
    return {}


def _float(header: dict[str, str], key: str, default: float) -> float:
    try:
        return float(header.get(key, default))
    except (TypeError, ValueError):
        return default


def _int(header: dict[str, str], key: str, default: int) -> int:
    try:
        return int(header.get(key, default))
    except (TypeError, ValueError):
        return default


def _parse_bump_windows(spec: str) -> list[tuple[int, int, int, int, float]]:
    windows: list[tuple[int, int, int, int, float]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) != 5:
            continue
        start, ramp_end, hold_end, fade_end = map(int, fields[:4])
        mult = float(fields[4])
        if start <= ramp_end <= hold_end <= fade_end:
            windows.append((start, ramp_end, hold_end, fade_end, mult))
    return windows


def _parse_floor_windows(spec: str) -> list[tuple[int, int, int, int, float]]:
    windows: list[tuple[int, int, int, int, float]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) != 5:
            continue
        start, ramp_end, hold_end, fade_end = map(int, fields[:4])
        eta = float(fields[4])
        if start <= ramp_end <= hold_end <= fade_end:
            windows.append((start, ramp_end, hold_end, fade_end, eta))
    return windows


def _bump_multiplier(step: int, spec: str) -> float:
    multiplier = 1.0
    for start, ramp_end, hold_end, fade_end, mult in _parse_bump_windows(spec):
        if step < start or step > fade_end:
            continue
        if ramp_end <= start or step >= ramp_end:
            if step <= hold_end:
                t = 1.0
            elif fade_end <= hold_end:
                t = 0.0
            else:
                t = max(0.0, (fade_end - step) / (fade_end - hold_end))
        else:
            t = (step - start) / (ramp_end - start)
        multiplier *= 1.0 + (mult - 1.0) * t
    return multiplier


def _eta_floor(step: int, header: dict[str, str]) -> float:
    eta_floor = _float(header, "lr_min_eta", 0.0)
    for start, ramp_end, hold_end, fade_end, eta in _parse_floor_windows(header.get("lr_min_eta_windows", "")):
        if step < start or step > fade_end:
            continue
        if ramp_end <= start or step >= ramp_end:
            if step <= hold_end:
                t = 1.0
            elif fade_end <= hold_end:
                t = 0.0
            else:
                t = max(0.0, (fade_end - step) / (fade_end - hold_end))
        else:
            t = (step - start) / (ramp_end - start)
        eta_floor = max(eta_floor, eta * t)
    return eta_floor


def _schedule_fraction(
    header: dict[str, str],
    step: int,
    *,
    schedule_key: str = "lr_schedule",
    steps_key: str = "lr_schedule_steps",
    power_key: str = "lr_power",
) -> float | None:
    schedule = header.get("lr_schedule", "linear")
    if schedule_key != "lr_schedule":
        schedule = header.get(schedule_key, "")
    if not schedule:
        return None
    if schedule == "pr287":
        # PR287 is group-dependent because it uses power_c and min(initial_lr, ...).
        # The generated header does not include the group power_c values.
        return None
    schedule_steps = _int(header, steps_key, 0)
    if schedule_steps <= 0:
        return None
    cooldown_frac = _float(header, "cooldown_frac", 0.7)
    lr_power = _float(header, power_key, 1.0)
    progress = step / schedule_steps
    if progress < 1.0 - cooldown_frac:
        eta = 1.0
    else:
        eta = (1.0 - progress) / cooldown_frac
        if schedule == "power":
            eta = eta**lr_power
        eta = max(eta, _eta_floor(step, header))
    return eta


def lr_fraction(header: dict[str, str], step: int) -> float | None:
    lr_mult = _bump_multiplier(step, header.get("lr_bump_windows", ""))
    base = _schedule_fraction(header, step)
    if base is None:
        return None

    base *= lr_mult
    blend_target = header.get("lr_blend_target", "")
    blend_start = _int(header, "lr_blend_start", -1)
    if not blend_target or blend_start < 0 or step < blend_start:
        return base

    target = _schedule_fraction(
        header,
        step,
        schedule_key="lr_blend_target",
        steps_key="lr_blend_target_steps",
        power_key="lr_blend_target_power",
    )
    if target is None:
        return None
    target *= lr_mult

    blend_end = _int(header, "lr_blend_end", -1)
    if blend_end <= blend_start or step >= blend_end:
        t = 1.0
    else:
        t = (step - blend_start) / (blend_end - blend_start)
        t = max(0.0, min(1.0, t))
        t = t * t * (3.0 - 2.0 * t)
    return base + (target - base) * t


def lr_fraction_for_optimizer(header: dict[str, str], step: int, opt_name: str) -> float | None:
    fraction = lr_fraction(header, step)
    if fraction is None:
        return None
    if opt_name == "adam":
        return fraction * _bump_multiplier(step, header.get("lr_adam_bump_windows", ""))
    if opt_name == "muon":
        return fraction * _bump_multiplier(step, header.get("lr_muon_bump_windows", ""))
    return fraction


def _required_slope(start_loss: float, start_step: int, target_step: int, target_loss: float) -> float | None:
    if target_step <= start_step:
        return None
    required = (start_loss - target_loss) / (target_step - start_step)
    return required if required > 0 else None


def _window_status(ratio: float | None) -> str:
    if ratio is None or not math.isfinite(ratio):
        return "missing"
    if ratio >= 1.0:
        return "healthy"
    if ratio >= 0.9:
        return "marginal"
    return "cold"


def _fmt_ratio(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value:.2f}x"


def _fmt_pct(value: float | None) -> str:
    if value is None or not math.isfinite(value):
        return "nan"
    return f"{value * 100:.1f}%"


def _steps_for(lanes: list[Lane], requested: list[int] | None) -> list[int]:
    if requested is not None:
        return requested
    steps: set[int] = set()
    for lane in lanes:
        steps.update(lane.vals)
    return sorted(steps)


def _merged_header(path: Path, defaults: dict[str, str]) -> dict[str, str]:
    header = _parse_header(path)
    return {**defaults, **header}


def print_report(
    lanes: list[Lane],
    *,
    steps: list[int],
    target_step: int,
    target_loss: float,
    schedule_defaults: dict[str, str],
) -> None:
    print("# Track 3 LocoProp-M LR/Slope Join")
    print()
    if not lanes:
        print("No logs parsed.")
        return

    print("## Step Values")
    print()
    print("| lane | category | step | val_loss | lr_frac | adam_frac | muon_frac |")
    print("| --- | --- | ---: | ---: | ---: | ---: | ---: |")
    headers = {lane.name: _merged_header(lane.path, schedule_defaults) for lane in lanes}
    for lane in sorted(lanes, key=lambda item: item.name):
        header = headers[lane.name]
        for step in steps:
            if step not in lane.vals:
                continue
            print(
                f"| {lane.name} | {lane.category} | {step} | {_fmt(lane.vals[step])} | "
                f"{_fmt(lr_fraction(header, step), 6)} | "
                f"{_fmt(lr_fraction_for_optimizer(header, step, 'adam'), 6)} | "
                f"{_fmt(lr_fraction_for_optimizer(header, step, 'muon'), 6)} |"
            )
    print()

    print("## Window Slopes")
    print()
    print("| lane | category | window | drop | drop/step | rolling target/step | ratio | lr start | lr end | lr drop | status |")
    print("| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- |")
    for lane in sorted(lanes, key=lambda item: item.name):
        header = headers[lane.name]
        for start, end in zip(steps, steps[1:]):
            if start not in lane.vals or end not in lane.vals or end <= start:
                continue
            drop = lane.vals[start] - lane.vals[end]
            slope = drop / (end - start)
            required = _required_slope(lane.vals[start], start, target_step, target_loss)
            ratio = slope / required if required else None
            lr_start = lr_fraction(header, start)
            lr_end = lr_fraction(header, end)
            lr_drop = None
            if lr_start is not None and lr_start > 0 and lr_end is not None:
                lr_drop = (lr_start - lr_end) / lr_start
            print(
                f"| {lane.name} | {lane.category} | {start}->{end} | {_fmt(drop)} | {_fmt(slope, 7)} | "
                f"{_fmt(required, 7)} | {_fmt_ratio(ratio)} | {_fmt(lr_start, 6)} | {_fmt(lr_end, 6)} | "
                f"{_fmt_pct(lr_drop)} | {_window_status(ratio)} |"
            )
    print()

    print("## Read")
    print()
    for lane in sorted(lanes, key=lambda item: item.name):
        cold_windows: list[str] = []
        healthy_windows: list[str] = []
        for start, end in zip(steps, steps[1:]):
            if start not in lane.vals or end not in lane.vals or end <= start:
                continue
            slope = (lane.vals[start] - lane.vals[end]) / (end - start)
            required = _required_slope(lane.vals[start], start, target_step, target_loss)
            status = _window_status(slope / required if required else None)
            if status == "healthy":
                healthy_windows.append(f"{start}->{end}")
            elif status == "cold":
                cold_windows.append(f"{start}->{end}")
        last_healthy = healthy_windows[-1] if healthy_windows else "none"
        first_cold = cold_windows[0] if cold_windows else "none"
        print(f"- `{lane.name}`: last healthy `{last_healthy}`, first cold `{first_cold}`.")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--steps", default="")
    parser.add_argument("--target-step", type=int, default=3000)
    parser.add_argument("--target-loss", type=float, default=3.28)
    parser.add_argument("--default-lr-schedule", default="")
    parser.add_argument("--default-lr-power", default="")
    parser.add_argument("--default-lr-schedule-steps", default="")
    parser.add_argument("--default-cooldown-frac", default="")
    parser.add_argument("--default-lr-min-eta", default="")
    parser.add_argument("--default-lr-bump-windows", default="")
    parser.add_argument("--default-lr-adam-bump-windows", default="")
    parser.add_argument("--default-lr-muon-bump-windows", default="")
    args = parser.parse_args()

    schedule_defaults = {
        key: value
        for key, value in {
            "lr_schedule": args.default_lr_schedule,
            "lr_power": args.default_lr_power,
            "lr_schedule_steps": args.default_lr_schedule_steps,
            "cooldown_frac": args.default_cooldown_frac,
            "lr_min_eta": args.default_lr_min_eta,
            "lr_bump_windows": args.default_lr_bump_windows,
            "lr_adam_bump_windows": args.default_lr_adam_bump_windows,
            "lr_muon_bump_windows": args.default_lr_muon_bump_windows,
        }.items()
        if value != ""
    }
    lanes = [parse_log(path) for path in _collect_paths(args.logs)]
    print_report(
        lanes,
        steps=_steps_for(lanes, _parse_steps(args.steps)),
        target_step=args.target_step,
        target_loss=args.target_loss,
        schedule_defaults=schedule_defaults,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
