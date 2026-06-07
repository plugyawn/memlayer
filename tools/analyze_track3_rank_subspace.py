#!/usr/bin/env python3
"""Analyze Track 3 checkpoint rank and update subspace drift.

This intentionally works from saved checkpoints only. It does not need to
rebuild a dataloader or run training, so it is suitable for late-stage suffix
diagnostics on a live GPU pod.
"""

from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import torch


@dataclass(frozen=True)
class CheckpointSpec:
    label: str
    path: Path


def parse_checkpoint_spec(text: str) -> CheckpointSpec:
    if "=" in text:
        label, path = text.split("=", 1)
        return CheckpointSpec(label=label.strip(), path=Path(path.strip()))
    path = Path(text)
    return CheckpointSpec(label=path.stem, path=path)


def surface_for_name(name: str) -> str:
    if ".mlp.fc.weight" in name:
        return "mlp_fc"
    if ".mlp.proj.weight" in name:
        return "mlp_proj"
    if ".attn.q.weight" in name:
        return "attn_q"
    if ".attn.k.weight" in name:
        return "attn_k"
    if ".attn.v.weight" in name:
        return "attn_v"
    if ".attn.proj.weight" in name:
        return "attn_o"
    if name == "embed.weight":
        return "embed"
    if name == "proj.weight":
        return "lm_head"
    return "other"


def block_matrix_names(model: dict[str, torch.Tensor]) -> list[str]:
    return [
        name
        for name, tensor in model.items()
        if name.startswith("blocks.")
        and name.endswith(".weight")
        and hasattr(tensor, "ndim")
        and tensor.ndim == 2
    ]


def assumed_muon_names(model: dict[str, torch.Tensor]) -> list[str]:
    """Return the Muon state order seen in the saved LocoProp-M checkpoints.

    PyTorch optimizer state dicts do not preserve parameter names. In these
    generated Track 3 checkpoints, the Muon state appears bucketed as
    mlp.fc, mlp.proj, then attention matrices. Keep this explicit so reports
    do not silently depend on an implicit dict order.
    """

    names: list[str] = []
    for suffix in (".mlp.fc.weight", ".mlp.proj.weight"):
        names.extend(name for name in model if name.startswith("blocks.") and name.endswith(suffix))
    for suffix in (
        ".attn.q.weight",
        ".attn.k.weight",
        ".attn.v.weight",
        ".attn.proj.weight",
    ):
        names.extend(name for name in model if name.startswith("blocks.") and name.endswith(suffix))
    return names


def load_checkpoint(path: Path, device: torch.device) -> dict:
    checkpoint = torch.load(path, map_location="cpu", weights_only=False)
    if "model" not in checkpoint:
        raise ValueError(f"{path} has no model key")
    return checkpoint


def svdvals(matrix: torch.Tensor, device: torch.device) -> torch.Tensor:
    x = matrix.detach().to(device=device, dtype=torch.float32)
    return torch.linalg.svdvals(x).detach().cpu()


def svd_basis(matrix: torch.Tensor, k: int, device: torch.device) -> tuple[torch.Tensor, torch.Tensor]:
    x = matrix.detach().to(device=device, dtype=torch.float32)
    u, _s, vh = torch.linalg.svd(x, full_matrices=False)
    kk = min(k, u.shape[1], vh.shape[0])
    return u[:, :kk].contiguous(), vh[:kk, :].T.contiguous()


def spectrum_metrics(s: torch.Tensor) -> dict[str, float]:
    if s.numel() == 0:
        return {}
    e = s.square()
    total = float(e.sum().item())
    smax2 = float(e.max().item())
    if total <= 0.0 or smax2 <= 0.0:
        return {
            "fro": 0.0,
            "op": 0.0,
            "stable_rank": 0.0,
            "rank90": 0.0,
            "rank95": 0.0,
            "rank99": 0.0,
            "top1_energy": 0.0,
            "top8_energy": 0.0,
            "top32_energy": 0.0,
            "top64_energy": 0.0,
        }
    cs = torch.cumsum(e, dim=0)

    def rank_at(frac: float) -> int:
        return int(torch.searchsorted(cs, torch.tensor(total * frac), right=False).item()) + 1

    def top_frac(k: int) -> float:
        return float(e[: min(k, e.numel())].sum().item() / total)

    return {
        "fro": math.sqrt(total),
        "op": float(s[0].item()),
        "stable_rank": total / smax2,
        "rank90": float(rank_at(0.90)),
        "rank95": float(rank_at(0.95)),
        "rank99": float(rank_at(0.99)),
        "top1_energy": top_frac(1),
        "top8_energy": top_frac(8),
        "top32_energy": top_frac(32),
        "top64_energy": top_frac(64),
    }


def delta_outside_metrics(
    before: torch.Tensor,
    after: torch.Tensor,
    basis_source: torch.Tensor,
    k: int,
    device: torch.device,
) -> dict[str, float]:
    delta = after.detach().to(device=device, dtype=torch.float32) - before.detach().to(
        device=device, dtype=torch.float32
    )
    denom = delta.norm().clamp_min(1e-30)
    u, v = svd_basis(basis_source, k=k, device=device)
    left_resid = delta - u @ (u.T @ delta)
    right_resid = delta - (delta @ v) @ v.T
    both_proj = u @ (u.T @ delta @ v) @ v.T
    both_resid = delta - both_proj
    return {
        "delta_norm": float(denom.item()),
        "outside_left_frac": float((left_resid.norm() / denom).item()),
        "outside_right_frac": float((right_resid.norm() / denom).item()),
        "outside_both_frac": float((both_resid.norm() / denom).item()),
    }


