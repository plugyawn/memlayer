#!/usr/bin/env python3
"""Validate and preview the Track 3 LocoProp-M post-2000 suffix ladder."""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path


HEADER_PREFIX = "LocoM enabled="
DEFAULT_STEPS = (2000, 2025, 2050, 2075, 2100, 2125, 2200, 2250, 2325, 2400)
DEFAULT_REQUIRED_LANES = (
    "control",
    "floor111",
    "floor111_norm002_k5",
    "floor111_random002",
    "floor111_norm005_k5",
    "floor111_random005",
    "ramp111",
)
FLOAT_KEYS = {
    "inner_lr",
    "target_gamma",
    "prox",
    "alpha",
    "norm_target",
    "norm_cap",
    "target_loss",
    "cooldown_frac",
    "lr_power",
    "lr_min_eta",
}
INT_KEYS = {
    "steps",
    "sample_tokens",
    "micro_sample_tokens",
    "diag_max_layers",
    "start_step",
    "end_step",
    "interval",
    "seed_base",
    "seed_offset",
    "lr_schedule_steps",
    "lr_switch_step",
}
BOOL_KEYS = {
    "enabled",
    "gather",
    "accum",
    "aux_capture",
    "batched_prep",
    "true_post_grad",
    "lr_decay",
    "rms_reset_each_step",
    "require_loss_decrease",
    "norm_to_base",
    "random_correction",
    "soft_muon",
    "soft_norm_restore",
    "resume_load_optimizers",
}


@dataclass(frozen=True)
class LaneSpec:
    lane: str
    enabled: bool
    local_opt: str
    random_correction: bool
    correction_mode: str
    norm_target: float
    lr_min_eta: float
    lr_bump_windows: str
    intent: str


LANES = {
    "control": LaneSpec("control", False, "sgd", False, "normal", 0.0, 0.0, "", "no-correction cold-schedule control"),
    "floor111": LaneSpec("floor111", False, "sgd", False, "normal", 0.0, 0.1111111111, "", "LR floor at the step-2000 eta"),
    "floor111_norm002_k5": LaneSpec("floor111_norm002_k5", True, "sgd", False, "normal", 0.02, 0.1111111111, "", "LR floor plus true-post c_fc K5 at 2% base-step norm"),
    "floor111_random002": LaneSpec("floor111_random002", True, "random", True, "normal", 0.02, 0.1111111111, "", "LR floor plus same-shape random 2% correction"),
    "floor111_norm005_k5": LaneSpec("floor111_norm005_k5", True, "sgd", False, "normal", 0.05, 0.1111111111, "", "LR floor plus true-post c_fc K5 at 5% base-step norm"),
    "floor111_random005": LaneSpec("floor111_random005", True, "random", True, "normal", 0.05, 0.1111111111, "", "LR floor plus same-shape random 5% correction"),
    "ramp111": LaneSpec("ramp111", False, "sgd", False, "normal", 0.0, 0.0, "2000:2250:2250:2400:1.7777777778", "smooth LR multiplier ramp targeting step-2000 eta near 2250"),
    "floor111_orthogonal002": LaneSpec("floor111_orthogonal002", True, "sgd", False, "orthogonal", 0.02, 0.1111111111, "", "optional LR floor plus orthogonalized 2% correction"),
    "natural_k5": LaneSpec("natural_k5", True, "sgd", False, "normal", 0.0, 0.0, "", "optional natural-scale true-post c_fc K5"),
    "norm002_k5": LaneSpec("norm002_k5", True, "sgd", False, "normal", 0.02, 0.0, "", "optional true-post c_fc K5 at 2% base-step norm"),
    "random_norm002": LaneSpec("random_norm002", True, "random", True, "normal", 0.02, 0.0, "", "optional same-shape random 2% correction"),
    "orthogonal_norm002": LaneSpec("orthogonal_norm002", True, "sgd", False, "orthogonal", 0.02, 0.0, "", "optional orthogonalized true-post 2% correction"),
    "parallel_norm002": LaneSpec("parallel_norm002", True, "sgd", False, "parallel", 0.02, 0.0, "", "optional parallel-only true-post 2% correction"),
    "hold115": LaneSpec("hold115", False, "sgd", False, "normal", 0.0, 0.0, "2000:2050:2250:2400:1.15", "optional small LR bump from the older suffix probe"),
}

COMMON_EXPECTED = {
    "layers": "all",
    "steps": 5,
    "sample_tokens": 1024,
    "target_space": "post",
    "true_post_grad": True,
    "require_loss_decrease": True,
    "min_cos_desc": 0.0,
    "inner_lr": 2e-4,
    "prox": 0.1,
    "alpha": 1.0,
    "norm_to_base": False,
    "norm_cap": 0.20,
    "active_windows": None,
    "end_step": None,
    "target_loss": 3.28,
    "seed_base": 0,
    "seed_offset": 3710,
    "cooldown_frac": 1.0,
    "lr_schedule": "power",
    "lr_power": 2.0,
    "lr_schedule_steps": 3000,
    "lr_switch_step": -1,
    "lr_after_switch": "",
    "resume_load_optimizers": True,
}


def _parse_steps(text: str) -> tuple[int, ...]:
    if not text:
        return DEFAULT_STEPS
    return tuple(int(item) for item in text.split(",") if item.strip())


def _lane_from_name(path: Path) -> str | None:
    match = re.search(r"track3_locom_2000_(?P<lane>.+?)_seed\d+", path.stem)
    if not match:
        return None
    return match["lane"]


