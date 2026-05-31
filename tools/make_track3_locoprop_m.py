#!/usr/bin/env python3
"""Generate a Track 3 script with a sampled LocoProp-M local correction."""

from __future__ import annotations

import argparse
from pathlib import Path


LOCOM_CONFIG = r'''
# Modal's CUDA image can route compiled SDPA through cuDNN plans that are
# unavailable for this shape. Keep the Track 3 model unchanged, but force
# PyTorch to use the flash/math SDPA backends instead.
torch.backends.cuda.enable_cudnn_sdp(False)

def _env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).lower() in {"1", "true", "yes", "on"}

def _parse_layer_set(spec: str, total_layers: int = 12) -> set[int]:
    spec = spec.strip().lower()
    if spec in {"all", "*"}:
        return set(range(total_layers))
    layers: set[int] = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            layers.update(range(int(lo), int(hi) + 1))
        else:
            layers.add(int(part))
    return layers

LOCO_M_ENABLED = _env_flag("TRACK3_LOCOM_ENABLED", "1")
LOCO_M_LAYERS_SPEC = os.environ.get("TRACK3_LOCOM_LAYERS", "all")
LOCO_M_LAYER_SET = _parse_layer_set(LOCO_M_LAYERS_SPEC)
LOCO_M_SAMPLE_TOKENS = int(os.environ.get("TRACK3_LOCOM_SAMPLE_TOKENS", "2048"))
LOCO_M_LOCAL_STEPS = int(os.environ.get("TRACK3_LOCOM_STEPS", "4"))
LOCO_M_INNER_LR = float(os.environ.get("TRACK3_LOCOM_INNER_LR", "0.1"))
LOCO_M_TARGET_GAMMA = float(os.environ.get("TRACK3_LOCOM_TARGET_GAMMA", "1.0"))
LOCO_M_PROX = float(os.environ.get("TRACK3_LOCOM_PROX", "0.1"))
LOCO_M_ALPHA = float(os.environ.get("TRACK3_LOCOM_ALPHA", "1.0"))
LOCO_M_NORM_TO_BASE = _env_flag("TRACK3_LOCOM_NORM_TO_BASE", "0")
LOCO_M_NORM_CAP = float(os.environ.get("TRACK3_LOCOM_NORM_CAP", "0.20"))
LOCO_M_START_STEP = int(os.environ.get("TRACK3_LOCOM_START_STEP", "0"))
LOCO_M_END_STEP = int(os.environ.get("TRACK3_LOCOM_END_STEP", "1000000000"))
LOCO_M_INTERVAL = int(os.environ.get("TRACK3_LOCOM_INTERVAL", "1"))
LOCO_M_GATHER_SAMPLES = _env_flag("TRACK3_LOCOM_GATHER_SAMPLES", "1")
LOCO_M_ACCUM_SAMPLES = _env_flag("TRACK3_LOCOM_ACCUM_SAMPLES", "0")
LOCO_M_MICRO_SAMPLE_TOKENS = int(os.environ.get("TRACK3_LOCOM_MICRO_SAMPLE_TOKENS", "32"))
TRACK3_TARGET_LOSS = float(os.environ.get("TRACK3_TARGET_LOSS", "0"))
LOCO_M_LOG_STEPS = {
    int(x)
    for x in os.environ.get("TRACK3_LOCOM_LOG_STEPS", "0,1,2,10,50,125,250,500").split(",")
    if x.strip()
}
LOCO_M_OWNED_LAYER_SET: set[int] = set()
LOCO_M_APPLY_STATS: list[str] = []
'''


