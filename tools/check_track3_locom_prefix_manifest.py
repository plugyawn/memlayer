#!/usr/bin/env python3
"""Validate the decisive Track 3 LocoProp-M prefix-control lane manifest.

The 1600->1800 prefix-specificity experiment is only useful if the lanes differ
in the intended axis:

* active K5 natural LocoProp correction,
* no LocoProp,
* random same-shape correction at a fixed 2% base-step norm,
* orthogonalized true-post correction at the same fixed 2% base-step norm.

This checker can be run before launch with no logs, where it prints the intended
manifest, and after launch against generated logs, where it validates the header
line emitted by the generated training script.
"""

from __future__ import annotations

import argparse
import math
import re
from dataclasses import dataclass
from pathlib import Path


HEADER_PREFIX = "LocoM enabled="
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
    min_cos_desc: float
    intent: str


LANES = {
    "active_k5": LaneSpec("active_k5", True, "sgd", False, "normal", 0.0, 0.0, "natural true-post c_fc LocoProp K5"),
    "noloco": LaneSpec("noloco", False, "sgd", False, "normal", 0.0, 0.0, "exact no-correction checkpoint/schedule control"),
    "random_norm002": LaneSpec("random_norm002", True, "random", True, "normal", 0.02, 0.0, "same-shape random perturbation at 2% base-step norm"),
    "orthogonal_k5_norm002": LaneSpec("orthogonal_k5_norm002", True, "sgd", False, "orthogonal", 0.02, -1.0, "true-post correction with descent-parallel component removed at 2% base-step norm"),
}

COMMON_EXPECTED = {
    "layers": "all",
    "steps": 5,
    "sample_tokens": 1024,
    "local_opt": None,
    "target_space": "post",
    "true_post_grad": True,
    "require_loss_decrease": True,
    "inner_lr": 2e-4,
    "prox": 0.1,
    "alpha": 1.0,
    "norm_to_base": False,
    "norm_cap": 0.20,
    "active_windows": "0:1800",
    "end_step": 1800,
    "target_loss": 3.28,
    "seed_base": 0,
    "seed_offset": 3710,
    "cooldown_frac": 1.0,
    "lr_schedule": "power",
    "lr_power": 2.0,
    "lr_schedule_steps": 3000,
    "lr_min_eta": 0.0,
    "lr_bump_windows": "",
    "lr_switch_step": -1,
    "lr_after_switch": "",
    "resume_load_optimizers": True,
}


def _lane_from_name(path: Path) -> str | None:
    name = path.stem
    match = re.search(r"track3_prefix_(?P<lane>.+?)_seed\d+", name)
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


def _validate_lane(path: Path, header: dict[str, object], spec: LaneSpec) -> list[str]:
    errors: list[str] = []
    expected = {
        **COMMON_EXPECTED,
        "enabled": spec.enabled,
        "local_opt": spec.local_opt,
        "random_correction": spec.random_correction,
        "correction_mode": spec.correction_mode,
        "norm_target": spec.norm_target,
        "min_cos_desc": spec.min_cos_desc,
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
            logs.extend(sorted(entry.glob("track3_prefix_*.log")))
        else:
            logs.append(entry)
    return [path for path in logs if path.exists()]


def print_manifest() -> None:
    print("# Track 3 Prefix Specificity Manifest")
    print()
    print("| lane | enabled | local_opt | random | mode | norm_target | min_cos_desc | intent |")
    print("| --- | ---: | --- | ---: | --- | ---: | ---: | --- |")
    for spec in LANES.values():
        print(
            f"| {spec.lane} | {int(spec.enabled)} | {spec.local_opt} | "
            f"{int(spec.random_correction)} | {spec.correction_mode} | {spec.norm_target:.2f} | "
            f"{spec.min_cos_desc:.1f} | {spec.intent} |"
        )
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
    args = parser.parse_args()

    print_manifest()
    if args.manifest_only:
        return 0

    logs = _collect_logs(args.logs)
    if not logs:
        print()
        print("No prefix logs found; manifest only.")
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

    missing = set(LANES) - seen
    for lane in sorted(missing):
        errors.append(f"missing lane log: {lane}")

    print()
    print("Validation:")
    if errors:
        print("- FAIL")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("- PASS: all prefix lane headers match the manifest.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
