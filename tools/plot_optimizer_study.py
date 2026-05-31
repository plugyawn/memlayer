#!/usr/bin/env python3
"""Generate compact optimizer-study tables and SVG plots from paired run logs."""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass
from pathlib import Path


CASE_START_RE = re.compile(r"^===== NEWTONV_CASE_START\s+(\S+)")
OUTER_CASE_START_RE = re.compile(r"^===== SOFTPOLAR_PR291_CASE_START\s+(\S+)")
VAL_RE = re.compile(r"step:(?P<step>\d+)/(?P<total>\d+) val_loss:(?P<loss>[0-9.]+)")
PRECOND_RE = re.compile(r"loco_full_precond step=(?P<step>\d+) (?P<body>.*)$")
STAT_RE = re.compile(
    r"(?P<name>[a-zA-Z0-9_]+):n=(?P<n>\d+) layers=(?P<layers>[^ ]+) "
    r"blend=(?P<blend>[0-9.eE+-]+).*? "
    r"delta=(?P<delta>[0-9.eE+-]+)/[0-9.eE+-]+/[0-9.eE+-]+ "
    r"cos=(?P<cos>[0-9.eE+-]+)/[0-9.eE+-]+/[0-9.eE+-]+"
)


@dataclass
class Group:
    name: str
    cases: dict[str, list[tuple[int, float]]]


@dataclass
class Perturbation:
    group: str
    case: str
    step: int
    name: str
    layers: str
    blend: float
    delta: float
    cos: float


def parse_logs(paths: list[Path]) -> tuple[dict[str, Group], list[Perturbation]]:
    groups: dict[str, Group] = {}
    perturbations: list[Perturbation] = []
    for path in paths:
        group_name = path.stem
        case_name: str | None = None
        for line in path.read_text(errors="replace").splitlines():
            if line.lstrip().startswith('"tail":'):
                continue
            if m := OUTER_CASE_START_RE.match(line):
                group_name = m.group(1)
                case_name = None
                groups.setdefault(group_name, Group(group_name, {}))
                continue
            if m := CASE_START_RE.match(line):
                case_name = m.group(1)
                groups.setdefault(group_name, Group(group_name, {})).cases.setdefault(case_name, [])
                continue
            if case_name and (m := VAL_RE.search(line)):
                groups.setdefault(group_name, Group(group_name, {})).cases.setdefault(case_name, []).append(
                    (int(m.group("step")), float(m.group("loss")))
                )
            if m := PRECOND_RE.search(line):
                step = int(m.group("step"))
                for chunk in m.group("body").split(" | "):
                    if sm := STAT_RE.search(chunk):
                        perturbations.append(
                            Perturbation(
                                group=group_name,
                                case=case_name or "",
                                step=step,
                                name=sm.group("name"),
                                layers=sm.group("layers"),
                                blend=float(sm.group("blend")),
                                delta=float(sm.group("delta")),
                                cos=float(sm.group("cos")),
                            )
                        )
    return groups, perturbations


def deltas(group: Group) -> list[tuple[int, float, float, float | None, float | None]]:
    active = dict(group.cases.get("paired_active", []))
    noop1 = dict(group.cases.get("paired_noop", []))
    noop2 = dict(group.cases.get("paired_noop2", []))
    rows = []
    for step in sorted(active):
        noops = [x for x in (noop1.get(step), noop2.get(step)) if x is not None]
        if not noops:
            continue
        mean = sum(noops) / len(noops)
        rows.append((step, active[step], mean, active[step] - mean, min(noops) if len(noops) == 2 else None))
    return rows


def write_markdown(groups: dict[str, Group], perturbations: list[Perturbation], output: Path) -> None:
    lines = ["# Optimizer Study Summary", ""]
    lines += ["## Paired Validation Deltas", ""]
    lines += ["| group | step | active | noop_mean | delta | active_vs_best_noop |", "| --- | ---: | ---: | ---: | ---: | ---: |"]
    for group in groups.values():
        for step, active, mean, delta, best_noop in deltas(group):
            best_delta = active - best_noop if best_noop is not None else None
            lines.append(
                f"| {group.name} | {step} | {active:.4f} | {mean:.4f} | {delta:+.4f} | "
                f"{'' if best_delta is None else f'{best_delta:+.4f}'} |"
            )
    if perturbations:
        lines += ["", "## Update Perturbations", ""]
        lines += ["| group | case | step | surface | layers | blend | delta | cos |", "| --- | --- | ---: | --- | --- | ---: | ---: | ---: |"]
        for p in perturbations:
            if p.case and p.case != "paired_active":
                continue
            lines.append(
                f"| {p.group} | {p.case or 'warmup'} | {p.step} | {p.name} | {p.layers} | "
                f"{p.blend:.4f} | {p.delta:.4f} | {p.cos:.4f} |"
            )
    output.write_text("\n".join(lines) + "\n")


def sx(step: int, max_step: int, left: float, width: float) -> float:
    return left + width * step / max(max_step, 1)


def sy(value: float, v_min: float, v_max: float, top: float, height: float) -> float:
    span = max(v_max - v_min, 1e-9)
    return top + height * (v_max - value) / span