LOCOM_MLP = r'''class MLP(nn.Module):
    def __init__(self, dim: int, layer_idx: int):
        super().__init__()
        hdim = 4 * dim
        self.layer_idx = layer_idx
        self.fc = Linear(dim, hdim)
        self.proj = Linear(hdim, dim)
        self._loco_x = None
        self._loco_post = None
        self._loco_dpre = None
        self._loco_x_chunks = []
        self._loco_post_chunks = []
        self._loco_dpre_chunks = []
        self._loco_corr = None
        self._loco_diag = None

    def _loco_sample(self, x: Tensor, sample_tokens: int | None = None) -> Tensor:
        flat = x.reshape(-1, x.size(-1))
        world = dist.get_world_size() if dist.is_initialized() else 1
        sample_tokens = LOCO_M_SAMPLE_TOKENS if sample_tokens is None else sample_tokens
        if LOCO_M_GATHER_SAMPLES and world > 1 and sample_tokens > 0:
            sample_tokens = max(1, (sample_tokens + world - 1) // world)
        if sample_tokens <= 0 or flat.size(0) <= sample_tokens:
            return flat.detach()
        stride = max(flat.size(0) // sample_tokens, 1)
        return flat[::stride][:sample_tokens].detach()

    def _store_loco_sample(self, name: str, value: Tensor):
        if LOCO_M_ACCUM_SAMPLES:
            sample_tokens = LOCO_M_MICRO_SAMPLE_TOKENS
            getattr(self, name + "_chunks").append(self._loco_sample(value, sample_tokens).to(torch.bfloat16))
        else:
            setattr(self, name, self._loco_sample(value).to(torch.bfloat16))

    def _capture_locom(self, x: Tensor, pre: Tensor, post: Tensor):
        if not (LOCO_M_ENABLED and self.training and self.layer_idx in LOCO_M_LAYER_SET):
            return
        self._store_loco_sample("_loco_x", x)
        self._store_loco_sample("_loco_post", post)
        if not LOCO_M_ACCUM_SAMPLES:
            self._loco_dpre = None
        self._loco_corr = None

        def save_dpre(grad):
            self._store_loco_sample("_loco_dpre", grad)
            return grad

        pre.register_hook(save_dpre)

    def forward(self, x: Tensor):
        pre = self.fc(x)
        post = pre.relu().square()
        self._capture_locom(x, pre, post)
        x = self.proj(post)
        return x
'''


