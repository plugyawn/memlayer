#!/usr/bin/env python3
"""Validate the Track 3 LocoProp-M layer-subset probe manifest.

This probe follows the prefix-specificity screen, but changes only the active
LocoProp layer set:

* all c_fc layers,
* robust core layers 7-10,
* expanded layers 6-10,
* no-Loco control.

It is meant to test whether the prefix effect is carried by the healthy late
MLP layers identified by kdiag, or whether all-layer state changes are needed.
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
    layers: str
    intent: str
    required: bool = True


LANES = {
    "active_all": LaneSpec("active_all", True, "all", "known all-layer active K5 prefix"),
    "core_7_10": LaneSpec("core_7_10", True, "7,8,9,10", "robust K5/K8/K10 strong-layer core"),
    "expanded_6_10": LaneSpec("expanded_6_10", True, "6,7,8,9,10", "core plus layer 6, which joins at K8/K10"),
    "freq_0_6_10": LaneSpec("freq_0_6_10", True, "0,6,10", "optional high-acceptance-frequency contrast", required=False),
    "noloco": LaneSpec("noloco", False, "all", "exact no-correction control"),
}

COMMON_EXPECTED = {
    "steps": 5,
    "sample_tokens": 1024,
    "local_opt": "sgd",
    "target_space": "post",
    "true_post_grad": True,
    "random_correction": False,
    "correction_mode": "normal",
    "require_loss_decrease": True,
    "min_cos_desc": 0.0,
    "inner_lr": 2e-4,
    "prox": 0.1,
    "alpha": 1.0,
    "norm_to_base": False,
    "norm_target": 0.0,
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
    match = re.search(r"track3_layersubset_(?P<lane>.+?)_seed\d+", path.stem)
    return None if match is None else match["lane"]


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
        "layers": spec.layers,
    }
    for key, value in expected.items():
        actual = header.get(key)
        if not _equal(value, actual):
            errors.append(f"{path.name}: expected {key}={value!r}, got {actual!r}")
    return errors


def _collect_logs(entries: list[Path]) -> list[Path]:
    logs: list[Path] = []
    for entry in entries:
        if entry.is_dir():
            logs.extend(sorted(entry.glob("track3_layersubset_*.log")))
        else:
            logs.append(entry)
    return [path for path in logs if path.exists()]


def print_manifest() -> None:
    print("# Track 3 LocoProp-M Layer-Subset Manifest")
    print()
    print("| lane | required | enabled | layers | intent |")
    print("| --- | ---: | ---: | --- | --- |")
    for spec in LANES.values():
        print(f"| {spec.lane} | {int(spec.required)} | {int(spec.enabled)} | {spec.layers} | {spec.intent} |")
    print()
    print("Common invariants:")
    print()
    for key, value in COMMON_EXPECTED.items():
        print(f"- `{key}={value}`")


def validate(logs: list[Path]) -> int:
    errors: list[str] = []
    seen: set[str] = set()
    for path in logs:
        lane = _lane_from_name(path)
        if lane is None:
            errors.append(f"{path.name}: could not infer layer-subset lane")
            continue
        seen.add(lane)
        spec = LANES.get(lane)
        if spec is None:
            errors.append(f"{path.name}: unexpected lane {lane!r}")
            continue
        header = _parse_header(path)
        if header is None:
            errors.append(f"{path.name}: no LocoM header found")
            continue
        errors.extend(_validate_lane(path, header, spec))
    required_lanes = {lane for lane, spec in LANES.items() if spec.required}
    missing = required_lanes - seen
    if missing:
        errors.append(f"missing lanes: {sorted(missing)}")

    print_manifest()
    print()
    print("## Validation")
    print()
    if errors:
        print("FAIL")
        for error in errors:
            print(f"- {error}")
        return 1
    print("PASS: all layer-subset lane headers match the manifest.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="*", type=Path)
    parser.add_argument("--manifest-only", action="store_true")
    args = parser.parse_args()

    if args.manifest_only or not args.logs:
        print_manifest()
        return 0
    return validate(_collect_logs(args.logs))


if __name__ == "__main__":
    raise SystemExit(main())
