#!/usr/bin/env python3
"""Generate a current-record Track 3 script that resumes from a LocoProp prefix.

The previous WR-stack LocoProp-M probe inserted activation capture hooks into the
current-record source and OOMed before step 0. This generator tests the cleaner
handoff hypothesis instead: load a model checkpoint produced by the simple
Track 3 LocoProp-M harness, then continue with the current-record optimizer
stack and no LocoProp hooks.
"""

from __future__ import annotations

import argparse
from pathlib import Path


RESUME_BLOCK = r'''
def _wr_resume_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).lower() in {"1", "true", "yes", "on"}

WR_RESUME_CHECKPOINT = os.environ.get("WR_RESUME_CHECKPOINT", "").strip()
WR_RESUME_ADVANCE_DATA = _wr_resume_flag("WR_RESUME_ADVANCE_DATA", "1")
WR_RESUME_RESTORE_RNG = _wr_resume_flag("WR_RESUME_RESTORE_RNG", "1")
WR_RESUME_LOAD_ADAM = _wr_resume_flag("WR_RESUME_LOAD_ADAM", "0")
WR_RESUME_STRICT_MODEL = _wr_resume_flag("WR_RESUME_STRICT_MODEL", "1")
WR_RESUME_LOG_MODEL_DIFF = _wr_resume_flag("WR_RESUME_LOG_MODEL_DIFF", "1")
WR_TARGET_LOSS = float(os.environ.get("WR_TARGET_LOSS", "0.0"))

@torch.no_grad()
def maybe_load_wr_resume_checkpoint(model: nn.Module, optimizer1: torch.optim.Optimizer) -> int:
    if not WR_RESUME_CHECKPOINT:
        return 0
    checkpoint = torch.load(WR_RESUME_CHECKPOINT, map_location=device)
    model_state = checkpoint["model"]
    if WR_RESUME_LOG_MODEL_DIFF:
        current_keys = set(model.state_dict().keys())
        saved_keys = set(model_state.keys())
        missing = sorted(current_keys - saved_keys)
        extra = sorted(saved_keys - current_keys)
        print0(
            f"wr_resume_model_key_diff missing={len(missing)} extra={len(extra)} "
            f"missing_head={missing[:6]} extra_head={extra[:6]}",
            console=True,
        )
    model.load_state_dict(model_state, strict=WR_RESUME_STRICT_MODEL)
    if WR_RESUME_LOAD_ADAM:
        saved_optimizers = checkpoint.get("optimizers", [])
        if not saved_optimizers:
            raise ValueError("WR_RESUME_LOAD_ADAM=1 but checkpoint has no optimizer state")
        optimizer1.load_state_dict(saved_optimizers[0])
        # The loaded state dict can overwrite group metadata. Restore WR lr
        # constants while preserving Adam moments.
        for group, initial_lr in zip(optimizer1.param_groups, (0.3, 1 / 320, 0.01)):
            group["initial_lr"] = initial_lr
            group["lr"] = initial_lr
        optimizer1.param_groups[0]["power_c"] = ADAM_EMBED_POWER_C
        optimizer1.param_groups[1]["power_c"] = ADAM_PROJ_POWER_C
        optimizer1.param_groups[2]["power_c"] = ADAM_OTHER_POWER_C
    if WR_RESUME_RESTORE_RNG:
        if "rng_cpu" in checkpoint:
            torch.set_rng_state(checkpoint["rng_cpu"].detach().cpu().to(torch.uint8))
        if "rng_cuda" in checkpoint:
            states = [state.detach().cpu().to(torch.uint8) for state in checkpoint["rng_cuda"]]
            if len(states) == torch.cuda.device_count():
                torch.cuda.set_rng_state_all(states)
            elif len(states) == 1:
                torch.cuda.set_rng_state(states[0], device=device)
            else:
                print0(
                    f"wr_resume_rng_cuda_skip saved_states={len(states)} local_cuda_devices={torch.cuda.device_count()}",
                    console=True,
                )
    step = int(checkpoint["step"])
    print0(
        f"wr_resume_loaded path:{WR_RESUME_CHECKPOINT} step:{step} seed:{checkpoint.get('seed')} "
        f"val_loss:{checkpoint.get('val_loss')} load_adam:{WR_RESUME_LOAD_ADAM} "
        f"restore_rng:{WR_RESUME_RESTORE_RNG}",
        console=True,
    )
    return step
'''


