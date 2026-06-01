#!/usr/bin/env python3
"""Generate a Track 3 script with a sampled LocoProp-M local correction."""

from __future__ import annotations

import argparse
import re
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
LOCO_M_LOCAL_OPT = os.environ.get("TRACK3_LOCOM_LOCAL_OPT", "sgd").lower()
LOCO_M_LOCAL_LR_DECAY = _env_flag("TRACK3_LOCOM_LOCAL_LR_DECAY", "0")
LOCO_M_RMS_BETA1 = float(os.environ.get("TRACK3_LOCOM_RMS_BETA1", "0.999"))
LOCO_M_RMS_BETA2 = float(os.environ.get("TRACK3_LOCOM_RMS_BETA2", "0.9"))
LOCO_M_RMS_EPS = float(os.environ.get("TRACK3_LOCOM_RMS_EPS", "1e-5"))
TRACK3_TARGET_LOSS = float(os.environ.get("TRACK3_TARGET_LOSS", "0"))
TRACK3_SEED_BASE = int(os.environ.get("TRACK3_SEED_BASE", "0"))
TRACK3_SEED_OFFSET = int(os.environ.get("TRACK3_SEED_OFFSET", "0"))
TRACK3_COOLDOWN_FRAC = float(os.environ.get("TRACK3_COOLDOWN_FRAC", "0.7"))
TRACK3_LR_SCHEDULE = os.environ.get("TRACK3_LR_SCHEDULE", "linear").lower()
TRACK3_LR_POWER = float(os.environ.get("TRACK3_LR_POWER", "1.0"))
TRACK3_LR_SCHEDULE_STEPS = int(os.environ.get("TRACK3_LR_SCHEDULE_STEPS", "0"))
TRACK3_ADAM_EMBED_POWER_C = float(os.environ.get("TRACK3_ADAM_EMBED_POWER_C", "4.976805410800738e-05"))
TRACK3_ADAM_PROJ_POWER_C = float(os.environ.get("TRACK3_ADAM_PROJ_POWER_C", "5.184172302917436e-07"))
TRACK3_ADAM_OTHER_POWER_C = float(os.environ.get("TRACK3_ADAM_OTHER_POWER_C", "1.6589351369335795e-06"))
TRACK3_MUON_POWER_C = float(os.environ.get("TRACK3_MUON_POWER_C", "3.3169534699576625e-06"))
if TRACK3_LR_SCHEDULE not in {"linear", "power", "pr287"}:
    raise ValueError("TRACK3_LR_SCHEDULE must be 'linear', 'power', or 'pr287'")
