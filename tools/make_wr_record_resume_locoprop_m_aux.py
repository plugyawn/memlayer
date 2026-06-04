#!/usr/bin/env python3
"""Generate current-record Track 3 resume script with aux-capture LocoProp-M."""

from __future__ import annotations

import argparse
from pathlib import Path

import make_wr_record_locoprop_m as locom
import make_wr_record_locoprop_m_aux as aux
import make_wr_record_resume as resume


def generate(source: Path, output: Path, train_steps: int, schedule_steps: int | None) -> None:
    text = locom._code_only(source.read_text())
    text = locom.replace_exact(
        text,
        "import torch.distributed as dist\n",
        "import torch.distributed as dist\n" + resume.RESUME_BLOCK + "\n" + locom.LOCOM_BLOCK + "\n" + aux.AUX_BLOCK + "\n",
    )
    text = locom.replace_exact(
        text,
        "FINAL_TRAIN_STEPS = 3040\n",
        f"FINAL_TRAIN_STEPS = int(os.environ.get(\"FINAL_TRAIN_STEPS\", \"{train_steps}\"))\n",
    )
    if schedule_steps is not None:
        text = locom.replace_exact(
            text,
            "FINAL_SCHEDULE_STEPS = 3105\n",
            f"FINAL_SCHEDULE_STEPS = int(os.environ.get(\"FINAL_SCHEDULE_STEPS\", \"{schedule_steps}\"))\n",
        )
    else:
        text = locom.replace_exact(
            text,
            "FINAL_SCHEDULE_STEPS = 3105\n",
            "FINAL_SCHEDULE_STEPS = int(os.environ.get(\"FINAL_SCHEDULE_STEPS\", \"3105\"))\n",
        )
    text = locom.replace_exact(
        text,
        "mbs = 64\n",
        "mbs = int(os.environ.get(\"FINAL_MBS\", \"64\"))\n",
    )
    text = locom.replace_exact(
        text,
        "print0(\"=\"*100)\n\nval_tokens = 20 * 524288\n",
        "print0(\n"
        "    f\"WR resume+LocoProp-M aux generated run checkpoint={WR_RESUME_CHECKPOINT or '<none>'} \"\n"
        "    f\"model_checkpoint={WR_RESUME_MODEL_CHECKPOINT or '<none>'} \"\n"
        "    f\"optimizer_checkpoint={WR_RESUME_OPTIMIZER_CHECKPOINT or '<none>'} \"\n"
        "    f\"advance_data={WR_RESUME_ADVANCE_DATA} restore_rng={WR_RESUME_RESTORE_RNG} \"\n"
        "    f\"load_adam={WR_RESUME_LOAD_ADAM} load_optimizers={WR_RESUME_LOAD_OPTIMIZERS} \"\n"
        "    f\"target_loss={WR_TARGET_LOSS} \"\n"
        "    f\"loco_enabled={WR_LOCOM_ENABLED} layers={WR_LOCOM_LAYERS_SPEC} \"\n"
        "    f\"windows={WR_LOCOM_ACTIVE_WINDOWS or [(WR_LOCOM_START_STEP, WR_LOCOM_END_STEP)]} \"\n"
        "    f\"K={WR_LOCOM_STEPS} sample_tokens={WR_LOCOM_SAMPLE_TOKENS} aux_seqs={WR_LOCOM_AUX_SEQS} \"\n"
        "    f\"inner_lr={WR_LOCOM_INNER_LR} prox={WR_LOCOM_PROX} alpha={WR_LOCOM_ALPHA} \"\n"
        "    f\"norm_cap={WR_LOCOM_NORM_CAP} norm_to_base={WR_LOCOM_NORM_TO_BASE} \"\n"
        "    f\"min_cos={WR_LOCOM_MIN_COS_DESC} aux_hookless=1\",\n"
        "    console=True,\n"
        ")\n"
        "print0(\"=\"*100)\n\nval_tokens = 20 * 524288\n",
    )
    text = locom.replace_exact(
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
    text = locom.replace_exact(
        text,
        "for step in range(train_steps + 1):\n",
        "for step in range(start_step, train_steps + 1):\n    _wr_locom_begin_step(step)\n",
    )
    text = locom.replace_exact(
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
    text = locom.replace_exact(
        text,
        "    # set optimization hyperparameters and take a step\n    set_hparams(step)\n    for opt in optimizers:\n        opt.step()\n    model.zero_grad(set_to_none=True)\n",
        "    # set optimization hyperparameters and take a step\n"
        "    set_hparams(step)\n"
        "    prepare_wr_locom_m_aux(model, inputs, targets, step)\n"
        "    for opt in optimizers:\n"
        "        opt.step()\n"
        "    apply_wr_locom_m(model, optimizer2, step)\n"
        "    model.zero_grad(set_to_none=True)\n",
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