LOCOM_HELPERS = r'''
@torch.no_grad()
def _locom_active(step: int) -> bool:
    return (
        LOCO_M_ENABLED
        and LOCO_M_LOCAL_STEPS > 0
        and step >= LOCO_M_START_STEP
        and step < LOCO_M_END_STEP
        and step % max(LOCO_M_INTERVAL, 1) == 0
    )

@torch.no_grad()
def attach_locoprop_m_optimizer(model: nn.Module, optimizer: torch.optim.Optimizer):
    global LOCO_M_OWNED_LAYER_SET
    rank = dist.get_rank() if dist.is_initialized() else 0
    world = dist.get_world_size() if dist.is_initialized() else 1
    fc_to_layer = {
        id(model.blocks[i].mlp.fc.weight): i
        for i in range(len(model.blocks))
        if i in LOCO_M_LAYER_SET
    }
    owned = set()
    for group in optimizer.param_groups:
        for idx, p in enumerate(group["params"]):
            layer_idx = fc_to_layer.get(id(p))
            if layer_idx is not None and idx % world == rank:
                owned.add(layer_idx)
    LOCO_M_OWNED_LAYER_SET = owned
    print0(
        f"locoprop_m_owner rank={rank} world={world} owned_layers={sorted(owned)} "
        f"sample_tokens={LOCO_M_SAMPLE_TOKENS} gather_samples={LOCO_M_GATHER_SAMPLES} "
        f"accum_samples={LOCO_M_ACCUM_SAMPLES} micro_sample_tokens={LOCO_M_MICRO_SAMPLE_TOKENS}",
        console=True,
    )

@torch.no_grad()
def _locom_gather_sample(t: Tensor) -> Tensor:
    if not LOCO_M_GATHER_SAMPLES or not dist.is_initialized() or dist.get_world_size() == 1:
        return t.float()
    gathered = [torch.empty_like(t) for _ in range(dist.get_world_size())]
    dist.all_gather(gathered, t.contiguous())
    return torch.cat(gathered, dim=0).float()

@torch.no_grad()
def _locom_take_sample(mlp: nn.Module, name: str):
    if LOCO_M_ACCUM_SAMPLES:
        chunks = getattr(mlp, name + "_chunks")
        setattr(mlp, name + "_chunks", [])
        if not chunks:
            return None
        return torch.cat(chunks, dim=0)
    value = getattr(mlp, name)
    setattr(mlp, name, None)
    return value

@torch.no_grad()
def prepare_locoprop_m(model: nn.Module, step: int):
    if not _locom_active(step):
        return
    stats = []
    for layer_idx in sorted(LOCO_M_LAYER_SET):
        if layer_idx < 0 or layer_idx >= len(model.blocks):
            continue
        mlp = model.blocks[layer_idx].mlp
        x_local = _locom_take_sample(mlp, "_loco_x")
        post_local = _locom_take_sample(mlp, "_loco_post")
        dpre_local = _locom_take_sample(mlp, "_loco_dpre")
        if x_local is None or post_local is None or dpre_local is None:
            continue
        if mlp.fc.weight.grad is None:
            continue

        x = _locom_gather_sample(x_local)
        post = _locom_gather_sample(post_local)
        dpre = _locom_gather_sample(dpre_local)
        if layer_idx not in LOCO_M_OWNED_LAYER_SET:
            continue

        target = post - LOCO_M_TARGET_GAMMA * dpre
        W0 = mlp.fc.weight.detach().float()
        W = W0.clone()
        inv_n = 1.0 / max(x.size(0), 1)
        loss0 = None
        loss_k = None

        for _ in range(LOCO_M_LOCAL_STEPS):
            pred = x @ W.mT
            pred = pred + mlp.fc.bias.detach().float()
            post = pred.relu().square()
            err = post - target
            loss_k = 0.5 * err.square().mean()
            if loss0 is None:
                loss0 = loss_k
            # Matching-loss gradient: dL/d(preactivation) = post - target.
            # This is the LocoProp-M property that makes the first local step
            # match BackProp when target = post - gamma * dpre.
            grad_w = err.mT @ x
            grad_w.mul_(inv_n)
            if LOCO_M_PROX != 0:
                grad_w.add_(W - W0, alpha=LOCO_M_PROX)
            W.add_(grad_w, alpha=-LOCO_M_INNER_LR)

        corr = (W - W0).to(mlp.fc.weight.dtype)
        mlp._loco_corr = corr
        mlp.fc.weight._loco_corr = corr
        mlp.fc.weight._loco_step = step

        if step in LOCO_M_LOG_STEPS and len(stats) < 4:
            raw_grad = mlp.fc.weight.grad.float()
            corr_f = corr.float()
            raw_desc = -raw_grad
            denom = corr_f.norm().mul(raw_desc.norm()).clamp_min(1e-12)
            cosine = corr_f.flatten().dot(raw_desc.flatten()) / denom
            stats.append(
                f"l{layer_idx}:loss0={float(loss0):.3e}"
                f",lossK={float(loss_k):.3e}"
                f",corr_norm={float(corr_f.norm()):.3e}"
                f",grad_norm={float(raw_grad.norm()):.3e}"
                f",cos_desc={float(cosine):.3f}"
                f",tokens={x.size(0)}"
            )

    if step in LOCO_M_LOG_STEPS and stats:
        print0("locoprop_m_prepare step=" + str(step) + " " + " | ".join(stats), console=True)

@torch.no_grad()
def _locom_apply_owned_param_(p: nn.Parameter, update: Tensor, lr: float):
    corr = getattr(p, "_loco_corr", None)
    if corr is None:
        return
    step = getattr(p, "_loco_step", -1)
    base_step_norm = update.float().norm().mul(lr)
    corr_f = corr.float()
    corr_norm = corr_f.norm().clamp_min(1e-12)
    scale = torch.ones((), device=corr.device, dtype=torch.float32)
    if LOCO_M_NORM_TO_BASE:
        scale = base_step_norm / corr_norm
    if LOCO_M_NORM_CAP > 0:
        max_norm = LOCO_M_NORM_CAP * base_step_norm
        scale = torch.minimum(scale, max_norm / corr_norm)
    scale = scale * LOCO_M_ALPHA
    p.add_(corr, alpha=float(scale))
    if step in LOCO_M_LOG_STEPS and len(LOCO_M_APPLY_STATS) < 8:
        LOCO_M_APPLY_STATS.append(
            f"shape={tuple(p.shape)}:base_step={float(base_step_norm):.3e}"
            f",corr_norm={float(corr_norm):.3e},scale={float(scale):.3e}"
        )
    p._loco_corr = None

@torch.no_grad()
def flush_locoprop_m_apply_stats(step: int):
    if step in LOCO_M_LOG_STEPS and LOCO_M_APPLY_STATS:
        print0("locoprop_m_apply step=" + str(step) + " " + " | ".join(LOCO_M_APPLY_STATS[:8]), console=True)
    LOCO_M_APPLY_STATS.clear()
'''


def replace_exact(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"pattern not found:\n{old[:240]}")
    return text.replace(old, new, 1)


