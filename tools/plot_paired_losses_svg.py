#!/usr/bin/env python3
import argparse
import html
import re
from pathlib import Path


OUTER_CASE_START_RE = re.compile(r"^===== SOFTPOLAR_PR291_CASE_START\s+(\S+)")
CASE_START_RE = re.compile(r"^===== NEWTONV_CASE_START\s+(\S+)")
STEP_RE = re.compile(r"step:(?P<step>\d+)/(?P<total>\d+) val_loss:(?P<val_loss>[0-9.]+)")

COLORS = {
    "paired_noop": "#6b7280",
    "paired_active": "#dc2626",
    "paired_noop2": "#2563eb",
}


def parse(paths: list[Path]) -> dict[str, dict[str, list[tuple[int, float]]]]:
    groups: dict[str, dict[str, list[tuple[int, float]]]] = {}
    for path in paths:
        group = path.stem
        case = None
        for line in path.read_text(errors="replace").splitlines():
            if line.lstrip().startswith('"tail":'):
                continue
            if m := OUTER_CASE_START_RE.match(line):
                group = m.group(1)
                case = None
                continue
            if m := CASE_START_RE.match(line):
                case = m.group(1)
                groups.setdefault(group, {}).setdefault(case, [])
                continue
            if case and (m := STEP_RE.search(line)):
                groups[group][case].append((int(m.group("step")), float(m.group("val_loss"))))
    return groups


def sx(step: int, max_step: int, left: float, width: float) -> float:
    return left + width * step / max(max_step, 1)


def sy(loss: float, y_min: float, y_max: float, top: float, height: float) -> float:
    span = max(y_max - y_min, 1e-9)
    return top + height * (y_max - loss) / span


def polyline(points: list[tuple[float, float]]) -> str:
    return " ".join(f"{x:.1f},{y:.1f}" for x, y in points)


def render(groups: dict[str, dict[str, list[tuple[int, float]]]], title: str) -> str:
    panel_w, panel_h = 760, 280
    margin_l, margin_r, margin_t, margin_b = 60, 20, 44, 44
    plot_w = panel_w - margin_l - margin_r
    plot_h = panel_h - margin_t - margin_b
    svg_h = 42 + panel_h * max(len(groups), 1)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{panel_w}" height="{svg_h}" viewBox="0 0 {panel_w} {svg_h}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="20" y="26" font-family="monospace" font-size="16" fill="#111827">{html.escape(title)}</text>',
    ]
    for panel_idx, (group, cases) in enumerate(groups.items()):
        y0 = 42 + panel_idx * panel_h
        all_points = [p for points in cases.values() for p in points]
        if not all_points:
            continue
        max_step = max(step for step, _ in all_points)
        y_min = min(loss for _, loss in all_points)
        y_max = max(loss for _, loss in all_points)
        pad = max((y_max - y_min) * 0.08, 1e-4)
        y_min -= pad
        y_max += pad

        left, top = margin_l, y0 + margin_t
        parts.append(f'<text x="20" y="{y0 + 24}" font-family="monospace" font-size="14" fill="#111827">{html.escape(group)}</text>')
        parts.append(f'<rect x="{left}" y="{top}" width="{plot_w}" height="{plot_h}" fill="#f9fafb" stroke="#d1d5db"/>')
        for tick in range(5):
            frac = tick / 4
            y = top + plot_h * frac
            value = y_max - (y_max - y_min) * frac
            parts.append(f'<line x1="{left}" y1="{y:.1f}" x2="{left + plot_w}" y2="{y:.1f}" stroke="#e5e7eb"/>')
            parts.append(f'<text x="8" y="{y + 4:.1f}" font-family="monospace" font-size="11" fill="#4b5563">{value:.4f}</text>')
        for step in sorted({step for step, _ in all_points}):
            x = sx(step, max_step, left, plot_w)
            parts.append(f'<line x1="{x:.1f}" y1="{top + plot_h}" x2="{x:.1f}" y2="{top + plot_h + 4}" stroke="#9ca3af"/>')
            parts.append(f'<text x="{x - 8:.1f}" y="{top + plot_h + 20}" font-family="monospace" font-size="11" fill="#4b5563">{step}</text>')
        legend_x = left + 8
        for case in sorted(cases):
            points = cases[case]
            if not points:
                continue
            color = COLORS.get(case, "#111827")
            xy = [(sx(step, max_step, left, plot_w), sy(loss, y_min, y_max, top, plot_h)) for step, loss in points]
            parts.append(f'<polyline points="{polyline(xy)}" fill="none" stroke="{color}" stroke-width="2.2"/>')
            for x, y in xy:
                parts.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="{color}"/>')
            parts.append(f'<rect x="{legend_x}" y="{top + 8}" width="10" height="10" fill="{color}"/>')
            parts.append(f'<text x="{legend_x + 16}" y="{top + 17}" font-family="monospace" font-size="11" fill="#111827">{html.escape(case)}</text>')
            legend_x += 150
    parts.append("</svg>")
    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("logs", nargs="+", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--title", default="paired validation loss")
    args = parser.parse_args()

    groups = parse(args.logs)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(groups, args.title))


if __name__ == "__main__":
    main()
