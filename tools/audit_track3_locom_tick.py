#!/usr/bin/env python3
"""Audit whether the Track 3 LocoProp-M mechanism question is actually closed.

This script is intentionally conservative. It treats the existing K-depth and
suffix reports as useful evidence, but it will not claim "what makes LocoProp
tick" is settled until the two critical controls land:

* prefix specificity at step 2000, and
* static layer subset at step 2000.

The post-2000 suffix slope gate is reported separately because it is a WR-path
conversion question: it asks whether the discovered mechanism can preserve the
healthy 1900->2000 descent after step 2000.
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path


PASS = "PASS"
FAIL = "FAIL"
MISSING = "MISSING"
PARTIAL = "PARTIAL"


@dataclass(frozen=True)
class Gate:
    name: str
    status: str
    evidence: Path | None
    read: str


def _read(path: Path | None) -> str:
    if path is None or not path.exists():
        return ""
    return path.read_text(errors="replace")


def _find_latest(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern), key=lambda path: path.stat().st_mtime)
    return matches[-1] if matches else None


def _path_arg(value: str | None, fallback: Path | None) -> Path | None:
    if value:
        return Path(value)
    return fallback


def _gate_existing_kdepth(path: Path | None) -> Gate:
    text = _read(path)
    if not text:
        return Gate("K-depth", MISSING, path, "K=5/K8/K10 mechanism report not found.")
    has_k_ladder = all(token in text for token in ("k5-lr", "k8-lr", "k10-lr"))
    has_synthesis = "missing ingredient is not more local iterations" in text
    if "K=5 is externally sufficient" in text or (has_k_ladder and has_synthesis):
        return Gate(
            "K-depth",
            PASS,
            path,
            "K=5 is enough externally; more local steps are not the missing ingredient.",
        )
    return Gate("K-depth", PARTIAL, path, "K-depth report exists but did not contain the expected K=5 conclusion.")


def _gate_suffix(path: Path | None) -> Gate:
    text = _read(path)
    if not text:
        return Gate("post-2000 suffix slope", MISSING, path, "No suffix slope decision found.")
    if "Slope read: at least one lane preserves" in text:
        return Gate(
            "post-2000 suffix slope",
            PASS,
            path,
            "At least one suffix lane preserved the 1900->2000 slope target.",
        )
    if "Slope read: no lane preserves" in text or "Best slope preservation: 0.80x" in text:
        return Gate(
            "post-2000 suffix slope",
            FAIL,
            path,
            "Existing suffix lanes are slope-starved after 2000.",
        )
    return Gate("post-2000 suffix slope", PARTIAL, path, "Suffix decision exists but preservation status is ambiguous.")


def _gate_prefix(path: Path | None) -> Gate:
    text = _read(path)
    if not text:
        return Gate(
            "prefix specificity",
            MISSING,
            path,
            "Need active K5 vs no-Loco vs random vs orthogonal through decision step 2000.",
        )
    if "@ 2000" not in text and "2000" not in text:
        return Gate(
            "prefix specificity",
            PARTIAL,
            path,
            "Decision exists but does not appear to score the required step-2000 carry window.",
        )
    if "c_fc true-post direction matters in the prefix" in text:
        return Gate(
            "prefix specificity",
            PASS,
            path,
            "Active true-post c_fc LocoProp beat no-Loco and perturbation controls at the carry decision.",
        )
    if "not clearly local-direction-specific" in text:
        return Gate(
            "prefix specificity",
            FAIL,
            path,
            "Perturbation/orthogonal control matched active; current prefix gain is not LocoProp-direction-specific.",
        )
    if "probably schedule/checkpoint state" in text or "not LocoProp-specific" in text:
        return Gate(
            "prefix specificity",
            FAIL,
            path,
            "No active direction-specific prefix signal was found.",
        )
    if "active K5 did not reproduce" in text:
        return Gate(
            "prefix specificity",
            FAIL,
            path,
            "Active K5 did not reproduce the known prefix; rerun/fix before interpreting controls.",
        )
    return Gate("prefix specificity", PARTIAL, path, "Prefix decision exists but the read is ambiguous.")


def _gate_layer_subset(path: Path | None) -> Gate:
    text = _read(path)
    if not text:
        return Gate(
            "static layer subset",
            MISSING,
            path,
            "Need all-layer vs 7-10 vs 6-10 vs no-Loco through decision step 2000.",
        )
    if "@ 2000" not in text and "2000" not in text:
        return Gate(
            "static layer subset",
            PARTIAL,
            path,
            "Decision exists but does not appear to score the required step-2000 carry window.",
        )
    if "match all-layer active" in text or "beat all-layer active" in text:
        return Gate(
            "static layer subset",
            PASS,
            path,
            "A static c_fc subset matched or beat all-layer active at the carry decision.",
        )
    if "no subset matches all-layer active" in text:
        return Gate(
            "static layer subset",
            FAIL,
            path,
            "No static subset matched all-layer; moving-gate/distributed state formation remains implicated.",
        )
    if "all-layer active did not reproduce" in text:
        return Gate(
            "static layer subset",
            FAIL,
            path,
            "All-layer active did not reproduce the known prefix; subset interpretation is invalid.",
        )
    return Gate("static layer subset", PARTIAL, path, "Layer-subset decision exists but the read is ambiguous.")


def _fmt_path(path: Path | None) -> str:
    return "none" if path is None else str(path)


def print_report(gates: list[Gate], *, require_suffix: bool) -> int:
    print("# Track 3 LocoProp-M Tick Completion Audit")
    print()
    print("| gate | status | evidence | read |")
    print("| --- | --- | --- | --- |")
    for gate in gates:
        print(f"| {gate.name} | {gate.status} | `{_fmt_path(gate.evidence)}` | {gate.read} |")
    print()

    critical = {
        "K-depth",
        "prefix specificity",
        "static layer subset",
    }
    if require_suffix:
        critical.add("post-2000 suffix slope")

    missing_or_bad = [
        gate
        for gate in gates
        if gate.name in critical and gate.status != PASS
    ]

    if missing_or_bad:
        print("## Completion")
        print()
        print("NOT COMPLETE")
        print()
        print("Blocking gates:")
        print()
        for gate in missing_or_bad:
            print(f"- {gate.name}: {gate.status} - {gate.read}")
        return 1

    print("## Completion")
    print()
    if require_suffix:
        print("COMPLETE for mechanism plus suffix-slope conversion gates.")
    else:
        print("COMPLETE for the current mechanism question. Suffix-slope conversion remains separately reportable.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(".opencode"))
    parser.add_argument("--kdepth")
    parser.add_argument("--suffix")
    parser.add_argument("--prefix")
    parser.add_argument("--layer-subset")
    parser.add_argument(
        "--require-suffix",
        action="store_true",
        help="Require the post-2000 suffix preservation gate for completion.",
    )
    args = parser.parse_args()

    root = args.root
    kdepth = _path_arg(args.kdepth, root / "track3_locom_mechanism_kdepth_20260607.md")
    suffix = _path_arg(args.suffix, root / "track3_locom_2000_suffix_slope_decision_20260607.md")
    prefix = _path_arg(args.prefix, _find_latest(root, "**/track3_prefix_specificity_decision.md"))
    layer_subset = _path_arg(args.layer_subset, _find_latest(root, "**/track3_layer_subset_decision.md"))

    gates = [
        _gate_existing_kdepth(kdepth),
        _gate_prefix(prefix),
        _gate_layer_subset(layer_subset),
        _gate_suffix(suffix),
    ]
    return print_report(gates, require_suffix=args.require_suffix)


if __name__ == "__main__":
    raise SystemExit(main())