def generate(source: Path, output: Path, train_steps: int) -> None:
    text = source.read_text()
    text = replace_exact(
        text,
        "import torch.distributed as dist\n",
        "import torch.distributed as dist\n" + LOCOM_CONFIG,
    )
    plain_mlp = """class MLP(nn.Module):
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
"""
    nm_mlp = """class MLP(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        hdim = 4 * dim
        self.fc = Linear(dim, hdim)
        self.proj = Linear(hdim, dim)
        self.register_buffer("fc_xtx", torch.zeros(dim, dim, dtype=torch.float32), persistent=False)
        self.register_buffer("fc_count", torch.zeros((), dtype=torch.float32), persistent=False)
        self.register_buffer("proj_xtx", torch.zeros(4, dim, dim, dtype=torch.float32), persistent=False)
        self.register_buffer("proj_count", torch.zeros((), dtype=torch.float32), persistent=False)

    def forward(self, x: Tensor):
        x = self.fc(x)
        x = x.relu().square()
        x = self.proj(x)
        return x
"""
    if plain_mlp in text:
        text = text.replace(plain_mlp, LOCOM_MLP, 1)
    elif nm_mlp in text:
        text = text.replace(nm_mlp, LOCOM_MLP, 1)
    else:
        raise RuntimeError("MLP class pattern not found")
    text = replace_exact(
        text,
        """class Block(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.attn = CausalSelfAttention(dim)
        self.mlp = MLP(dim)
        self.norm1 = RMSNorm(dim)
        self.norm2 = RMSNorm(dim)
""",
        """class Block(nn.Module):
    def __init__(self, dim: int, layer_idx: int):
        super().__init__()
        self.attn = CausalSelfAttention(dim)
        self.mlp = MLP(dim, layer_idx)
        self.norm1 = RMSNorm(dim)
        self.norm2 = RMSNorm(dim)
""",
    )
    text = replace_exact(
        text,
        "        self.blocks = nn.ModuleList([Block(model_dim) for _ in range(num_layers)])\n",
        "        self.blocks = nn.ModuleList([Block(model_dim, i) for i in range(num_layers)])\n",
    )
    text = replace_exact(
        text,
        """@torch.compile
def muon_update(grad, momentum, mu=0.95, nesterov=True):
    momentum.lerp_(grad, 1 - mu)
    update = grad.lerp_(momentum, mu) if nesterov else momentum
    update = zeropower_via_newtonschulz5(update)
    update *= max(1, grad.size(-2) / grad.size(-1))**0.5
    return update
""",
        """@torch.compile
def muon_update(grad, momentum, mu=0.95, nesterov=True):
    momentum.lerp_(grad, 1 - mu)
    update = grad.lerp_(momentum, mu) if nesterov else momentum
    update = zeropower_via_newtonschulz5(update)
    update *= max(1, grad.size(-2) / grad.size(-1))**0.5
    return update
""" + LOCOM_HELPERS,
    )
    text = replace_exact(
        text,
        "                    update = muon_update(p.grad, state[\"momentum\"], mu=group[\"mu\"])\n",
        "                    update = muon_update(p.grad, state[\"momentum\"], mu=group[\"mu\"])\n"
        "                    state[\"last_update_norm\"] = update.float().norm()\n",
    )
    text = replace_exact(
        text,
        "                    p.mul_(1 - group[\"lr\"] * group[\"weight_decay\"])\n"
        "                    p.add_(update, alpha=-group[\"lr\"])\n",
        "                    p.mul_(1 - group[\"lr\"] * group[\"weight_decay\"])\n"
        "                    p.add_(update, alpha=-group[\"lr\"])\n"
        "                    _locom_apply_owned_param_(p, update, group[\"lr\"])\n",
    )
    if "model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()\nattach_precond_stats(model)\nmodel.compile(dynamic=False)\n" in text:
        text = replace_exact(
            text,
            "model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()\nattach_precond_stats(model)\nmodel.compile(dynamic=False)\n",
            "model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()\n"
            "attach_precond_stats(model)\n"
            "if not LOCO_M_ENABLED or _env_flag(\"TRACK3_LOCOM_COMPILE\", \"0\"):\n"
            "    model.compile(dynamic=False)\n",
        )
    else:
        text = replace_exact(
            text,
            "model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()\nmodel.compile(dynamic=False)\n",
            "model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()\n"
            "if not LOCO_M_ENABLED or _env_flag(\"TRACK3_LOCOM_COMPILE\", \"0\"):\n"
            "    model.compile(dynamic=False)\n",
        )
    text = replace_exact(
        text,
        'print0(f"Running PyTorch {torch.version.__version__} compiled for CUDA {torch.version.cuda}"',
        f'print0("Track3 LocoProp-M generated run: train_steps={train_steps}")\n'
        'print0(f"LocoM enabled={LOCO_M_ENABLED} layers={LOCO_M_LAYERS_SPEC} steps={LOCO_M_LOCAL_STEPS} sample_tokens={LOCO_M_SAMPLE_TOKENS} gather={LOCO_M_GATHER_SAMPLES} accum={LOCO_M_ACCUM_SAMPLES} micro_sample_tokens={LOCO_M_MICRO_SAMPLE_TOKENS} inner_lr={LOCO_M_INNER_LR} target_gamma={LOCO_M_TARGET_GAMMA} prox={LOCO_M_PROX} alpha={LOCO_M_ALPHA} norm_to_base={LOCO_M_NORM_TO_BASE} norm_cap={LOCO_M_NORM_CAP} target_loss={TRACK3_TARGET_LOSS}")\n'
        'print0(f"Running PyTorch {torch.version.__version__} compiled for CUDA {torch.version.cuda}"',
    )
    if "    train_steps = 3350\n" in text:
        text = replace_exact(
            text,
            "    train_steps = 3350\n",
            f"    train_steps = {train_steps}  # generated by tools/make_track3_locoprop_m.py\n",
        )
    else:
        text = replace_exact(
            text,
            "    train_steps = 3300\n",
            f"    train_steps = {train_steps}  # generated by tools/make_track3_locoprop_m.py\n",
        )
    text = replace_exact(
        text,
        "mbs = 64\n",
        "mbs = int(os.environ.get(\"TRACK3_MBS\", \"64\"))\n",
    )
    text = replace_exact(
        text,
        "        val_step_freq = 125 if step / train_steps < 0.9 else 25\n",
        "        val_step_freq = int(os.environ.get(\"SCREEN_VAL_EVERY\", \"125\")) if step / train_steps < 0.9 else 25\n",
    )
    text = replace_exact(
        text,
        "            model.train()\n            # start the clock again\n",
        "            if TRACK3_TARGET_LOSS > 0 and float(val_loss) <= TRACK3_TARGET_LOSS:\n"
        "                print0(f\"target_loss_reached step:{step} val_loss:{val_loss:.5f} target:{TRACK3_TARGET_LOSS:.5f}\", console=True)\n"
        "                break\n"
        "            model.train()\n            # start the clock again\n",
    )
    text = replace_exact(
        text,
        """        set_hparams(step)
        for opt in optimizers:
            opt.step()
        model.zero_grad(set_to_none=True)
""",
        """        set_hparams(step)
        prepare_locoprop_m(model, step)
        for opt in optimizers:
            opt.step()
        flush_locoprop_m_apply_stats(step)
        model.zero_grad(set_to_none=True)
""",
    )
    text = replace_exact(
        text,
        "assert 8 % dist.get_world_size() == 0\n",
        "assert 8 % dist.get_world_size() == 0\n",
    )
    if "    optimizer2.attach_preconditioner()\n    optimizers = [optimizer1, optimizer2]\n" in text:
        text = replace_exact(
            text,
            "    optimizer2.attach_preconditioner()\n    optimizers = [optimizer1, optimizer2]\n",
            "    optimizer2.attach_preconditioner()\n"
            "    attach_locoprop_m_optimizer(model, optimizer2)\n"
            "    optimizers = [optimizer1, optimizer2]\n",
        )
    else:
        text = replace_exact(
            text,
            "    optimizer2 = Muon([p for p in model.blocks.parameters() if p.ndim >= 2],\n"
            "                      lr=0.035, weight_decay=0.025)\n",
            "    optimizer2 = Muon([p for p in model.blocks.parameters() if p.ndim >= 2],\n"
            "                      lr=0.035, weight_decay=0.025)\n"
            "    attach_locoprop_m_optimizer(model, optimizer2)\n",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="records/track_3_optimization/train_gpt_simple.py")
    parser.add_argument("--output", required=True)
    parser.add_argument("--steps", type=int, default=500)
    args = parser.parse_args()
    generate(Path(args.source), Path(args.output), args.steps)


if __name__ == "__main__":
    main()