def write_tsv(path: Path, rows: Iterable[dict[str, object]]) -> None:
    rows = list(rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict[str, object]], group_keys: tuple[str, ...], value_keys: tuple[str, ...]) -> list[dict[str, object]]:
    groups: dict[tuple[object, ...], list[dict[str, object]]] = defaultdict(list)
    for row in rows:
        groups[tuple(row[k] for k in group_keys)].append(row)
    out: list[dict[str, object]] = []
    for group, items in sorted(groups.items(), key=lambda kv: tuple(str(x) for x in kv[0])):
        summary = {key: value for key, value in zip(group_keys, group)}
        summary["n"] = len(items)
        for key in value_keys:
            vals = torch.tensor([float(item[key]) for item in items if key in item], dtype=torch.float64)
            if vals.numel() == 0:
                continue
            summary[f"{key}_mean"] = float(vals.mean().item())
            summary[f"{key}_median"] = float(vals.median().item())
        out.append(summary)
    return out


def analyze(args: argparse.Namespace) -> None:
    device = torch.device(args.device)
    specs = [parse_checkpoint_spec(item) for item in args.checkpoint]
    checkpoints = [(spec, load_checkpoint(spec.path, device)) for spec in specs]

    matrix_rows: list[dict[str, object]] = []
    momentum_rows: list[dict[str, object]] = []
    delta_rows: list[dict[str, object]] = []

    for spec, checkpoint in checkpoints:
        model = checkpoint["model"]
        for name in block_matrix_names(model):
            tensor = model[name]
            metrics = spectrum_metrics(svdvals(tensor, device=device))
            matrix_rows.append(
                {
                    "label": spec.label,
                    "step": checkpoint.get("step", ""),
                    "kind": "weight",
                    "name": name,
                    "surface": surface_for_name(name),
                    "shape": "x".join(map(str, tensor.shape)),
                    **metrics,
                }
            )

        if args.include_momentum:
            names = assumed_muon_names(model)
            state = checkpoint.get("optimizers", [{}, {}])[1].get("state", {})
            for idx, name in enumerate(names):
                item = state.get(idx)
                if not item or "momentum" not in item:
                    continue
                tensor = item["momentum"]
                if tuple(tensor.shape) != tuple(model[name].shape):
                    # Keep the row, but make the assumption failure explicit.
                    assumed_name = name
                    name = f"unmapped_state_{idx}"
                    surface = "unmapped"
                else:
                    assumed_name = ""
                    surface = surface_for_name(name)
                metrics = spectrum_metrics(svdvals(tensor, device=device))
                momentum_rows.append(
                    {
                        "label": spec.label,
                        "step": checkpoint.get("step", ""),
                        "kind": "muon_momentum",
                        "state_idx": idx,
                        "name": name,
                        "assumed_name_if_shape_mismatch": assumed_name,
                        "surface": surface,
                        "shape": "x".join(map(str, tensor.shape)),
                        **metrics,
                    }
                )

    for (before_spec, before_ckpt), (after_spec, after_ckpt) in zip(checkpoints, checkpoints[1:]):
        before_model = before_ckpt["model"]
        after_model = after_ckpt["model"]
        common = [name for name in block_matrix_names(before_model) if name in after_model]
        for name in common:
            before = before_model[name]
            after = after_model[name]
            metrics = spectrum_metrics(svdvals(after.float() - before.float(), device=device))
            row: dict[str, object] = {
                "from_label": before_spec.label,
                "to_label": after_spec.label,
                "from_step": before_ckpt.get("step", ""),
                "to_step": after_ckpt.get("step", ""),
                "name": name,
                "surface": surface_for_name(name),
                "shape": "x".join(map(str, before.shape)),
                **{f"delta_{k}": v for k, v in metrics.items()},
            }
            for k in args.subspace_k:
                outside_w = delta_outside_metrics(before, after, before, k=k, device=device)
                for metric_key, metric_value in outside_w.items():
                    row[f"w_top{k}_{metric_key}"] = metric_value
            delta_rows.append(row)

    write_tsv(args.out_dir / "matrix_spectrum.tsv", matrix_rows)
    write_tsv(args.out_dir / "momentum_spectrum.tsv", momentum_rows)
    write_tsv(args.out_dir / "delta_subspace.tsv", delta_rows)
    write_tsv(
        args.out_dir / "matrix_surface_summary.tsv",
        summarize(
            matrix_rows,
            ("label", "step", "surface"),
            ("fro", "op", "stable_rank", "rank90", "top1_energy", "top32_energy", "top64_energy"),
        ),
    )
    write_tsv(
        args.out_dir / "momentum_surface_summary.tsv",
        summarize(
            momentum_rows,
            ("label", "step", "surface"),
            ("fro", "op", "stable_rank", "rank90", "top1_energy", "top32_energy", "top64_energy"),
        ),
    )
    value_keys = ["delta_fro", "delta_stable_rank", "delta_top1_energy", "delta_top32_energy"]
    for k in args.subspace_k:
        value_keys.extend(
            [
                f"w_top{k}_outside_left_frac",
                f"w_top{k}_outside_right_frac",
                f"w_top{k}_outside_both_frac",
            ]
        )
    write_tsv(
        args.out_dir / "delta_surface_summary.tsv",
        summarize(delta_rows, ("from_label", "to_label", "from_step", "to_step", "surface"), tuple(value_keys)),
    )

    print(f"wrote {args.out_dir}")
    print(f"matrix rows: {len(matrix_rows)}")
    print(f"momentum rows: {len(momentum_rows)}")
    print(f"delta rows: {len(delta_rows)}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--checkpoint", action="append", required=True, help="label=/path/to/checkpoint.pt")
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--subspace-k", type=int, nargs="+", default=[16, 32, 64, 128])
    parser.add_argument("--include-momentum", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    analyze(args)


if __name__ == "__main__":
    main()