TRACK3_SOFT_MUON = _env_flag("TRACK3_SOFT_MUON", "0")
TRACK3_SOFT_MUON_BLEND = float(os.environ.get("TRACK3_SOFT_MUON_BLEND", "1.0"))
TRACK3_SOFT_MUON_NORM_RESTORE = _env_flag("TRACK3_SOFT_MUON_NORM_RESTORE", "1")
TRACK3_CHECKPOINT_STEPS = {
    int(x)
    for x in os.environ.get("TRACK3_CHECKPOINT_STEPS", "").split(",")
    if x.strip()
}
TRACK3_CHECKPOINT_DIR = os.environ.get("TRACK3_CHECKPOINT_DIR", "")
TRACK3_CHECKPOINT_PREFIX = os.environ.get("TRACK3_CHECKPOINT_PREFIX", "track3_locom")
TRACK3_CHECKPOINT_EXIT_AFTER = _env_flag("TRACK3_CHECKPOINT_EXIT_AFTER", "0")
TRACK3_RESUME_CHECKPOINT = os.environ.get("TRACK3_RESUME_CHECKPOINT", "")
TRACK3_RESUME_ADVANCE_DATA = _env_flag("TRACK3_RESUME_ADVANCE_DATA", "1")
TRACK3_RESUME_RESTORE_RNG = _env_flag("TRACK3_RESUME_RESTORE_RNG", "1")
LOCO_M_LOG_STEPS = {
    int(x)
    for x in os.environ.get("TRACK3_LOCOM_LOG_STEPS", "0,1,2,10,50,125,250,500").split(",")
    if x.strip()
}
LOCO_M_OWNED_LAYER_SET: set[int] = set()
LOCO_M_APPLY_STATS: list[str] = []
LOCO_M_CURRENT_STEP = -1
LOCO_M_CAPTURE_THIS_MICRO = True
'''


LOCOM_MLP = r'''class MLP(nn.Module):
    def __init__(self, dim: int, layer_idx: int):
        super().__init__()
        hdim = 4 * dim
        self.layer_idx = layer_idx
        self.fc = Linear(dim, hdim)
        self.proj = Linear(hdim, dim)
        self.register_buffer("fc_xtx", torch.zeros(dim, dim, dtype=torch.float32), persistent=False)
        self.register_buffer("fc_count", torch.zeros((), dtype=torch.float32), persistent=False)
        self.register_buffer("proj_xtx", torch.zeros(4, dim, dim, dtype=torch.float32), persistent=False)
        self.register_buffer("proj_count", torch.zeros((), dtype=torch.float32), persistent=False)
        self._loco_x = None
        self._loco_post = None
        self._loco_dpre = None
        self._loco_x_chunks = []
        self._loco_post_chunks = []
        self._loco_dpre_chunks = []
        self._loco_corr = None
        self._loco_diag = None
        self.register_buffer("_loco_rms_avg", torch.zeros(hdim, dim, dtype=torch.float32), persistent=False)
        self.register_buffer("_loco_rms_mom", torch.zeros(hdim, dim, dtype=torch.float32), persistent=False)

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
        if torch.compiler.is_compiling():
            return
        if not (
            LOCO_M_ENABLED
            and self.training
            and LOCO_M_CAPTURE_THIS_MICRO
            and self.layer_idx in LOCO_M_LAYER_SET
            and _locom_active(LOCO_M_CURRENT_STEP)
        ):
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
def set_locoprop_m_current_step(step: int):
    global LOCO_M_CURRENT_STEP
    LOCO_M_CURRENT_STEP = step

@torch.no_grad()
def set_locoprop_m_capture_this_micro(enabled: bool):
    global LOCO_M_CAPTURE_THIS_MICRO
    LOCO_M_CAPTURE_THIS_MICRO = enabled

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

        rms_avg = mlp._loco_rms_avg
        rms_mom = mlp._loco_rms_mom

        for local_step in range(LOCO_M_LOCAL_STEPS):
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
            local_lr = LOCO_M_INNER_LR
            if LOCO_M_LOCAL_LR_DECAY:
                local_lr *= max(1.0 - float(local_step) / max(LOCO_M_LOCAL_STEPS, 1), 0.25)
            if LOCO_M_LOCAL_OPT == "rmsprop":
                rms_avg.mul_(LOCO_M_RMS_BETA2).addcmul_(grad_w, grad_w, value=1.0 - LOCO_M_RMS_BETA2)
                denom = rms_avg.sqrt().add_(LOCO_M_RMS_EPS)
                rms_mom.mul_(LOCO_M_RMS_BETA1).addcdiv_(grad_w, denom, value=local_lr)
                W.add_(rms_mom, alpha=-1.0)
            else:
                W.add_(grad_w, alpha=-local_lr)

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
                f",opt={LOCO_M_LOCAL_OPT}"
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

