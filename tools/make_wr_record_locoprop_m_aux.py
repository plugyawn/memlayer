#!/usr/bin/env python3
"""Generate current-record Track 3 with hookless auxiliary LocoProp-M capture.

The older WR LocoProp-M generator captures dpre through main-graph Python hooks,
which forces `model.compile` off and needs small microbatches. This variant keeps
the main training path compiled. After the normal backward pass, it runs a small
auxiliary forward/autograd pass on sampled sequences from the same training
batch. The auxiliary forward is spelled out for active MLP blocks, so neither
the main nor auxiliary path uses Python activation hooks. It computes dpre with
`torch.autograd.grad`, then applies the same state-decoupled LocoProp-M
correction.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import make_wr_record_locoprop_m as locom


AUX_BLOCK = r'''
WR_LOCOM_AUX_SEQS = int(os.environ.get("WR_LOCOM_AUX_SEQS", "16"))

def _wr_locom_aux_forward_capture(model: nn.Module, inputs: Tensor, targets: Tensor, active_layers: list[int]) -> Tensor:
    active = set(active_layers)
    pre_tensors = []
    pre_layers = []

    x = model.norm1(model.embed(inputs))
    for layer_idx, block in enumerate(model.blocks):
        x = x + block.attn(block.norm1(x))
        if layer_idx in active:
            mlp_in = block.norm2(x)
            pre = block.mlp.fc(mlp_in)
            post = pre.relu().square()
            WR_LOCOM_SAMPLES[layer_idx] = {
                "x": _wr_locom_sample_rows(mlp_in),
                "post": _wr_locom_sample_rows(post),
            }
            pre_layers.append(layer_idx)
            pre_tensors.append(pre)
            x = x + block.mlp.proj(post)
        else:
            x = x + block.mlp(block.norm2(x))

    logits = model.proj(model.norm2(x)).float()
    logits = 15 * logits * (logits.square() + 15**2).rsqrt()
    aux_loss = F.cross_entropy(logits.view(targets.numel(), -1), targets.view(-1), reduction="sum")
    dpre_tensors = torch.autograd.grad(
        aux_loss,
        pre_tensors,
        retain_graph=False,
        create_graph=False,
        allow_unused=True,
    )
    for layer_idx, dpre in zip(pre_layers, dpre_tensors):
        if dpre is not None:
            _wr_locom_capture_dpre(layer_idx, dpre)
    return aux_loss

def prepare_wr_locom_m_aux(model: nn.Module, inputs: Tensor, targets: Tensor, step: int) -> None:
    if not _wr_locom_active(step):
        return
    active_layers = [i for i, _ in enumerate(model.blocks) if _wr_locom_layer_active(i)]
    if not active_layers:
        return

    seqs = max(1, min(int(WR_LOCOM_AUX_SEQS), inputs.size(0)))
    aux_inputs = inputs[-seqs:].detach()
    aux_targets = targets[-seqs:].detach()
    with torch.enable_grad():
        _wr_locom_aux_forward_capture(model, aux_inputs, aux_targets, active_layers)

    prepare_wr_locom_m(model, step)
'''


def generate(source: Path, output: Path, train_steps: int, schedule_steps: int | None) -> None:
    text = locom._code_only(source.read_text())
    text = locom.replace_exact(
        text,
        "import torch.distributed as dist\n",
        "import torch.distributed as dist\n" + locom.LOCOM_BLOCK + "\n" + AUX_BLOCK + "\n",
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
        "    f\"WR LocoProp-M aux generated run enabled={WR_LOCOM_ENABLED} layers={WR_LOCOM_LAYERS_SPEC} \"\n"
        "    f\"windows={WR_LOCOM_ACTIVE_WINDOWS or [(WR_LOCOM_START_STEP, WR_LOCOM_END_STEP)]} \"\n"
        "    f\"K={WR_LOCOM_STEPS} sample_tokens={WR_LOCOM_SAMPLE_TOKENS} aux_seqs={WR_LOCOM_AUX_SEQS} \"\n"
        "    f\"inner_lr={WR_LOCOM_INNER_LR} prox={WR_LOCOM_PROX} alpha={WR_LOCOM_ALPHA} \"\n"
        "    f\"norm_cap={WR_LOCOM_NORM_CAP} norm_to_base={WR_LOCOM_NORM_TO_BASE} \"\n"
        "    f\"min_cos={WR_LOCOM_MIN_COS_DESC} batched_prep={WR_LOCOM_BATCHED_PREP} \"\n"
        "    f\"aux_hookless=1\",\n"
        "    console=True,\n"
        ")\n"
        "print0(\"=\"*100)\n\nval_tokens = 20 * 524288\n",
    )
    text = locom.replace_exact(
        text,
        "for step in range(train_steps + 1):\n",
        "for step in range(train_steps + 1):\n    _wr_locom_begin_step(step)\n",
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
