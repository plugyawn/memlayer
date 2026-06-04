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
WR_RESUME_MODEL_CHECKPOINT = os.environ.get("WR_RESUME_MODEL_CHECKPOINT", "").strip()
WR_RESUME_OPTIMIZER_CHECKPOINT = os.environ.get("WR_RESUME_OPTIMIZER_CHECKPOINT", "").strip()
WR_RESUME_ADVANCE_DATA = _wr_resume_flag("WR_RESUME_ADVANCE_DATA", "1")
WR_RESUME_RESTORE_RNG = _wr_resume_flag("WR_RESUME_RESTORE_RNG", "1")
WR_RESUME_LOAD_ADAM = _wr_resume_flag("WR_RESUME_LOAD_ADAM", "0")
WR_RESUME_LOAD_OPTIMIZERS = _wr_resume_flag("WR_RESUME_LOAD_OPTIMIZERS", "0")
WR_RESUME_STRICT_MODEL = _wr_resume_flag("WR_RESUME_STRICT_MODEL", "1")
WR_RESUME_LOG_MODEL_DIFF = _wr_resume_flag("WR_RESUME_LOG_MODEL_DIFF", "1")
WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE = float(os.environ.get("WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE", "1.0"))
WR_RESUME_OPTIMIZER2_SOAP_RESET = _wr_resume_flag("WR_RESUME_OPTIMIZER2_SOAP_RESET", "0")
WR_RESUME_OPTIMIZER2_NOR_RESET = _wr_resume_flag("WR_RESUME_OPTIMIZER2_NOR_RESET", "0")
WR_SAVE_CHECKPOINT = os.environ.get("WR_SAVE_CHECKPOINT", "").strip()
WR_SAVE_CHECKPOINT_STEP = int(os.environ.get("WR_SAVE_CHECKPOINT_STEP") or "-1")
WR_SAVE_CHECKPOINT_STEPS = {
    int(x)
    for x in os.environ.get("WR_SAVE_CHECKPOINT_STEPS", "").split(",")
    if x.strip()
}
WR_TARGET_LOSS = float(os.environ.get("WR_TARGET_LOSS", "0.0"))

def _wr_load_checkpoint(path: str) -> dict:
    return torch.load(path, map_location=device)

def _wr_checkpoint_step(checkpoint: dict) -> int:
    return int(checkpoint["step"])

def _wr_restore_rng_from_checkpoint(checkpoint: dict) -> None:
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

def _wr_model_diff(model: nn.Module, model_state: dict) -> None:
    if not WR_RESUME_LOG_MODEL_DIFF:
        return
    current_keys = set(model.state_dict().keys())
    saved_keys = set(model_state.keys())
    missing = sorted(current_keys - saved_keys)
    extra = sorted(saved_keys - current_keys)
    print0(
        f"wr_resume_model_key_diff missing={len(missing)} extra={len(extra)} "
        f"missing_head={missing[:6]} extra_head={extra[:6]}",
        console=True,
    )

def _wr_set_optimizer2_step(optimizer2: torch.optim.Optimizer, step: int) -> None:
    if hasattr(optimizer2, "step_count"):
        optimizer2.step_count = step

def _wr_adjust_optimizer2_resume_state(optimizer2: torch.optim.Optimizer) -> None:
    scaled_momentum = 0
    reset_soap = 0
    reset_nor = 0
    for state in optimizer2.state.values():
        momentum = state.get("momentum")
        if torch.is_tensor(momentum) and WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE != 1.0:
            momentum.mul_(WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE)
            scaled_momentum += 1
        if WR_RESUME_OPTIMIZER2_SOAP_RESET and "row_gg" in state:
            for key in ("exp_avg_sq", "row_gg", "col_gg"):
                value = state.get(key)
                if torch.is_tensor(value):
                    value.zero_()
            state["q_row"] = None
            state["q_col"] = None
            state["soap_step"] = 0
            reset_soap += 1
        if WR_RESUME_OPTIMIZER2_NOR_RESET and "second_moment" in state:
            value = state.get("second_moment")
            if torch.is_tensor(value):
                value.zero_()
                reset_nor += 1
    if (
        WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE != 1.0
        or WR_RESUME_OPTIMIZER2_SOAP_RESET
        or WR_RESUME_OPTIMIZER2_NOR_RESET
    ):
        print0(
            f"wr_resume_optimizer2_adjust momentum_scale:{WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE} "
            f"scaled_momentum:{scaled_momentum} soap_reset:{reset_soap} nor_reset:{reset_nor}",
            console=True,
        )

def _wr_checkpoint_save_path(path: str, step: int) -> str:
    if "{step}" in path:
        return path.format(step=step)
    if WR_SAVE_CHECKPOINT_STEPS and len(WR_SAVE_CHECKPOINT_STEPS) > 1:
        base, suffix = os.path.splitext(path)
        return f"{base}_step{step}{suffix or '.pt'}"
    return path