def _parse_bool(value: str) -> bool | None:
    lowered = value.lower()
    if lowered in {"1", "true", "yes"}:
        return True
    if lowered in {"0", "false", "no"}:
        return False
    return None


def _coerce(key: str, value: str) -> object:
    if key in BOOL_KEYS:
        parsed = _parse_bool(value)
        return value if parsed is None else parsed
    if key in INT_KEYS:
        try:
            return int(value)
        except ValueError:
            return value
    if key in FLOAT_KEYS:
        try:
            return float(value)
        except ValueError:
            return value
    return value


def _parse_header(path: Path) -> dict[str, object] | None:
    for line in path.read_text(errors="replace").splitlines():
        if not line.startswith(HEADER_PREFIX):
            continue
        values: dict[str, object] = {}
        for token in line.split():
            if "=" not in token:
                continue
            key, value = token.split("=", 1)
            values[key] = _coerce(key, value)
        return values
    return None


def _equal(expected: object, actual: object) -> bool:
    if isinstance(expected, float):
        try:
            return math.isclose(expected, float(actual), rel_tol=1e-6, abs_tol=1e-9)
        except (TypeError, ValueError):
            return False
    return expected == actual


def _parse_bump_windows(spec: str) -> list[tuple[int, int, int, int, float]]:
    windows: list[tuple[int, int, int, int, float]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) != 5:
            raise ValueError(f"bad LR bump window: {part}")
        start, ramp_end, hold_end, fade_end = map(int, fields[:4])
        mult = float(fields[4])
        windows.append((start, ramp_end, hold_end, fade_end, mult))
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


def _lr_fraction(step: int, *, lr_min_eta: float, lr_bump_windows: str) -> float:
    eta = (1.0 - step / 3000.0) ** 2.0
    eta = max(eta, lr_min_eta)
    return eta * _bump_multiplier(step, lr_bump_windows)


def _validate_lane(path: Path, header: dict[str, object], spec: LaneSpec) -> list[str]:
    errors: list[str] = []
    expected = {
        **COMMON_EXPECTED,
        "enabled": spec.enabled,
        "local_opt": spec.local_opt,
        "random_correction": spec.random_correction,
        "correction_mode": spec.correction_mode,
        "norm_target": spec.norm_target,
        "lr_min_eta": spec.lr_min_eta,
        "lr_bump_windows": spec.lr_bump_windows,
    }
    for key, value in expected.items():
        if value is None:
            continue
        actual = header.get(key)
        if not _equal(value, actual):
            errors.append(f"{path.name}: expected {key}={value!r}, got {actual!r}")
    return errors


def _collect_logs(entries: list[Path]) -> list[Path]:
    logs: list[Path] = []
    for entry in entries:
        if entry.is_dir():
            logs.extend(sorted(entry.glob("track3_locom_2000_*.log")))
        else:
            logs.append(entry)
    return [path for path in logs if path.exists()]


def print_manifest(steps: tuple[int, ...]) -> None:
    print("# Track 3 Post-2000 Suffix Manifest")
    print()
    print("| lane | enabled | local_opt | random | mode | norm_target | lr_min_eta | lr_bump_windows | intent |")
    print("| --- | ---: | --- | ---: | --- | ---: | ---: | --- | --- |")
    for lane in DEFAULT_REQUIRED_LANES:
        spec = LANES[lane]
        print(
            f"| {spec.lane} | {int(spec.enabled)} | {spec.local_opt} | "
            f"{int(spec.random_correction)} | {spec.correction_mode} | "
            f"{spec.norm_target:.2f} | {spec.lr_min_eta:.10f} | `{spec.lr_bump_windows}` | {spec.intent} |"
        )
    print()
    print("## LR Preview")
    print()
    print("| lane | " + " | ".join(str(step) for step in steps) + " |")
    print("| --- | " + " | ".join("---:" for _ in steps) + " |")
    for lane in DEFAULT_REQUIRED_LANES:
        spec = LANES[lane]
        values = [
            f"{_lr_fraction(step, lr_min_eta=spec.lr_min_eta, lr_bump_windows=spec.lr_bump_windows):.6f}"
            for step in steps
        ]
        print(f"| {lane} | " + " | ".join(values) + " |")
    print()
    print("Common invariants:")
    print()
    for key, value in COMMON_EXPECTED.items():
        if value is not None:
            print(f"- `{key}={value}`")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="*", type=Path)
    parser.add_argument("--manifest-only", action="store_true")
    parser.add_argument("--steps", default=",".join(str(step) for step in DEFAULT_STEPS))
    parser.add_argument("--required-lanes", default=",".join(DEFAULT_REQUIRED_LANES))
    args = parser.parse_args()

    steps = _parse_steps(args.steps)
    required_lanes = {item.strip() for item in args.required_lanes.split(",") if item.strip()}
    print_manifest(steps)
    if args.manifest_only:
        return 0

    logs = _collect_logs(args.logs)
    if not logs:
        print()
        print("No suffix logs found; manifest only.")
        return 0

    seen: set[str] = set()
    errors: list[str] = []
    for path in logs:
        lane = _lane_from_name(path)
        if lane not in LANES:
            errors.append(f"{path.name}: unknown lane")
            continue
        seen.add(lane)
        header = _parse_header(path)
        if header is None:
            errors.append(f"{path.name}: missing LocoM header")
            continue
        errors.extend(_validate_lane(path, header, LANES[lane]))

    for lane in sorted(required_lanes - seen):
        errors.append(f"missing lane log: {lane}")

    print()
    print("Validation:")
    if errors:
        print("- FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("- PASS: all suffix lane headers match the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
