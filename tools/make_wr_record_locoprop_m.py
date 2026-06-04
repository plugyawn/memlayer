#!/usr/bin/env python3
"""Generate a current-record Track 3 script with additive c_fc LocoProp-M.

This targets the 2026-05-09 current-record source format under
records/track_3_optimization/results/20260509_contra_soft_muon/*.txt. That
source is a simple module-level script, not the sharded speedrun-bank script
patched by make_wr_locoprop_m.py.
"""

from __future__ import annotations

import argparse
from pathlib import Path


LOCOM_BLOCK = r'''
try:
    import torch._dynamo as _wr_locom_dynamo
    _wr_locom_dynamo.config.allow_unspec_int_on_nn_module = True
    _wr_locom_dynamo_disable = _wr_locom_dynamo.disable
except Exception:
    _wr_locom_dynamo_disable = lambda fn: fn

def _wr_locom_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).lower() in {"1", "true", "yes", "on"}

def _wr_locom_parse_set(spec: str, total_layers: int = 12) -> set[int]:
    spec = spec.strip().lower()
    if spec in {"all", "*"}:
        return set(range(total_layers))
    if spec in {"", "none"}:
        return set()
    out: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            out.update(range(int(lo), int(hi) + 1))
        else:
            out.add(int(part))
    return out

def _wr_locom_parse_windows(spec: str) -> list[tuple[int, int]]:
    if not spec.strip():
        return []
    windows = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        lo, hi = part.split(":", 1)
        windows.append((int(lo), int(hi)))
    return windows

WR_LOCOM_ENABLED = _wr_locom_flag("WR_LOCOM_ENABLED", "1")
WR_LOCOM_LAYERS_SPEC = os.environ.get("WR_LOCOM_LAYERS", "all")
WR_LOCOM_LAYER_SET = _wr_locom_parse_set(WR_LOCOM_LAYERS_SPEC)
WR_LOCOM_ACTIVE_WINDOWS = _wr_locom_parse_windows(os.environ.get("WR_LOCOM_ACTIVE_WINDOWS", ""))
WR_LOCOM_START_STEP = int(os.environ.get("WR_LOCOM_START_STEP", "0"))
WR_LOCOM_END_STEP = int(os.environ.get("WR_LOCOM_END_STEP", "1000000000"))
WR_LOCOM_INTERVAL = int(os.environ.get("WR_LOCOM_INTERVAL", "1"))
WR_LOCOM_SAMPLE_TOKENS = int(os.environ.get("WR_LOCOM_SAMPLE_TOKENS", "1024"))
WR_LOCOM_STEPS = int(os.environ.get("WR_LOCOM_STEPS", "4"))
WR_LOCOM_INNER_LR = float(os.environ.get("WR_LOCOM_INNER_LR", "0.1"))
WR_LOCOM_TARGET_GAMMA = float(os.environ.get("WR_LOCOM_TARGET_GAMMA", "1.0"))
WR_LOCOM_PROX = float(os.environ.get("WR_LOCOM_PROX", "0.1"))
WR_LOCOM_ALPHA = float(os.environ.get("WR_LOCOM_ALPHA", "1.0"))
WR_LOCOM_NORM_CAP = float(os.environ.get("WR_LOCOM_NORM_CAP", "0.20"))
WR_LOCOM_NORM_TO_BASE = _wr_locom_flag("WR_LOCOM_NORM_TO_BASE", "0")
WR_LOCOM_REQUIRE_LOSS_DECREASE = _wr_locom_flag("WR_LOCOM_REQUIRE_LOSS_DECREASE", "0")
WR_LOCOM_MIN_COS_DESC = float(os.environ.get("WR_LOCOM_MIN_COS_DESC", "-inf"))
WR_LOCOM_LOG_STEPS = {
    int(x)
    for x in os.environ.get("WR_LOCOM_LOG_STEPS", "0,1,2,10,50,125,250,500,1000,1500,2000,2125,2250,2500,2750,3000").split(",")
    if x.strip()
}

WR_LOCOM_CURRENT_STEP = -1
WR_LOCOM_NEXT_LAYER = 0
WR_LOCOM_SAMPLES: dict[int, dict[str, Tensor]] = {}
WR_LOCOM_CORR: dict[int, Tensor] = {}
WR_LOCOM_APPLY_STATS: list[str] = []

def _wr_locom_active(step: int) -> bool:
    if not (WR_LOCOM_ENABLED and WR_LOCOM_STEPS > 0):
        return False
    if step % max(WR_LOCOM_INTERVAL, 1) != 0:
        return False
    if WR_LOCOM_ACTIVE_WINDOWS:
        return any(start <= step < end for start, end in WR_LOCOM_ACTIVE_WINDOWS)
    return WR_LOCOM_START_STEP <= step < WR_LOCOM_END_STEP

def _wr_locom_layer_active(layer_idx: int) -> bool:
    return layer_idx in WR_LOCOM_LAYER_SET

def _wr_locom_begin_step(step: int) -> None:
    global WR_LOCOM_CURRENT_STEP
    WR_LOCOM_CURRENT_STEP = step
    WR_LOCOM_SAMPLES.clear()
    WR_LOCOM_CORR.clear()
    WR_LOCOM_APPLY_STATS.clear()

@_wr_locom_dynamo_disable
@torch.no_grad()
def _wr_locom_sample_rows(x: Tensor) -> Tensor:
    flat = x.reshape(-1, x.size(-1))
    sample_tokens = WR_LOCOM_SAMPLE_TOKENS
    if dist.is_available() and dist.is_initialized() and dist.get_world_size() > 1:
        sample_tokens = max(1, (sample_tokens + dist.get_world_size() - 1) // dist.get_world_size())
    if sample_tokens <= 0 or flat.size(0) <= sample_tokens:
        return flat.detach().to(torch.bfloat16)
    stride = max(flat.size(0) // sample_tokens, 1)
    return flat[::stride][:sample_tokens].detach().to(torch.bfloat16)

@_wr_locom_dynamo_disable
@torch.no_grad()
def _wr_locom_gather(t: Tensor) -> Tensor:
    if not (dist.is_available() and dist.is_initialized()) or dist.get_world_size() == 1:
        return t.float()
    gathered = [torch.empty_like(t) for _ in range(dist.get_world_size())]
    dist.all_gather(gathered, t.contiguous())
    return torch.cat(gathered, dim=0).float()

@_wr_locom_dynamo_disable
@torch.no_grad()
def _wr_locom_capture_forward(layer_idx: int, x: Tensor, post: Tensor) -> None:
    if not (_wr_locom_active(WR_LOCOM_CURRENT_STEP) and _wr_locom_layer_active(layer_idx)):
        return
    WR_LOCOM_SAMPLES[layer_idx] = {
        "x": _wr_locom_sample_rows(x),
        "post": _wr_locom_sample_rows(post),
    }

@_wr_locom_dynamo_disable
@torch.no_grad()
def _wr_locom_capture_dpre(layer_idx: int, dpre: Tensor) -> None:
    if not (_wr_locom_active(WR_LOCOM_CURRENT_STEP) and _wr_locom_layer_active(layer_idx)):
        return
    sample = WR_LOCOM_SAMPLES.get(layer_idx)
    if sample is not None:
        sample["dpre"] = _wr_locom_sample_rows(dpre)

@torch.no_grad()
def prepare_wr_locom_m(model: nn.Module, step: int) -> None:
    if not _wr_locom_active(step):
        return
    stats = []
    for layer_idx, block in enumerate(model.blocks):
        if not _wr_locom_layer_active(layer_idx):
            continue
        sample = WR_LOCOM_SAMPLES.get(layer_idx)
        if sample is None or "x" not in sample or "post" not in sample or "dpre" not in sample:
            continue
        layer = block.mlp
        x = _wr_locom_gather(sample["x"])
        post0 = _wr_locom_gather(sample["post"])
        dpre = _wr_locom_gather(sample["dpre"])
        target = post0 - WR_LOCOM_TARGET_GAMMA * dpre

        W0 = layer.fc.weight.detach().float()
        b0 = layer.fc.bias.detach().float()
        W = W0.clone()
        inv_n = 1.0 / max(x.size(0), 1)
        loss0 = None
        loss_k = None
        for _ in range(WR_LOCOM_STEPS):
            pre = x @ W.mT + b0
            post = pre.relu().square()
            err = post - target
            loss_k = 0.5 * err.square().mean()
            if loss0 is None:
                loss0 = loss_k
            grad_w = err.mT @ x
            grad_w.mul_(inv_n)
            if WR_LOCOM_PROX != 0:
                grad_w.add_(W - W0, alpha=WR_LOCOM_PROX)
            W.add_(grad_w, alpha=-WR_LOCOM_INNER_LR)

        corr = (W - W0).to(layer.fc.weight.dtype)
        corr_f = corr.float()
        raw_grad = layer.fc.weight.grad.float() if layer.fc.weight.grad is not None else None
        if raw_grad is None:
            grad_norm = float("nan")
            cos_desc = float("nan")
        else:
            raw_desc = -raw_grad
            denom = corr_f.norm().mul(raw_desc.norm()).clamp_min(1e-12)
            cos_desc = float(corr_f.flatten().dot(raw_desc.flatten()) / denom)
            grad_norm = float(raw_grad.norm())
        accepted = True
        loss_decreased = bool(loss_k <= loss0)
        if WR_LOCOM_REQUIRE_LOSS_DECREASE and not loss_decreased:
            accepted = False
        if cos_desc < WR_LOCOM_MIN_COS_DESC:
            accepted = False
        if accepted:
            WR_LOCOM_CORR[layer_idx] = corr

        if step in WR_LOCOM_LOG_STEPS and len(stats) < 8:
            stats.append(
                f"l{layer_idx}:loss0={float(loss0):.3e},lossK={float(loss_k):.3e}"
                f",corr={float(corr_f.norm()):.3e},grad={grad_norm:.3e}"
                f",cos={cos_desc:.3f},accepted={int(accepted)},tokens={x.size(0)}"
            )
    if step in WR_LOCOM_LOG_STEPS and stats:
        print0("wr_locom_prepare step=" + str(step) + " " + " | ".join(stats), console=True)

@torch.no_grad()
def apply_wr_locom_m(model: nn.Module, optimizer: torch.optim.Optimizer, step: int) -> None:
    if not _wr_locom_active(step):
        return
    muon_lr = optimizer.param_groups[0]["lr"]
    for layer_idx, corr in sorted(WR_LOCOM_CORR.items()):
        layer = model.blocks[layer_idx].mlp
        p = layer.fc.weight
        corr_f = corr.float()
        corr_norm = corr_f.norm().clamp_min(1e-12)
        base_step_norm = muon_lr * TARGET_UW * p.float().norm().clamp_min(1e-12)
        if WR_LOCOM_NORM_TO_BASE:
            scale = base_step_norm / corr_norm
        else:
            scale = torch.ones((), device=p.device, dtype=torch.float32)
        if WR_LOCOM_NORM_CAP > 0:
            scale = torch.minimum(scale, (WR_LOCOM_NORM_CAP * base_step_norm) / corr_norm)
        scale = scale * WR_LOCOM_ALPHA
        p.add_(corr, alpha=float(scale))
        if step in WR_LOCOM_LOG_STEPS and len(WR_LOCOM_APPLY_STATS) < 8:
            WR_LOCOM_APPLY_STATS.append(
                f"l{layer_idx}:base={float(base_step_norm):.3e},corr={float(corr_norm):.3e},scale={float(scale):.3e}"
            )
    if step in WR_LOCOM_LOG_STEPS and WR_LOCOM_APPLY_STATS:
        print0("wr_locom_apply step=" + str(step) + " " + " | ".join(WR_LOCOM_APPLY_STATS), console=True)
'''


