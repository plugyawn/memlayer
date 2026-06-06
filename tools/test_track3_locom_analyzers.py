#!/usr/bin/env python3
"""Synthetic regression tests for Track 3 LocoProp mechanism analyzers."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOLS = ROOT / "tools"


def _header(*, enabled: bool, local_opt: str = "sgd", random: bool = False, mode: str = "normal", norm_target: float = 0.0, lr_bump: str = "") -> str:
    return (
        f"LocoM enabled={enabled} layers=all steps=5 sample_tokens=1024 "
        f"gather=True accum=False micro_sample_tokens=32 aux_capture=False "
        f"aux_seqs=16 batched_prep=False local_opt={local_opt} target_space=post "
        f"true_post_grad=True random_correction={random} correction_mode={mode} "
        f"diag_steps=1,2,4,5 lr_decay=False rms_beta1=0.999 rms_beta2=0.9 "
        f"rms_eps=1e-5 rms_reset_each_step=False require_loss_decrease=True "
        f"min_cos_desc=0.0 inner_lr=0.0002 target_gamma=1.0 prox=0.1 "
        f"alpha=1.0 norm_to_base=False norm_target={norm_target} norm_cap=0.20 "
        f"norm_cap_windows= active_windows=0:1800 start_step=0 end_step=1800 "
        f"interval=1 target_loss=3.28 seed_base=0 seed_offset=3710 "
        f"cooldown_frac=1.0 lr_schedule=power lr_power=2.0 "
        f"lr_schedule_steps=3000 lr_min_eta=0.0 lr_bump_windows={lr_bump} "
        f"lr_switch_step=-1 lr_after_switch= lr_after_switch_power=2.0 "
        f"lr_after_switch_steps=0 lr_blend_start=-1 lr_blend_end=-1 "
        f"lr_blend_target= lr_blend_target_power=2.0 lr_blend_target_steps=0 "
        f"soft_muon=False soft_blend=1.0 soft_start=-1 soft_end=-1 "
        f"soft_ceil=1.0 soft_norm_restore=True resume_checkpoint=/tmp/ckpt.pt "
        f"resume_load_optimizers=True\n"
    )


def _apply(step: int, eff_frac: float = 0.02) -> str:
    base = 1.0
    corr = 0.1
    scale = eff_frac * base / corr
    return (
        f"locoprop_m_apply step={step} shape=(3072, 768):"
        f"base_step={base:.3e},corr_norm={corr:.3e},cap=0.200,scale={scale:.3e}\n"
    )


def _kdiag(step: int, layer: int, *, k: int = 5, ratio: float = 0.90, corr_norm: float = 0.004, cos: float = 0.02) -> str:
    return (
        f"locoprop_m_kdiag step={step} l{layer} "
        f"k{k}:loss=1.000e-05,ratio={ratio:.3e},corr_norm={corr_norm:.3e},raw_cos={cos:.3f},cos={cos:.3f}\n"
    )


def _log(
    path: Path,
    *,
    vals: dict[int, float],
    enabled: bool,
    local_opt: str = "sgd",
    random: bool = False,
    mode: str = "normal",
    norm_target: float = 0.0,
    lr_bump: str = "",
    with_apply: bool = False,
) -> None:
    lines = [_header(enabled=enabled, local_opt=local_opt, random=random, mode=mode, norm_target=norm_target, lr_bump=lr_bump)]
    total = max(vals) if vals else 0
    for step, loss in sorted(vals.items()):
        lines.append(f"step:{step}/{total} val_loss:{loss:.5f} train_time:0.000s step_avg:nanms\n")
        if with_apply:
            lines.append(_apply(step, eff_frac=norm_target if norm_target > 0 else 0.01))
    path.write_text("".join(lines))


def _run(args: list[str]) -> str:
    proc = subprocess.run(
        [sys.executable, *args],
        cwd=ROOT,
        check=True,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return proc.stdout


def _assert_contains(text: str, needle: str) -> None:
    if needle not in text:
        raise AssertionError(f"expected output to contain {needle!r}\n--- output ---\n{text}")


def test_prefix_direction_specific(tmp: Path) -> None:
    _log(tmp / "track3_prefix_noloco_seed3710.log", vals={1600: 3.48, 1700: 3.42, 1800: 3.4000}, enabled=False)
    _log(tmp / "track3_prefix_active_k5_seed3710.log", vals={1600: 3.48, 1700: 3.418, 1800: 3.3965}, enabled=True, with_apply=True)
    _log(tmp / "track3_prefix_random_norm002_seed3710.log", vals={1600: 3.48, 1700: 3.419, 1800: 3.3990}, enabled=True, local_opt="random", random=True, norm_target=0.02, with_apply=True)
    _log(tmp / "track3_prefix_orthogonal_k5_norm002_seed3710.log", vals={1600: 3.48, 1700: 3.419, 1800: 3.3988}, enabled=True, mode="orthogonal", norm_target=0.02, with_apply=True)
    out = _run(["tools/analyze_track3_locom_prefix_probe.py", str(tmp), "--steps", "1600,1700,1800"])
    _assert_contains(out, "c_fc true-post direction matters in the prefix")


def test_prefix_perturbation_tie(tmp: Path) -> None:
    _log(tmp / "track3_prefix_noloco_seed3710.log", vals={1600: 3.48, 1800: 3.4000}, enabled=False)
    _log(tmp / "track3_prefix_active_k5_seed3710.log", vals={1600: 3.48, 1800: 3.3965}, enabled=True, with_apply=True)
    _log(tmp / "track3_prefix_random_norm002_seed3710.log", vals={1600: 3.48, 1800: 3.3963}, enabled=True, local_opt="random", random=True, norm_target=0.02, with_apply=True)
    out = _run(["tools/analyze_track3_locom_prefix_probe.py", str(tmp), "--steps", "1600,1800"])
    _assert_contains(out, "not clearly local-direction-specific")


def test_suffix_scheduler_only(tmp: Path) -> None:
    _log(tmp / "track3_locom_2000_control_seed3710.log", vals={2000: 3.3733, 2125: 3.3621}, enabled=False)
    _log(tmp / "track3_locom_2000_norm002_k5_seed3710.log", vals={2000: 3.3733, 2125: 3.3620}, enabled=True, norm_target=0.02, with_apply=True)
    _log(tmp / "track3_locom_2000_hold115_seed3710.log", vals={2000: 3.3733, 2125: 3.3598}, enabled=False, lr_bump="2000:2050:2250:2400:1.15")
    out = _run(["tools/analyze_track3_locom_suffix_probe.py", str(tmp), "--steps", "2000,2125"])
    _assert_contains(out, "mainly LR/velocity")


def test_suffix_insufficient_data(tmp: Path) -> None:
    _log(tmp / "track3_locom_2000_control_seed3710.log", vals={}, enabled=False)
    _log(tmp / "track3_locom_2000_norm002_k5_seed3710.log", vals={}, enabled=True, norm_target=0.02)
    out = _run(["tools/analyze_track3_locom_suffix_probe.py", str(tmp), "--steps", "2000,2125"])
    _assert_contains(out, "insufficient validation data")


def test_window_health_slope_break(tmp: Path) -> None:
    _log(
        tmp / "track3_survival_noloco_from_k5_1800_seed3710.log",
        vals={1800: 3.39867, 1900: 3.38474, 2000: 3.37334, 2100: 3.36420, 2125: 3.36213},
        enabled=False,
    )
    out = _run(
        [
            "tools/analyze_track3_locom_window_health.py",
            str(tmp),
            "--steps",
            "1800,1900,2000,2100,2125",
            "--start-step",
            "1800",
            "--target-step",
            "3000",
            "--target-loss",
            "3.28",
        ]
    )
    _assert_contains(out, "last healthy window `1900->2000`")
    _assert_contains(out, "first cold window `2100->2125`")


def test_mechanism_k5_read(tmp: Path) -> None:
    path = tmp / "track3_kdepth_k5-lr2e4_seed3710.log"
    lines = [_header(enabled=True)]
    lines.append("step:1600/1800 val_loss:3.48000 train_time:0.000s step_avg:nanms\n")
    lines.append(_kdiag(1600, 0, k=5, ratio=0.90, cos=0.02))
    lines.append(_kdiag(1600, 1, k=5, ratio=0.92, cos=-0.01))
    lines.append(_apply(1600, eff_frac=0.01))
    path.write_text("".join(lines))
    out = _run(["tools/analyze_track3_locom_mechanism.py", str(tmp), "--steps", "1600", "--ks", "5,10"])
    _assert_contains(out, "local K5 correction is locally sane at [1600]")


def test_prefix_manifest_checker(tmp: Path) -> None:
    lanes = [
        ("active_k5", True, "sgd", False, "normal", 0.0),
        ("noloco", False, "sgd", False, "normal", 0.0),
        ("random_norm002", True, "random", True, "normal", 0.02),
        ("orthogonal_k5_norm002", True, "sgd", False, "orthogonal", 0.02),
    ]
    for lane, enabled, local_opt, random, mode, norm_target in lanes:
        (tmp / f"track3_prefix_{lane}_seed3710.log").write_text(
            _header(
                enabled=enabled,
                local_opt=local_opt,
                random=random,
                mode=mode,
                norm_target=norm_target,
            )
        )
    out = _run(["tools/check_track3_locom_prefix_manifest.py", str(tmp)])
    _assert_contains(out, "PASS: all prefix lane headers match the manifest")


def main() -> int:
    tests = [
        test_prefix_direction_specific,
        test_prefix_perturbation_tie,
        test_suffix_scheduler_only,
        test_suffix_insufficient_data,
        test_window_health_slope_break,
        test_mechanism_k5_read,
        test_prefix_manifest_checker,
    ]
    with tempfile.TemporaryDirectory() as tmpdir:
        base = Path(tmpdir)
        for test in tests:
            case_dir = base / test.__name__
            case_dir.mkdir()
            test(case_dir)
            print(f"pass {test.__name__}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