def render_svg(groups: dict[str, Group], perturbations: list[Perturbation], title: str) -> str:
    width, height = 920, 700
    left, right, top, plot_h = 72, 24, 58, 260
    plot_w = width - left - right
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="24" y="30" font-family="monospace" font-size="17" fill="#111827">{html.escape(title)}</text>',
    ]

    delta_rows = [(g.name, row) for g in groups.values() for row in deltas(g)]
    if delta_rows:
        max_step = max(row[0] for _, row in delta_rows)
        y_min = min(row[3] for _, row in delta_rows)
        y_max = max(row[3] for _, row in delta_rows)
        pad = max((y_max - y_min) * 0.15, 0.001)
        y_min -= pad
        y_max += pad
        parts.append(f'<text x="24" y="{top - 14}" font-family="monospace" font-size="13" fill="#111827">active validation loss minus noop mean; lower is better</text>')
        parts.append(f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#f9fafb" stroke="#d1d5db"/>')
        zero_y = sy(0.0, y_min, y_max, top, plot_h)
        parts.append(f'<line x1="{left}" y1="{zero_y:.1f}" x2="{left + plot_w}" y2="{zero_y:.1f}" stroke="#111827" stroke-dasharray="4 4"/>')
        for tick in range(5):
            frac = tick / 4
            y = top + plot_h * frac
            val = y_max - (y_max - y_min) * frac
            parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')
            parts.append(f'<text x="10" y="{y + 4:.1f}" font-family="monospace" font-size="11" fill="#4b5563">{val:+.4f}</text>')
        palette = ["#dc2626", "#2563eb", "#059669", "#7c3aed", "#d97706", "#0891b2"]
        for idx, group in enumerate(groups.values()):
            rows = deltas(group)
            if not rows:
                continue
            color = palette[idx % len(palette)]
            points = " ".join(
                f"{sx(step, max_step, left, plot_w):.1f},{sy(delta, y_min, y_max, top, plot_h):.1f}"
                for step, _, _, delta, _ in rows
            )
            parts.append(f'<polyline points="{points}" fill="none" stroke="{color}" stroke-width="2.4"/>')
            for step, _, _, delta, _ in rows:
                x = sx(step, max_step, left, plot_w)
                y = sy(delta, y_min, y_max, top, plot_h)
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{color}"/>')
            lx, ly = left + 10, top + 16 + idx * 18
            parts.append(f'<rect x="{lx}" y="{ly - 9}" width="10" height="10" fill="{color}"/>')
            parts.append(f'<text x="{lx + 16}" y="{ly}" font-family="monospace" font-size="11" fill="#111827">{html.escape(group.name)}</text>')
        for step in sorted({row[0] for _, row in delta_rows}):
            x = sx(step, max_step, left, plot_w)
            parts.append(f'<text x="{x - 10:.1f}" y="{top + plot_h + 20}" font-family="monospace" font-size="11" fill="#4b5563">{step}</text>')

    active_pert = [p for p in perturbations if not p.case or p.case == "paired_active"]
    y0 = top + plot_h + 78
    if active_pert:
        latest_by_surface: dict[tuple[str, str], Perturbation] = {}
        for p in active_pert:
            key = (p.group, p.name)
            if key not in latest_by_surface or p.step > latest_by_surface[key].step:
                latest_by_surface[key] = p
        rows = list(latest_by_surface.values())
        max_delta = max(p.delta for p in rows)
        bar_w = (width - 140) / max(len(rows), 1)
        parts.append(f'<text x="24" y="{y0 - 18}" font-family="monospace" font-size="13" fill="#111827">latest logged update perturbation: norm-relative delta and cosine to hard Muon update</text>')
        for idx, p in enumerate(rows):
            x = 70 + idx * bar_w
            h = 150 * p.delta / max(max_delta, 1e-9)
            color = "#dc2626" if "pr291" in p.group else "#2563eb"
            parts.append(f'<rect x="{x:.1f}" y="{y0 + 150 - h:.1f}" width="{max(bar_w - 10, 10):.1f}" height="{h:.1f}" fill="{color}" opacity="0.78"/>')
            parts.append(f'<text transform="translate({x + 4:.1f},{y0 + 168:.1f}) rotate(45)" font-family="monospace" font-size="10" fill="#111827">{html.escape(p.name)}</text>')
            parts.append(f'<text x="{x:.1f}" y="{y0 + 150 - h - 4:.1f}" font-family="monospace" font-size="10" fill="#111827">{p.delta:.3f}</text>')
            parts.append(f'<text x="{x:.1f}" y="{y0 + 188:.1f}" font-family="monospace" font-size="10" fill="#4b5563">cos {p.cos:.3f}</text>')
        parts.append(f'<line x1="60" y1="{y0 + 150}" x2="{width - 24}" y2="{y0 + 150}" stroke="#d1d5db"/>')

    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--summary", type=Path, required=True)
    parser.add_argument("--svg", type=Path, required=True)
    parser.add_argument("--title", default="NanoGPT optimizer study")
    args = parser.parse_args()

    groups, perturbations = parse_logs(args.logs)
    args.summary.parent.mkdir(parents=True, exist_ok=True)
    write_markdown(groups, perturbations, args.summary)
    args.svg.write_text(render_svg(groups, perturbations, args.title))


if __name__ == "__main__":
    main()