MLP_BLOCK = r'''class MLP(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        global WR_LOCOM_NEXT_LAYER
        self.layer_idx = WR_LOCOM_NEXT_LAYER
        WR_LOCOM_NEXT_LAYER += 1
        self.wr_locom_layer_enabled = _wr_locom_layer_active(self.layer_idx)
        hdim = 4 * dim
        self.fc = Linear(dim, hdim)
        self.proj = Linear(hdim, dim)

    def forward(self, x: Tensor):
        if self.wr_locom_layer_enabled:
            return self._forward_locom(x)
        return self._forward_plain(x)

    def _forward_plain(self, x: Tensor):
        x = self.fc(x)
        x = x.relu().square()
        x = self.proj(x)
        return x

    @_wr_locom_dynamo_disable
    def _forward_locom(self, x: Tensor):
        pre = self.fc(x)
        post = pre.relu().square()
        if self.training and _wr_locom_active(WR_LOCOM_CURRENT_STEP) and _wr_locom_layer_active(self.layer_idx):
            _wr_locom_capture_forward(self.layer_idx, x, post)
            pre.register_hook(lambda grad, layer_idx=self.layer_idx: _wr_locom_capture_dpre(layer_idx, grad))
        x = self.proj(post)
        return x
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
        "import torch.distributed as dist\n" + LOCOM_BLOCK + "\n",
    )
    text = replace_exact(
        text,
        "FINAL_TRAIN_STEPS = 3040\n",
        f"FINAL_TRAIN_STEPS = int(os.environ.get(\"FINAL_TRAIN_STEPS\", \"{train_steps}\"))\n",
    )
    if schedule_steps is not None:
        text = replace_exact(
            text,
            "FINAL_SCHEDULE_STEPS = 3105\n",
            f"FINAL_SCHEDULE_STEPS = int(os.environ.get(\"FINAL_SCHEDULE_STEPS\", \"{schedule_steps}\"))\n",
        )
    else:
        text = replace_exact(
            text,
            "FINAL_SCHEDULE_STEPS = 3105\n",
            "FINAL_SCHEDULE_STEPS = int(os.environ.get(\"FINAL_SCHEDULE_STEPS\", \"3105\"))\n",
        )
    text = replace_exact(
        text,
        "mbs = 64\n",
        "mbs = int(os.environ.get(\"FINAL_MBS\", \"64\"))\n",
    )
    old_mlp = '''class MLP(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        hdim = 4 * dim
        self.fc = Linear(dim, hdim)
        self.proj = Linear(hdim, dim)

    def forward(self, x: Tensor):
        x = self.fc(x)
        x = x.relu().square()
        x = self.proj(x)
        return x
'''
    text = replace_exact(text, old_mlp, MLP_BLOCK)
    text = replace_exact(
        text,
        "model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()\nmodel.compile(dynamic=False)\n",
        "model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()\n"
        "if WR_LOCOM_ENABLED and not _wr_locom_flag(\"WR_LOCOM_COMPILE\", \"0\"):\n"
        "    print0(\"WR LocoProp-M: skipping model.compile for activation-hook capture\", console=True)\n"
        "else:\n"
        "    model.compile(dynamic=False)\n",
    )
    text = replace_exact(
        text,
        "print0(\"=\"*100)\n\nval_tokens = 20 * 524288\n",
        "print0(\n"
        "    f\"WR LocoProp-M generated run enabled={WR_LOCOM_ENABLED} layers={WR_LOCOM_LAYERS_SPEC} \"\n"
        "    f\"windows={WR_LOCOM_ACTIVE_WINDOWS or [(WR_LOCOM_START_STEP, WR_LOCOM_END_STEP)]} \"\n"
        "    f\"K={WR_LOCOM_STEPS} sample_tokens={WR_LOCOM_SAMPLE_TOKENS} inner_lr={WR_LOCOM_INNER_LR} \"\n"
        "    f\"prox={WR_LOCOM_PROX} alpha={WR_LOCOM_ALPHA} norm_cap={WR_LOCOM_NORM_CAP} \"\n"
        "    f\"norm_to_base={WR_LOCOM_NORM_TO_BASE} min_cos={WR_LOCOM_MIN_COS_DESC}\",\n"
        "    console=True,\n"
        ")\n"
        "print0(\"=\"*100)\n\nval_tokens = 20 * 524288\n",
    )
    text = replace_exact(
        text,
        "for step in range(train_steps + 1):\n",
        "for step in range(train_steps + 1):\n    _wr_locom_begin_step(step)\n",
    )
    text = replace_exact(
        text,
        "    # set optimization hyperparameters and take a step\n    set_hparams(step)\n    for opt in optimizers:\n        opt.step()\n    model.zero_grad(set_to_none=True)\n",
        "    # set optimization hyperparameters and take a step\n"
        "    set_hparams(step)\n"
        "    prepare_wr_locom_m(model, step)\n"
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
