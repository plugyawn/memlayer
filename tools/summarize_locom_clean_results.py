#!/usr/bin/env python3
"""Summarize clean LocoProp-M matrix result artifacts.

Accepts files produced by tools/modal_locom_clean_runner.py, either as raw
JSON/JSONL or as the JSON wrapper emitted by the `show_result` entrypoint.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable


TARGET_GATES = (125, 250, 375, 500)


def _iter_rows_from_object(obj: Any) -> Iterable[dict[str, Any]]:
    if isinstance(obj, dict) and isinstance(obj.get("text"), str):
        yield from _iter_rows_from_text(obj["text"])
    elif isinstance(obj, dict) and isinstance(obj.get("runs"), list):
        for row in obj["runs"]:
            if isinstance(row, dict):
                yield row
    elif isinstance(obj, dict) and "id" in obj:
        yield obj


def _iter_rows_from_text(text: str) -> Iterable[dict[str, Any]]:
    stripped = text.strip()
    if not stripped:
        return
    try:
        yield from _iter_rows_from_object(json.loads(stripped))
        return
    except json.JSONDecodeError:
        pass
    for line in stripped.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            yield from _iter_rows_from_object(json.loads(line))
        except json.JSONDecodeError:
            continue


def iter_rows(paths: list[str]) -> Iterable[dict[str, Any]]:
    for path in paths:
        text = sys.stdin.read() if path == "-" else Path(path).read_text(errors="replace")
        yield from _iter_rows_from_text(text)


def _fmt(value: Any, digits: int = 5) -> str:
    if value is None or value == "":
        return ""
    if isinstance(value, float):
        return f"{value:.{digits}g}"
    return str(value)


def _fmt_loss(value: Any) -> str:
    return "" if value is None or value == "" else f"{float(value):.5f}"


def _gate_losses(row: dict[str, Any]) -> dict[int, float]:
    losses = {}
    for gate in row.get("gates") or []:
        if not isinstance(gate, dict):
            continue
        step = gate.get("step")
        loss = gate.get("val_loss")
        if isinstance(step, int) and isinstance(loss, (int, float)):
            losses[step] = float(loss)
    return losses


def _latest_summary(row: dict[str, Any], kind: str) -> tuple[int | None, dict[str, Any]]:
    diagnostics = row.get("locoprop_diagnostics") or {}
    entries = diagnostics.get(kind) or []
    if not entries:
        return None, {}
    last = entries[-1]
    if not isinstance(last, dict):
        return None, {}
    step = last.get("step")
    summary = last.get("summary") if isinstance(last.get("summary"), dict) else {}
    return step if isinstance(step, int) else None, summary


def row_to_summary(row: dict[str, Any]) -> dict[str, Any]:
    gates = _gate_losses(row)
    prep_step, prep = _latest_summary(row, "prepare")
    apply_step, apply = _latest_summary(row, "apply")
    final = row.get("final") if isinstance(row.get("final"), dict) else {}
    return {
        "id": row.get("id", ""),
        "returncode": row.get("returncode", ""),
        "final_step": final.get("step", ""),
        "final_val": final.get("val_loss", ""),
        "step_avg_ms": final.get("step_avg_ms", ""),
        **{f"val_{step}": gates.get(step) for step in TARGET_GATES},
        "diag_step": prep_step if prep_step == apply_step else f"{prep_step}/{apply_step}",
        "accepted": prep.get("accepted", ""),
        "layers": prep.get("layers", ""),
        "negative_cos": prep.get("negative_cos", ""),
        "mean_cos_desc": prep.get("mean_cos_desc", ""),
        "loss_decreased": prep.get("loss_decreased", ""),
        "max_loss_ratio": prep.get("max_loss_ratio", ""),
        "max_corr_norm": prep.get("max_corr_norm", ""),
        "mean_scale": apply.get("mean_scale", ""),
        "max_corr_to_base": apply.get("max_corr_to_base", ""),
    }


def print_markdown(rows: list[dict[str, Any]]) -> None:
    columns = [
        "id",
        "final",
        "125",
        "250",
        "375",
        "500",
        "ms",
        "diag",
        "acc",
        "negcos",
        "mean_cos",
        "loss_dec",
        "max_loss_ratio",
        "max_corr/base",
    ]
    print("| " + " | ".join(columns) + " |")
    print("| " + " | ".join("---" for _ in columns) + " |")
    for row in rows:
        vals = [
            _fmt(row["id"]),
            _fmt_loss(row["final_val"]),
            _fmt_loss(row["val_125"]),
            _fmt_loss(row["val_250"]),
            _fmt_loss(row["val_375"]),
            _fmt_loss(row["val_500"]),
            _fmt(row["step_avg_ms"], 2),
            _fmt(row["diag_step"]),
            f"{_fmt(row['accepted'])}/{_fmt(row['layers'])}" if row["layers"] != "" else "",
            _fmt(row["negative_cos"]),
            _fmt(row["mean_cos_desc"], 4),
            _fmt(row["loss_decreased"]),
            _fmt(row["max_loss_ratio"], 3),
            _fmt(row["max_corr_to_base"], 3),
        ]
        print("| " + " | ".join(vals) + " |")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("paths", nargs="+", help="JSON/JSONL result paths, or '-' for stdin")
    parser.add_argument("--json", action="store_true", help="emit normalized JSON summaries")
    args = parser.parse_args()

    rows = [row_to_summary(row) for row in iter_rows(args.paths)]
    if args.json:
        print(json.dumps(rows, indent=2, sort_keys=True))
    else:
        print_markdown(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