@torch.no_grad()
def maybe_save_track3_checkpoint(model: nn.Module, optimizers: list[torch.optim.Optimizer], step: int, train_steps: int, trial_idx: int, val_loss: Tensor | None):
    if step not in TRACK3_CHECKPOINT_STEPS:
        return False
    if not TRACK3_CHECKPOINT_DIR:
        raise ValueError("TRACK3_CHECKPOINT_STEPS is set but TRACK3_CHECKPOINT_DIR is empty")
    rank = dist.get_rank() if dist.is_initialized() else 0
    if rank == 0:
        checkpoint_dir = Path(TRACK3_CHECKPOINT_DIR)
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        seed = TRACK3_SEED_BASE + TRACK3_SEED_OFFSET + trial_idx
        path = checkpoint_dir / f"{TRACK3_CHECKPOINT_PREFIX}_seed{seed}_step{step}.pt"
        tmp_path = path.with_suffix(path.suffix + ".tmp")
        payload = {
            "step": step,
            "train_steps": train_steps,
            "trial_idx": trial_idx,
            "seed": seed,
            "val_loss": None if val_loss is None else float(val_loss),
            "model": model.state_dict(),
            "optimizers": [opt.state_dict() for opt in optimizers],
            "rng_cpu": torch.get_rng_state(),
            "rng_cuda": torch.cuda.get_rng_state_all(),
            "config": {
                "source": "track3_locom_generated",
                "loco_m_enabled": LOCO_M_ENABLED,
                "loco_m_layers": LOCO_M_LAYERS_SPEC,
                "loco_m_steps": LOCO_M_LOCAL_STEPS,
                "loco_m_sample_tokens": LOCO_M_SAMPLE_TOKENS,
                "loco_m_inner_lr": LOCO_M_INNER_LR,
                "loco_m_target_gamma": LOCO_M_TARGET_GAMMA,
                "loco_m_prox": LOCO_M_PROX,
                "loco_m_alpha": LOCO_M_ALPHA,
                "loco_m_norm_to_base": LOCO_M_NORM_TO_BASE,
                "loco_m_norm_cap": LOCO_M_NORM_CAP,
                "loco_m_start_step": LOCO_M_START_STEP,
                "loco_m_end_step": LOCO_M_END_STEP,
                "loco_m_interval": LOCO_M_INTERVAL,
                "loco_m_gather_samples": LOCO_M_GATHER_SAMPLES,
                "loco_m_accum_samples": LOCO_M_ACCUM_SAMPLES,
                "track3_cooldown_frac": TRACK3_COOLDOWN_FRAC,
                "track3_lr_schedule": TRACK3_LR_SCHEDULE,
                "track3_lr_power": TRACK3_LR_POWER,
                "track3_lr_schedule_steps": TRACK3_LR_SCHEDULE_STEPS,
            },
        }
        torch.save(payload, tmp_path)
        os.replace(tmp_path, path)
        print0(f"track3_checkpoint_saved step:{step} path:{path} val_loss:{payload['val_loss']}", console=True)
    if dist.is_initialized():
        dist.barrier()
    return TRACK3_CHECKPOINT_EXIT_AFTER

@torch.no_grad()
def maybe_load_track3_checkpoint(model: nn.Module, optimizers: list[torch.optim.Optimizer]) -> int:
    if not TRACK3_RESUME_CHECKPOINT:
        return 0
    checkpoint = torch.load(TRACK3_RESUME_CHECKPOINT, map_location="cuda")
    model.load_state_dict(checkpoint["model"], strict=True)
    saved_optimizers = checkpoint.get("optimizers", [])
    if len(saved_optimizers) != len(optimizers):
        raise ValueError(
            f"checkpoint has {len(saved_optimizers)} optimizer states, expected {len(optimizers)}"
        )
    for optimizer, optimizer_state in zip(optimizers, saved_optimizers):
        optimizer.load_state_dict(optimizer_state)
    if TRACK3_RESUME_RESTORE_RNG:
        if "rng_cpu" in checkpoint:
            torch.set_rng_state(checkpoint["rng_cpu"].detach().cpu().to(torch.uint8))
        if "rng_cuda" in checkpoint:
            torch.cuda.set_rng_state_all([
                state.detach().cpu().to(torch.uint8)
                for state in checkpoint["rng_cuda"]
            ])
    step = int(checkpoint["step"])
    print0(
        f"track3_checkpoint_loaded path:{TRACK3_RESUME_CHECKPOINT} step:{step} "
        f"seed:{checkpoint.get('seed')} val_loss:{checkpoint.get('val_loss')}",
        console=True,
    )
    return step