def maybe_save_wr_checkpoint(
    path: str,
    step: int,
    model: nn.Module,
    optimizer1: torch.optim.Optimizer,
    optimizer2: torch.optim.Optimizer,
    *,
    val_loss=None,
) -> None:
    if not path:
        return
    if WR_SAVE_CHECKPOINT_STEPS:
        if step not in WR_SAVE_CHECKPOINT_STEPS:
            return
    elif WR_SAVE_CHECKPOINT_STEP >= 0 and step != WR_SAVE_CHECKPOINT_STEP:
        return
    save_path = _wr_checkpoint_save_path(path, step)
    checkpoint = {
        "step": int(step),
        "seed": int(os.environ.get("WR_SEED", "0")),
        "train_steps": int(FINAL_TRAIN_STEPS),
        "schedule_steps": int(FINAL_SCHEDULE_STEPS),
        "val_loss": None if val_loss is None else float(val_loss),
        "model": {k: v.detach().cpu() for k, v in model.state_dict().items()},
        "optimizers": [optimizer1.state_dict(), optimizer2.state_dict()],
        "rng_cpu": torch.get_rng_state().detach().cpu(),
        "rng_cuda": [s.detach().cpu() for s in torch.cuda.get_rng_state_all()],
    }
    torch.save(checkpoint, save_path)
    print0(f"wr_save_checkpoint path:{save_path} step:{step} val_loss:{checkpoint['val_loss']}", console=True)

@torch.no_grad()
def maybe_load_wr_resume_checkpoint(
    model: nn.Module,
    optimizer1: torch.optim.Optimizer,
    optimizer2: torch.optim.Optimizer,
) -> int:
    model_checkpoint_path = WR_RESUME_MODEL_CHECKPOINT or WR_RESUME_CHECKPOINT
    optimizer_checkpoint_path = WR_RESUME_OPTIMIZER_CHECKPOINT or WR_RESUME_CHECKPOINT
    if not model_checkpoint_path and not optimizer_checkpoint_path:
        return 0
    optimizer_checkpoint = _wr_load_checkpoint(optimizer_checkpoint_path) if optimizer_checkpoint_path else None
    model_checkpoint = (
        optimizer_checkpoint
        if model_checkpoint_path == optimizer_checkpoint_path
        else _wr_load_checkpoint(model_checkpoint_path)
    )
    checkpoint_for_step = model_checkpoint or optimizer_checkpoint
    if optimizer_checkpoint is not None and WR_RESUME_LOAD_OPTIMIZERS:
        saved_optimizers = optimizer_checkpoint.get("optimizers", [])
        if len(saved_optimizers) < 2:
            raise ValueError("WR_RESUME_LOAD_OPTIMIZERS=1 requires two optimizer state dicts")
        optimizer1.load_state_dict(saved_optimizers[0])
        optimizer2.load_state_dict(saved_optimizers[1])
        _wr_adjust_optimizer2_resume_state(optimizer2)
    model_state = model_checkpoint["model"]
    _wr_model_diff(model, model_state)
    model.load_state_dict(model_state, strict=WR_RESUME_STRICT_MODEL)
    if WR_RESUME_LOAD_ADAM:
        adam_checkpoint = optimizer_checkpoint or model_checkpoint
        saved_optimizers = adam_checkpoint.get("optimizers", [])
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
        _wr_restore_rng_from_checkpoint(model_checkpoint)
    step = _wr_checkpoint_step(checkpoint_for_step)
    _wr_set_optimizer2_step(optimizer2, step)
    print0(
        f"wr_resume_loaded model_path:{model_checkpoint_path or '<none>'} "
        f"optimizer_path:{optimizer_checkpoint_path or '<none>'} step:{step} "
        f"model_seed:{model_checkpoint.get('seed')} optimizer_seed:{optimizer_checkpoint.get('seed') if optimizer_checkpoint else None} "
        f"model_val_loss:{model_checkpoint.get('val_loss')} "
        f"load_adam:{WR_RESUME_LOAD_ADAM} load_optimizers:{WR_RESUME_LOAD_OPTIMIZERS} "
        f"restore_rng:{WR_RESUME_RESTORE_RNG} optimizer2_step_count:{getattr(optimizer2, 'step_count', '<none>')} "
        f"optimizer2_momentum_scale:{WR_RESUME_OPTIMIZER2_MOMENTUM_SCALE} "
        f"optimizer2_soap_reset:{WR_RESUME_OPTIMIZER2_SOAP_RESET} "
        f"optimizer2_nor_reset:{WR_RESUME_OPTIMIZER2_NOR_RESET}",
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
        "    f\"model_checkpoint={WR_RESUME_MODEL_CHECKPOINT or '<none>'} \"\n"
        "    f\"optimizer_checkpoint={WR_RESUME_OPTIMIZER_CHECKPOINT or '<none>'} \"\n"
        "    f\"advance_data={WR_RESUME_ADVANCE_DATA} restore_rng={WR_RESUME_RESTORE_RNG} \"\n"
        "    f\"load_adam={WR_RESUME_LOAD_ADAM} load_optimizers={WR_RESUME_LOAD_OPTIMIZERS} \"\n"
        "    f\"save_checkpoint={WR_SAVE_CHECKPOINT or '<none>'}@{WR_SAVE_CHECKPOINT_STEP} \"\n"
        "    f\"target_loss={WR_TARGET_LOSS}\",\n"
        "    console=True,\n"
        ")\n"
        "print0(\"=\"*100)\n\nval_tokens = 20 * 524288\n",
    )
    text = replace_exact(
        text,
        "optimizer2.param_groups[0][\"power_c\"] = MUON_POWER_C\n\n# learning rate schedule: stable then decay\n",
        "optimizer2.param_groups[0][\"power_c\"] = MUON_POWER_C\n"
        "start_step = maybe_load_wr_resume_checkpoint(model, optimizer1, optimizer2)\n"
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
        '        maybe_save_wr_checkpoint(WR_SAVE_CHECKPOINT, step, model, optimizer1, optimizer2, val_loss=val_loss)\n'
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