def _code_only(text: str) -> str:
    marker = "\n===================================================================================================="
    if marker in text:
        return text.split(marker, 1)[0].rstrip() + "\n"
    return text


def replace_exact(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"pattern not found:\n{old[:500]}")
    return text.replace(old, new, 1)


def generate(source: Path, output: Path, train_steps: int, schedule_steps: int | None) -> None:
    text = _code_only(source.read_text())
    text = replace_exact(
        text,
        "import torch.distributed as dist\n",
        "import torch.distributed as dist\n" + RESUME_BLOCK + "\n",
    )
    text = replace_exact(
        text,
        "FINAL_TRAIN_STEPS = 3040\n",
        f"FINAL_TRAIN_STEPS = int(os.environ.get(\"FINAL_TRAIN_STEPS\", \"{train_steps}\"))\n",
    )
    if schedule_steps is None:
        text = replace_exact(
            text,
            "FINAL_SCHEDULE_STEPS = 3105\n",
            "FINAL_SCHEDULE_STEPS = int(os.environ.get(\"FINAL_SCHEDULE_STEPS\", \"3105\"))\n",
        )
    else:
        text = replace_exact(
            text,
            "FINAL_SCHEDULE_STEPS = 3105\n",
            f"FINAL_SCHEDULE_STEPS = int(os.environ.get(\"FINAL_SCHEDULE_STEPS\", \"{schedule_steps}\"))\n",
        )
    text = replace_exact(
        text,
        "print0(\"=\"*100)\n\nval_tokens = 20 * 524288\n",
        "print0(\n"
        "    f\"WR resume generated run checkpoint={WR_RESUME_CHECKPOINT or '<none>'} \"\n"
        "    f\"advance_data={WR_RESUME_ADVANCE_DATA} restore_rng={WR_RESUME_RESTORE_RNG} \"\n"
        "    f\"load_adam={WR_RESUME_LOAD_ADAM} target_loss={WR_TARGET_LOSS}\",\n"
        "    console=True,\n"
        ")\n"
        "print0(\"=\"*100)\n\nval_tokens = 20 * 524288\n",
    )
    text = replace_exact(
        text,
        "optimizer2.param_groups[0][\"power_c\"] = MUON_POWER_C\n\n# learning rate schedule: stable then decay\n",
        "optimizer2.param_groups[0][\"power_c\"] = MUON_POWER_C\n"
        "start_step = maybe_load_wr_resume_checkpoint(model, optimizer1)\n"
        "if start_step > 0 and WR_RESUME_ADVANCE_DATA:\n"
        "    for _ in range(start_step):\n"
        "        next(train_loader)\n"
        "    print0(f\"wr_resume_advanced_data steps:{start_step}\", console=True)\n"
        "\n# learning rate schedule: stable then decay\n",
    )
    text = replace_exact(
        text,
        "for p in model.parameters():\n    dist.broadcast(p.detach(), 0)\n",
        "for p in model.parameters():\n    dist.broadcast(p.detach(), 0)\n",
    )
    text = replace_exact(
        text,
        "for step in range(train_steps + 1):\n",
        "for step in range(start_step, train_steps + 1):\n",
    )
    text = replace_exact(
        text,
        '        print0(f"step:{step}/{train_steps} val_loss:{val_loss:.5f} train_time:{training_time:.3f}s"\n'
        '               + f" step_avg:{1000*training_time/max(step, 1):.2f}ms", console=True)\n',
        '        effective_steps = max(step - start_step, 1)\n'
        '        print0(f"step:{step}/{train_steps} val_loss:{val_loss:.5f} train_time:{training_time:.3f}s"\n'
        '               + f" step_avg:{1000*training_time/effective_steps:.2f}ms", console=True)\n'
        '        if WR_TARGET_LOSS > 0 and float(val_loss) <= WR_TARGET_LOSS:\n'
        '            print0(f"target_loss_reached step:{step} val_loss:{val_loss:.5f} target:{WR_TARGET_LOSS:.5f}", console=True)\n'
        '            break\n',
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--steps", type=int, default=3040)
    parser.add_argument("--schedule-steps", type=int, default=None)
    args = parser.parse_args()
    generate(Path(args.source), Path(args.output), args.steps, args.schedule_steps)


if __name__ == "__main__":
    main()
