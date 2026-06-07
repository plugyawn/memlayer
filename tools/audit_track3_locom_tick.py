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
SKIPPED = "SKIPPED"


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


def _first_existing(*paths: Path | None) -> Path | None:
    for path in paths:
        if path is not None and path.exists():
            return path
    return None


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
    if (
        "active and alpha-zero curves are indistinguishable" in text
        or "applied LocoProp correction did not measurably move validation" in text
        or "natural K5 c_fc LocoProp correction did not cause it" in text
    ):
        return Gate(
            "prefix specificity",
            FAIL,
            path,
            "Alpha-zero matched active K5 through the carry window; natural c_fc LocoProp did not cause the prefix.",
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


def _gate_layer_subset(path: Path | None, *, prefix_gate: Gate | None = None) -> Gate:
    if prefix_gate is not None and prefix_gate.status == FAIL:
        return Gate(
            "static layer subset",
            SKIPPED,
            path,
            "Skipped until a nonzero LocoProp correction beats alpha-zero; subset tests cannot rescue a failed all-layer prefix-specificity gate.",
        )
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


def _closed_negative(gates: list[Gate], *, require_suffix: bool) -> bool:
    if require_suffix:
        return False
    by_name = {gate.name: gate for gate in gates}
    return (
        by_name.get("K-depth") is not None
        and by_name["K-depth"].status == PASS
        and by_name.get("prefix specificity") is not None
        and by_name["prefix specificity"].status == FAIL
        and by_name.get("static layer subset") is not None
        and by_name["static layer subset"].status == SKIPPED
    )


def print_report(gates: list[Gate], *, require_suffix: bool, allow_negative: bool) -> int:
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
        if gate.name in critical and gate.status not in {PASS, SKIPPED}
    ]

    if allow_negative and _closed_negative(gates, require_suffix=require_suffix):
        print("## Completion")
        print()
        print("CLOSED NEGATIVE for the current c_fc K5-10 mechanism.")
        print()
        print(
            "This is not a positive LocoProp recipe. It proves the current natural "
            "true-post c_fc additive path is not the causal mechanism, so future "
            "work must change surface, target, integration, or optimizer state."
        )
        return 0

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
    parser.add_argument(
        "--allow-negative",
        action="store_true",
        help="Exit 0 when the current c_fc mechanism is conclusively closed negative.",
    )
    args = parser.parse_args()

    root = args.root
    kdepth = _path_arg(args.kdepth, root / "track3_locom_mechanism_kdepth_20260607.md")
    suffix = _path_arg(args.suffix, root / "track3_locom_2000_suffix_slope_decision_20260607.md")
    prefix = _path_arg(
        args.prefix,
        _first_existing(
            _find_latest(root, "**/track3_prefix_specificity_decision.md"),
            root / "track3_locom_prefix_effect_size_20260607.md",
            root / "track3_locom_tick_decision_20260607.md",
        ),
    )
    layer_subset = _path_arg(args.layer_subset, _find_latest(root, "**/track3_layer_subset_decision.md"))

    kdepth_gate = _gate_existing_kdepth(kdepth)
    prefix_gate = _gate_prefix(prefix)
    gates = [
        kdepth_gate,
        prefix_gate,
        _gate_layer_subset(layer_subset, prefix_gate=prefix_gate),
        _gate_suffix(suffix),
    ]
    return print_report(gates, require_suffix=args.require_suffix, allow_negative=args.allow_negative)


if __name__ == "__main__":
    raise SystemExit(main())