'''


def replace_exact(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"pattern not found:\n{old[:240]}")
    return text.replace(old, new, 1)


def generate(source: Path, output: Path, train_steps: int) -> None:
    source_label = str(source)
    text = source.read_text()
    if source.suffix == ".txt" and "\n====================================================================================================\n" in text:
        text = text.split("\n====================================================================================================\n", 1)[0]
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
    simple_muon_update = """@torch.compile
def muon_update(grad, momentum, mu=0.95, nesterov=True):
    momentum.lerp_(grad, 1 - mu)
    update = grad.lerp_(momentum, mu) if nesterov else momentum
    update = zeropower_via_newtonschulz5(update)
    update *= max(1, grad.size(-2) / grad.size(-1))**0.5
    return update
"""
    if simple_muon_update in text:
        text = text.replace(
            simple_muon_update,
            """def _track3_gram_frobenius_norm_estimate(x: torch.Tensor, keepdim: bool = False, eps: float = 1e-7):
    gram = x.mT @ x if x.size(-2) > x.size(-1) else x @ x.mT
    return gram.norm(dim=(-2, -1), keepdim=keepdim).sqrt().clamp_min(eps)

def _track3_soft_muon_pr291_from_operand(g: torch.Tensor):
    x = g.bfloat16()
    transposed = x.size(-2) > x.size(-1)
    if transposed:
        x = x.mT
    x = x / _track3_gram_frobenius_norm_estimate(x, keepdim=True, eps=1e-7).to(x.dtype)
    coeffs = (
        0.1091613623,
        0.07085664498,
        0.05210528973,
        0.05457295795,
        0.05011334061,
        0.03334622198,
        0.05022104481,
        0.1053727358,
        0.1187323776,
        0.1185061091,
        0.1185059576,
        0.1185059576,
    )
    a, b, c = 2.0, -1.5, 0.5
    out = torch.zeros_like(x)
    for coeff in coeffs:
        out = out + coeff * x
        gram = x @ x.mT
        basis = b * gram + c * (gram @ gram)
        x = a * x + basis @ x
    if transposed:
        out = out.mT
    return out

@torch.compile
def muon_update(grad, momentum, mu=0.95, nesterov=True):
    momentum.lerp_(grad, 1 - mu)
    operand = grad.lerp_(momentum, mu) if nesterov else momentum
    update = zeropower_via_newtonschulz5(operand)
    update *= max(1, grad.size(-2) / grad.size(-1))**0.5
    if TRACK3_SOFT_MUON:
        soft_update = _track3_soft_muon_pr291_from_operand(operand)
        soft_update *= max(1, grad.size(-2) / grad.size(-1))**0.5
        if TRACK3_SOFT_MUON_NORM_RESTORE:
            soft_update = soft_update * update.float().norm().div(soft_update.float().norm().clamp_min(1e-12))
        update = update + TRACK3_SOFT_MUON_BLEND * (soft_update - update)
    return update
""" + LOCOM_HELPERS,
            1,
        )
    else:
        text = replace_exact(
            text,
            "\nclass Muon(torch.optim.Optimizer):\n",
            "\n" + LOCOM_HELPERS + "\nclass Muon(torch.optim.Optimizer):\n",
        )
    if "                    update = muon_update(p.grad, state[\"momentum\"], mu=group[\"mu\"])\n" in text:
        text = replace_exact(
            text,
            "                    update = muon_update(p.grad, state[\"momentum\"], mu=group[\"mu\"])\n",
            "                    update = muon_update(p.grad, state[\"momentum\"], mu=group[\"mu\"])\n"
            "                    state[\"last_update_norm\"] = update.float().norm()\n",
        )
    if (
        "                    p.mul_(1 - group[\"lr\"] * group[\"weight_decay\"])\n"
        "                    p.add_(update, alpha=-group[\"lr\"])\n"
    ) in text:
        text = replace_exact(
            text,
            "                    p.mul_(1 - group[\"lr\"] * group[\"weight_decay\"])\n"
            "                    p.add_(update, alpha=-group[\"lr\"])\n",
            "                    p.mul_(1 - group[\"lr\"] * group[\"weight_decay\"])\n"
            "                    p.add_(update, alpha=-group[\"lr\"])\n"
            "                    _locom_apply_owned_param_(p, update, group[\"lr\"])\n",
        )
    else:
        text = replace_exact(
            text,
            "                    p.add_(update, alpha=-group[\"lr\"])\n",
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
            "    model.compile(dynamic=False)\n"
            "compiled_model = model\n",
        )
    else:
        text = replace_exact(
            text,
            "model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()\nmodel.compile(dynamic=False)\n",
            "model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()\n"
            "if not LOCO_M_ENABLED or _env_flag(\"TRACK3_LOCOM_COMPILE\", \"0\"):\n"
            "    model.compile(dynamic=False)\n"
            "compiled_model = model\n",
        )
    text = replace_exact(
        text,
        'print0(f"Running PyTorch {torch.version.__version__} compiled for CUDA {torch.version.cuda}"',
        f'print0("Track3 LocoProp-M generated run: source={source_label} train_steps={train_steps}")\n'
        'print0(f"LocoM enabled={LOCO_M_ENABLED} layers={LOCO_M_LAYERS_SPEC} steps={LOCO_M_LOCAL_STEPS} sample_tokens={LOCO_M_SAMPLE_TOKENS} gather={LOCO_M_GATHER_SAMPLES} accum={LOCO_M_ACCUM_SAMPLES} micro_sample_tokens={LOCO_M_MICRO_SAMPLE_TOKENS} local_opt={LOCO_M_LOCAL_OPT} lr_decay={LOCO_M_LOCAL_LR_DECAY} rms_beta1={LOCO_M_RMS_BETA1} rms_beta2={LOCO_M_RMS_BETA2} rms_eps={LOCO_M_RMS_EPS} inner_lr={LOCO_M_INNER_LR} target_gamma={LOCO_M_TARGET_GAMMA} prox={LOCO_M_PROX} alpha={LOCO_M_ALPHA} norm_to_base={LOCO_M_NORM_TO_BASE} norm_cap={LOCO_M_NORM_CAP} start_step={LOCO_M_START_STEP} end_step={LOCO_M_END_STEP} interval={LOCO_M_INTERVAL} target_loss={TRACK3_TARGET_LOSS} seed_base={TRACK3_SEED_BASE} seed_offset={TRACK3_SEED_OFFSET} cooldown_frac={TRACK3_COOLDOWN_FRAC} lr_schedule={TRACK3_LR_SCHEDULE} lr_power={TRACK3_LR_POWER} lr_schedule_steps={TRACK3_LR_SCHEDULE_STEPS} soft_muon={TRACK3_SOFT_MUON} soft_blend={TRACK3_SOFT_MUON_BLEND} soft_norm_restore={TRACK3_SOFT_MUON_NORM_RESTORE} resume_checkpoint={TRACK3_RESUME_CHECKPOINT}")\n'
        'print0(f"Running PyTorch {torch.version.__version__} compiled for CUDA {torch.version.cuda}"',
    )
    text = replace_exact(
        text,
        "for _ in range(num_trials):\n",
        "for trial_idx in range(num_trials):\n"
        "    track3_trial_seed = TRACK3_SEED_BASE + TRACK3_SEED_OFFSET + trial_idx\n"
        "    torch.manual_seed(track3_trial_seed)\n"
        "    torch.cuda.manual_seed_all(track3_trial_seed)\n"
        "    print0(f\"track3_trial_seed={track3_trial_seed} trial={trial_idx}\", console=True)\n",
    )
    if "    train_steps = 3350\n" in text:
        text = replace_exact(
            text,
            "    train_steps = 3350\n",
            f"    train_steps = {train_steps}  # generated by tools/make_track3_locoprop_m.py\n",
        )
    elif "    train_steps = 3300\n" in text:
        text = replace_exact(
            text,
            "    train_steps = 3300\n",
            f"    train_steps = {train_steps}  # generated by tools/make_track3_locoprop_m.py\n",
        )
    elif "train_steps = FINAL_TRAIN_STEPS\n" in text:
        text = replace_exact(
            text,
            "train_steps = FINAL_TRAIN_STEPS\n",
            f"train_steps = {train_steps}  # generated by tools/make_track3_locoprop_m.py\n",
        )
    else:
        text, count = re.subn(
            r"(?m)^train_steps = \d+\s*$",
            f"train_steps = {train_steps}  # generated by tools/make_track3_locoprop_m.py",
            text,
            count=1,
        )
        if count != 1:
            raise RuntimeError("train_steps pattern not found")
    text = replace_exact(
        text,
        "mbs = 64\n",
        "mbs = int(os.environ.get(\"TRACK3_MBS\", \"64\"))\n",
    )
    text = replace_exact(
        text,
        "    def set_hparams(step, cooldown_frac=0.7):\n",
        "    def _track3_pr287_lr(step, initial_lr, power_c):\n"
        "        schedule_steps = TRACK3_LR_SCHEDULE_STEPS if TRACK3_LR_SCHEDULE_STEPS > 0 else train_steps\n"
        "        downward_lr = power_c * max(0.0, schedule_steps - step) ** TRACK3_LR_POWER\n"
        "        return min(initial_lr, downward_lr)\n\n"
        "    def set_hparams(step, cooldown_frac=TRACK3_COOLDOWN_FRAC):\n",
    )
    text = replace_exact(
        text,
        "        progress = step / train_steps\n",
        "        if TRACK3_LR_SCHEDULE == \"pr287\":\n"
        "            for opt in optimizers:\n"
        "                for group in opt.param_groups:\n"
        "                    group[\"lr\"] = _track3_pr287_lr(step, group[\"initial_lr\"], group[\"power_c\"])\n"
        "            return\n"
        "        progress = step / train_steps\n",
    )
    text = replace_exact(
        text,
        "        else:\n            eta = (1 - progress) / cooldown_frac\n",
        "        else:\n"
        "            eta = (1 - progress) / cooldown_frac\n"
        "            if TRACK3_LR_SCHEDULE == \"power\":\n"
        "                eta = eta ** TRACK3_LR_POWER\n",
    )
    if "        val_step_freq = 125 if step / train_steps < 0.9 else 25\n" in text:
        text = replace_exact(
            text,
            "        val_step_freq = 125 if step / train_steps < 0.9 else 25\n",
            "        val_step_freq = int(os.environ.get(\"SCREEN_VAL_EVERY\", \"125\")) if step / train_steps < 0.9 else 25\n",
        )
    else:
        text = replace_exact(
            text,
            "val_regular_interval = 125\n",
            "val_regular_interval = int(os.environ.get(\"SCREEN_VAL_EVERY\", \"125\"))\n",
        )
    text = text.replace(
        "            step_avg = time_since_last_val / (step - last_val_step) if step > 0 else float(\"nan\")\n",
        "            step_avg = time_since_last_val / (step - last_val_step) if step > last_val_step else float(\"nan\")\n",
        1,
    )
    text = replace_exact(
        text,
        "    train_loader = distributed_data_generator(\"data/fineweb10B/fineweb_train_*.bin\", batch_size)\n",
        "    train_loader = distributed_data_generator(\"data/fineweb10B/fineweb_train_*.bin\", batch_size)\n"
        "    start_step = maybe_load_track3_checkpoint(model, optimizers)\n"
        "    if start_step > 0 and TRACK3_RESUME_ADVANCE_DATA:\n"
        "        for _ in range(start_step):\n"
        "            next(train_loader)\n"
        "        print0(f\"track3_resume_advanced_data steps:{start_step}\", console=True)\n",
    )
    text = replace_exact(
        text,
        "    last_val_step = 0\n",
        "    last_val_step = start_step\n",
    )
    text = replace_exact(
        text,
        "    for step in range(train_steps + 1):\n",
        "    for step in range(start_step, train_steps + 1):\n",
    )
    target_inserted = False
    for indent in ("            ", "        "):
        old = f"{indent}model.train()\n{indent}# start the clock again\n"
        if old in text:
            text = text.replace(
                old,
                f"{indent}if maybe_save_track3_checkpoint(model, optimizers, step, train_steps, trial_idx, val_loss):\n"
                f"{indent}    break\n"
                f"{indent}if TRACK3_TARGET_LOSS > 0 and float(val_loss) <= TRACK3_TARGET_LOSS:\n"
                f"{indent}    print0(f\"target_loss_reached step:{{step}} val_loss:{{val_loss:.5f}} target:{{TRACK3_TARGET_LOSS:.5f}}\", console=True)\n"
                f"{indent}    break\n"
                f"{indent}model.train()\n{indent}# start the clock again\n",
                1,
            )
            target_inserted = True
            break
    if not target_inserted:
        raise RuntimeError("validation target-loss insertion pattern not found")
    text = replace_exact(
        text,
        "        # --------------- TRAINING SECTION -----------------\n        inputs, targets = next(train_loader)\n",
        "        # --------------- TRAINING SECTION -----------------\n"
        "        set_locoprop_m_current_step(step)\n"
        "        inputs, targets = next(train_loader)\n",
    )
    text = replace_exact(
        text,
        "                    val_loss += model(val_inputs[i*mbs:(i+1)*mbs], val_targets[i*mbs:(i+1)*mbs])\n",
        "                    val_loss += compiled_model(val_inputs[i*mbs:(i+1)*mbs], val_targets[i*mbs:(i+1)*mbs])\n",
    )
    text = replace_exact(
        text,
        "        for i in range(len(inputs) // mbs):\n"
        "            model(inputs[i*mbs:(i+1)*mbs], targets[i*mbs:(i+1)*mbs]).backward()\n",
        "        num_microbatches = len(inputs) // mbs\n"
        "        for i in range(num_microbatches):\n"
        "            capture_this_micro = LOCO_M_ACCUM_SAMPLES or i == num_microbatches - 1\n"
        "            set_locoprop_m_capture_this_micro(capture_this_micro)\n"
        "            active_model = model if (LOCO_M_ENABLED and _locom_active(step) and capture_this_micro) else compiled_model\n"
        "            active_model(inputs[i*mbs:(i+1)*mbs], targets[i*mbs:(i+1)*mbs]).backward()\n"
        "        set_locoprop_m_capture_this_micro(False)\n",
    )
    step_block_inserted = False
    for indent in ("        ", "    "):
        old = (
            f"{indent}set_hparams(step)\n"
            f"{indent}for opt in optimizers:\n"
            f"{indent}    opt.step()\n"
            f"{indent}model.zero_grad(set_to_none=True)\n"
        )
        if old in text:
            text = text.replace(
                old,
                f"{indent}set_hparams(step)\n"
                f"{indent}prepare_locoprop_m(model, step)\n"
                f"{indent}for opt in optimizers:\n"
                f"{indent}    opt.step()\n"
                f"{indent}flush_locoprop_m_apply_stats(step)\n"
                f"{indent}model.zero_grad(set_to_none=True)\n",
                1,
            )
            step_block_inserted = True
            break
    if not step_block_inserted:
        raise RuntimeError("optimizer step insertion pattern not found")
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
    elif (
        "    optimizer2 = Muon([p for p in model.blocks.parameters() if p.ndim >= 2],\n"
        "                      lr=0.035, weight_decay=0.025)\n"
    ) in text:
        text = replace_exact(
            text,
            "    optimizer2 = Muon([p for p in model.blocks.parameters() if p.ndim >= 2],\n"
            "                      lr=0.035, weight_decay=0.025)\n",
            "    optimizer2 = Muon([p for p in model.blocks.parameters() if p.ndim >= 2],\n"
            "                      lr=0.035, weight_decay=0.025)\n"
            "    attach_locoprop_m_optimizer(model, optimizer2)\n",
        )
    elif "optimizers = [optimizer1, optimizer2]\n" in text:
        text = replace_exact(
            text,
            "optimizers = [optimizer1, optimizer2]\n",
            "attach_locoprop_m_optimizer(model, optimizer2)\n"
            "optimizers = [optimizer1, optimizer2]\n",
        )
    else:
        raise RuntimeError("optimizer2 attach pattern not found")
    text = replace_exact(
        text,
        "    assert set(p for opt in optimizers for group in opt.param_groups\n"
        "               for p in group[\"params\"]) == set(model.parameters())\n",
        "    if TRACK3_LR_SCHEDULE == \"pr287\":\n"
        "        optimizer1.param_groups[0][\"power_c\"] = TRACK3_ADAM_EMBED_POWER_C\n"
        "        optimizer1.param_groups[1][\"power_c\"] = TRACK3_ADAM_PROJ_POWER_C\n"
        "        optimizer1.param_groups[2][\"power_c\"] = TRACK3_ADAM_OTHER_POWER_C\n"
        "        optimizer2.param_groups[0][\"power_c\"] = TRACK3_MUON_POWER_C\n"
        "    assert set(p for opt in optimizers for group in opt.param_groups\n"
        "               for p in group[\"params\"]) == set(model.parameters())\n",
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
