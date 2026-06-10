"""
train_gpt_simple.py

This file descends from the [NanoGPT speedrun](https://github.com/KellerJordan/modded-nanogpt).
It was prepared as a simplified version of the speedrun for use in neural net optimization research.
"""

import os
import sys
with open(sys.argv[0]) as f:
    code = f.read() # read the code of this file ASAP, for logging
import uuid
import time
from pathlib import Path

import torch
from torch import Tensor, nn
from torch.optim import AdamW
import torch.nn.functional as F
import torch.distributed as dist


########################################
#        LocoProp-M configuration      #
########################################

def env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.lower() in ("1", "true", "yes", "on")

def env_int(name: str, default: int) -> int:
    return int(os.environ.get(name, str(default)))

def env_float(name: str, default: float) -> float:
    return float(os.environ.get(name, str(default)))

def parse_step_set(spec: str) -> frozenset[int]:
    if not spec:
        return frozenset()
    return frozenset(int(part) for part in spec.split(",") if part.strip())

def parse_linear_windows(spec: str) -> tuple[tuple[int, int, float, float], ...]:
    """Parse comma-separated start:end:value0:value1 windows."""
    windows: list[tuple[int, int, float, float]] = []
    if not spec:
        return tuple()
    for raw_part in spec.split(","):
        part = raw_part.strip()
        if not part:
            continue
        pieces = part.split(":")
        if len(pieces) != 4:
            raise ValueError(
                f"expected start:end:value0:value1 window in {spec!r}, got {part!r}"
            )
        start, end = int(pieces[0]), int(pieces[1])
        if end <= start:
            raise ValueError(f"window end must exceed start in {part!r}")
        windows.append((start, end, float(pieces[2]), float(pieces[3])))
    return tuple(windows)

def scheduled_value(
    step: int,
    default: float,
    windows: tuple[tuple[int, int, float, float], ...],
) -> float:
    value = default
    for start, end, value0, value1 in windows:
        if start <= step <= end:
            t = (step - start) / (end - start)
            value = value0 + t * (value1 - value0)
    return value

LOCOM_ENABLED = env_bool("TRACK3_LOCOM_ENABLED", True)
LOCOM_MODE = os.environ.get("TRACK3_LOCOM_MODE", "matching").lower()  # matching or squared
LOCOM_SAMPLE_TOKENS = env_int("TRACK3_LOCOM_SAMPLE_TOKENS", 1024)
LOCOM_AUX_SEQS = max(1, env_int("TRACK3_LOCOM_AUX_SEQS", 1))
LOCOM_LOCAL_STEPS = max(1, env_int("TRACK3_LOCOM_STEPS", 5))
LOCOM_INNER_LR = env_float("TRACK3_LOCOM_INNER_LR", 0.10)
LOCOM_TARGET_GAMMA = env_float("TRACK3_LOCOM_TARGET_GAMMA", 1.0)
LOCOM_PROX = env_float("TRACK3_LOCOM_PROX", 0.10)
LOCOM_ALPHA = env_float("TRACK3_LOCOM_ALPHA", 1.0)
LOCOM_NORM_CAP = env_float("TRACK3_LOCOM_NORM_CAP", 0.20)
LOCOM_NORM_CAP_WINDOWS_SPEC = os.environ.get("TRACK3_LOCOM_NORM_CAP_WINDOWS", "")
LOCOM_NORM_CAP_WINDOWS = parse_linear_windows(LOCOM_NORM_CAP_WINDOWS_SPEC)
LOCOM_BIAS = env_bool("TRACK3_LOCOM_BIAS", True)
LOCOM_DIRECT_APPLY = env_bool("TRACK3_LOCOM_DIRECT_APPLY", True)
LOCOM_SOURCE = os.environ.get("TRACK3_LOCOM_SOURCE", "grad").lower()
LOCOM_SOURCE_DAMPING = env_float("TRACK3_LOCOM_SOURCE_DAMPING", 1e-3)
LOCOM_SURFACES_SPEC = os.environ.get("TRACK3_LOCOM_SURFACES", "fc")
LOCOM_INNER_OPT = os.environ.get("TRACK3_LOCOM_INNER_OPT", "sgd").lower()
LOCOM_INNER_BETA1 = env_float("TRACK3_LOCOM_INNER_BETA1", 0.9)
LOCOM_INNER_BETA2 = env_float("TRACK3_LOCOM_INNER_BETA2", 0.99)
LOCOM_INNER_EPS = env_float("TRACK3_LOCOM_INNER_EPS", 1e-8)
LOCOM_CORR_MOMENTUM = env_float("TRACK3_LOCOM_CORR_MOMENTUM", 0.0)
LOCOM_MOMENTUM_MODE = os.environ.get("TRACK3_LOCOM_MOMENTUM_MODE", "none").lower()
LOCOM_MOMENTUM_BETA = env_float("TRACK3_LOCOM_MOMENTUM_BETA", LOCOM_CORR_MOMENTUM)
LOCOM_START_STEP = env_int("TRACK3_LOCOM_START_STEP", 0)
LOCOM_END_STEP = env_int("TRACK3_LOCOM_END_STEP", -1)
LOCOM_INTERVAL = max(1, env_int("TRACK3_LOCOM_INTERVAL", 1))
LOCOM_LAYERS_SPEC = os.environ.get("TRACK3_LOCOM_LAYERS", "all")
LOCOM_REQUIRE_LOSS_DECREASE = env_bool("TRACK3_LOCOM_REQUIRE_LOSS_DECREASE", False)
LOCOM_MIN_COS_DESC = env_float("TRACK3_LOCOM_MIN_COS_DESC", -2.0)
LOCOM_TRUE_RELU2_GRAD = env_bool("TRACK3_LOCOM_TRUE_RELU2_GRAD", False)
LOCOM_TRUST_REGION = env_bool("TRACK3_LOCOM_TRUST_REGION", False)
LOCOM_TRUST_MAX_TRIES = max(1, env_int("TRACK3_LOCOM_TRUST_MAX_TRIES", 4))
LOCOM_TRUST_PROX_MULT = env_float("TRACK3_LOCOM_TRUST_PROX_MULT", 4.0)
LOCOM_TRUST_INNER_LR_DECAY = env_float("TRACK3_LOCOM_TRUST_INNER_LR_DECAY", 0.5)
LOCOM_TRUST_CAP = env_float("TRACK3_LOCOM_TRUST_CAP", LOCOM_NORM_CAP)
LOCOM_METRIC_BETA = env_float("TRACK3_LOCOM_METRIC_BETA", 0.95)
LOCOM_METRIC_DAMPING = env_float("TRACK3_LOCOM_METRIC_DAMPING", 1e-3)
LOCOM_SOFT_POLAR_POWER = env_float("TRACK3_LOCOM_SOFT_POLAR_POWER", 0.0)
LOCOM_SOFT_POLAR_EPS = env_float("TRACK3_LOCOM_SOFT_POLAR_EPS", 1e-6)
LOCOM_MOMENTUM_BIAS_CORRECTION = env_bool("TRACK3_LOCOM_MOMENTUM_BIAS_CORRECTION", True)
LOCOM_MUON_SIDECAR_EPS = env_float("TRACK3_LOCOM_MUON_SIDECAR_EPS", 0.0)
LOCOM_MUON_SIDECAR_BETA = env_float("TRACK3_LOCOM_MUON_SIDECAR_BETA", 0.90)
LOCOM_MUON_SIDECAR_RESIDUALIZE = env_bool("TRACK3_LOCOM_MUON_SIDECAR_RESIDUALIZE", True)
LOCOM_LOG_STEPS = parse_step_set(os.environ.get(
    "TRACK3_LOCOM_LOG_STEPS",
    "0,1,2,10,50,125,250,500,1000,1500,2000,2400,2800",
))
TRACK3_TRAIN_STEPS = env_int("TRACK3_TRAIN_STEPS", 3350)
TRACK3_SCHEDULE_STEPS = env_int("TRACK3_SCHEDULE_STEPS", TRACK3_TRAIN_STEPS)
TRACK3_STOP_STEP = env_int("TRACK3_STOP_STEP", TRACK3_TRAIN_STEPS)
TRACK3_COOLDOWN_FRAC = env_float("TRACK3_COOLDOWN_FRAC", 0.7)
TRACK3_LR_MULT_WINDOWS_SPEC = os.environ.get("TRACK3_LR_MULT_WINDOWS", "")
TRACK3_LR_MULT_WINDOWS = parse_linear_windows(TRACK3_LR_MULT_WINDOWS_SPEC)
TRACK3_ABORT_ON_NONFINITE_VAL = env_bool("TRACK3_ABORT_ON_NONFINITE_VAL", True)
TRACK3_SEED = env_int("TRACK3_SEED", 0)
TRACK3_DEBUG_FINITE = env_bool("TRACK3_DEBUG_FINITE", False)
TRACK3_DEBUG_NORM_STEPS = parse_step_set(os.environ.get("TRACK3_DEBUG_NORM_STEPS", ""))
TRACK3_ADAM_FUSED = env_bool("TRACK3_ADAM_FUSED", True)
TRACK3_DEBUG_SKIP_ADAM = env_bool("TRACK3_DEBUG_SKIP_ADAM", False)
TRACK3_DEBUG_SKIP_MUON = env_bool("TRACK3_DEBUG_SKIP_MUON", False)
TRACK3_CHECKPOINT_STEPS = parse_step_set(os.environ.get("TRACK3_CHECKPOINT_STEPS", ""))
TRACK3_CHECKPOINT_DIR = os.environ.get("TRACK3_CHECKPOINT_DIR", "checkpoints/track3_locom")
TRACK3_CHECKPOINT_PREFIX = os.environ.get("TRACK3_CHECKPOINT_PREFIX", "track3_locom")
TRACK3_RESUME_CHECKPOINT = os.environ.get("TRACK3_RESUME_CHECKPOINT", "")
LOCOM_APPLY_STATS: list[str] = []

def locom_norm_cap_for_step(step: int) -> float:
    return scheduled_value(step, LOCOM_NORM_CAP, LOCOM_NORM_CAP_WINDOWS)

def track3_lr_multiplier_for_step(step: int) -> float:
    return scheduled_value(step, 1.0, TRACK3_LR_MULT_WINDOWS)


########################################
#              Dataloader              #
########################################

def _load_data_shard(file: Path):
    header = torch.from_file(str(file), False, 256, dtype=torch.int32) # header is 256 int32
    assert header[0] == 20240520, "magic number mismatch in the data .bin file"
    assert header[1] == 1, "unsupported version"
    num_tokens = int(header[2]) # number of tokens (claimed)
    with file.open("rb", buffering=0) as f:
        tokens = torch.empty(num_tokens, dtype=torch.uint16, pin_memory=True)
        f.seek(256 * 4)
        nbytes = f.readinto(tokens.numpy()) # avoid bytes->array copy
        assert nbytes == 2 * num_tokens, "number of tokens read does not match header"
    return tokens

def distributed_data_generator(filename_pattern: str, batch_size: int, seq_len=1024):
    files = sorted(Path.cwd().glob(filename_pattern))
    assert batch_size % dist.get_world_size() == 0
    local_batch_size = batch_size // dist.get_world_size()
    file_iter = iter(files)
    tokens, pos = _load_data_shard(next(file_iter)), 0
    while True:
        if pos + batch_size + 1 >= len(tokens):
            tokens, pos = _load_data_shard(next(file_iter)), 0
        buf = tokens[pos + dist.get_rank() * local_batch_size:][:local_batch_size + 1]
        inputs = buf[:-1].to(device="cuda", dtype=torch.int32, non_blocking=True)
        targets = buf[1:].to(device="cuda", dtype=torch.int64, non_blocking=True)
        pos += batch_size
        yield inputs.view(-1, seq_len), targets.view(-1, seq_len)


########################################
#             Architecture             #
########################################

class RMSNorm(nn.Module):
    def __init__(self, dim):
        super().__init__()
        self.gains = nn.Parameter(torch.ones(dim))

    def forward(self, x):
        return F.rms_norm(x, (x.size(-1),), weight=self.gains.type_as(x))

class Linear(nn.Linear):
    def __init__(self, in_features, out_features):
        super().__init__(in_features, out_features, bias=True)

    def forward(self, x):
        return F.linear(x, self.weight.type_as(x), self.bias.type_as(x))

class Rotary(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        # half-truncate RoPE (w/ base freq tuning)
        angular_freq = (1 / 1024) ** torch.linspace(0, 1, steps=dim//4, dtype=torch.float32)
        self.register_buffer("angular_freq", torch.cat([angular_freq, angular_freq.new_zeros(dim//4)]))

    def forward(self, x_BTHD: Tensor):
        pos = torch.arange(x_BTHD.size(1), dtype=torch.float32, device=x_BTHD.device)
        theta = torch.outer(pos, self.angular_freq)[None, :, None, :]
        cos, sin = theta.cos(), theta.sin()
        x1, x2 = x_BTHD.to(dtype=torch.float32).chunk(2, dim=-1)
        y1 = x1 * cos + x2 * sin
        y2 = x1 * (-sin) + x2 * cos
        return torch.cat((y1, y2), 3).type_as(x_BTHD)

class CausalSelfAttention(nn.Module):
    def __init__(self, dim: int, head_dim=128):
        super().__init__()
        self.num_heads = dim // head_dim
        self.head_dim = head_dim
        hdim = self.num_heads * self.head_dim
        self.q = Linear(dim, hdim)
        self.k = Linear(dim, hdim)
        self.v = Linear(dim, hdim)
        self.proj = Linear(hdim, dim)
        self.rotary = Rotary(head_dim)

    def forward(self, x: Tensor):
        B, T = x.size(0), x.size(1)
        q = self.q(x).view(B, T, self.num_heads, self.head_dim)
        k = self.k(x).view(B, T, self.num_heads, self.head_dim)
        v = self.v(x).view(B, T, self.num_heads, self.head_dim)
        q, k = F.rms_norm(q, (q.size(-1),)), F.rms_norm(k, (k.size(-1),))
        q, k = self.rotary(q), self.rotary(k)
        y = F.scaled_dot_product_attention(q.transpose(1, 2), k.transpose(1, 2),
                                           v.transpose(1, 2), scale=0.12, is_causal=True).transpose(1, 2)
        y = y.contiguous().view(B, T, self.num_heads * self.head_dim)
        y = self.proj(y)
        return y

class MLP(nn.Module):
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

class Block(nn.Module):
    def __init__(self, dim: int):
        super().__init__()
        self.attn = CausalSelfAttention(dim)
        self.mlp = MLP(dim)
        self.norm1 = RMSNorm(dim)
        self.norm2 = RMSNorm(dim)

    def forward(self, x: Tensor):
        x = x + self.attn(self.norm1(x))
        x = x + self.mlp(self.norm2(x))
        return x

class GPT(nn.Module):
    def __init__(self, vocab_size: int, num_layers: int, model_dim: int):
        super().__init__()
        self.embed = nn.Embedding(vocab_size, model_dim).bfloat16()
        self.blocks = nn.ModuleList([Block(model_dim) for _ in range(num_layers)])
        self.proj = Linear(model_dim, vocab_size)
        self.norm1 = RMSNorm(model_dim)
        self.norm2 = RMSNorm(model_dim)

    def forward(self, inputs: Tensor, targets: Tensor):
        x = self.norm1(self.embed(inputs))
        for block in self.blocks:
            x = block(x)
        logits = self.proj(self.norm2(x)).float()
        logits = 15 * logits * (logits.square() + 15**2).rsqrt()
        return F.cross_entropy(logits.view(targets.numel(), -1), targets.view(-1), reduction="sum")


########################################
#              Optimizer               #
########################################

def zeropower_via_newtonschulz5(G: Tensor) -> Tensor:
    assert G.ndim >= 2
    X = G.bfloat16()
    if G.size(-2) > G.size(-1):
        X = X.mT

    # Ensure spectral norm is at most 1
    X = X / (X.norm(dim=(-2, -1), keepdim=True) + 1e-7)
    # Perform the NS iterations, not optimizing for wallclock speed
    a, b, c = 2, -1.5, 0.5
    for _ in range(12):
        A = X @ X.mT
        B = b * A + c * A @ A
        X = a * X + B @ X

    if G.size(-2) > G.size(-1):
        X = X.mT
    return X

@torch.compile
def muon_update(grad, momentum, mu=0.95, nesterov=True):
    momentum.lerp_(grad, 1 - mu)
    update = grad.lerp_(momentum, mu) if nesterov else momentum
    update = zeropower_via_newtonschulz5(update)
    update *= max(1, grad.size(-2) / grad.size(-1))**0.5
    return update

@torch.compile
def muon_update_preview(grad, momentum, mu=0.95, nesterov=True):
    next_momentum = momentum.lerp(grad, 1 - mu)
    update = grad.lerp(next_momentum, mu) if nesterov else next_momentum
    update = zeropower_via_newtonschulz5(update)
    update *= max(1, grad.size(-2) / grad.size(-1))**0.5
    return update

def muon_operand_preview(grad, momentum, mu=0.95, nesterov=True):
    next_momentum = momentum.lerp(grad, 1 - mu)
    return grad.lerp(next_momentum, mu) if nesterov else next_momentum

@torch.compile
def muon_update_from_operand(operand):
    update = zeropower_via_newtonschulz5(operand)
    update *= max(1, operand.size(-2) / operand.size(-1))**0.5
    return update

class Muon(torch.optim.Optimizer):
    def __init__(self, params, lr=0.02, weight_decay=0, mu=0.95):
        assert isinstance(params, list) and len(params) >= 1 and isinstance(params[0], torch.nn.Parameter)
        params = sorted(params, key=lambda x: x.size(), reverse=True)
        defaults = dict(lr=lr, weight_decay=weight_decay, mu=mu)
        super().__init__(params, defaults)

    @torch.no_grad()
    def step(self):
        world_size = dist.get_world_size()
        rank = dist.get_rank()
        for group in self.param_groups:
            params = group["params"]
            params_pad = params + [torch.empty_like(params[-1])] * (world_size - len(params) % world_size)
            for base_i in range(0, len(params), world_size):
                if base_i + rank < len(params):
                    p = params[base_i + rank]
                    state = self.state[p]
                    if len(state) == 0:
                        state["momentum"] = torch.zeros_like(p)
                    sidecar = getattr(p, "_loco_muon_sidecar", None)
                    p._loco_muon_sidecar_scale = 0.0
                    p._loco_muon_sidecar_norm = 0.0
                    if LOCOM_MUON_SIDECAR_EPS > 0 and sidecar is not None and sidecar.shape == p.shape:
                        state["momentum"].lerp_(p.grad, 1 - group["mu"])
                        operand = p.grad.lerp(state["momentum"], group["mu"])
                        side_f = sidecar.float()
                        operand_norm = operand.float().norm().clamp_min(1e-12)
                        side_norm = side_f.norm().clamp_min(1e-12)
                        side_scale = LOCOM_MUON_SIDECAR_EPS * operand_norm / side_norm
                        if bool(torch.isfinite(side_scale)) and bool(torch.isfinite(side_f).all()):
                            operand = operand + side_f.to(operand.dtype).mul(side_scale.to(operand.dtype))
                            p._loco_muon_sidecar_scale = float(side_scale)
                            p._loco_muon_sidecar_norm = float(side_norm)
                        update = muon_update_from_operand(operand)
                    else:
                        update = muon_update(p.grad, state["momentum"], mu=group["mu"])
                    p.mul_(1 - group["lr"] * group["weight_decay"])
                    p.add_(update, alpha=-group["lr"])
                    apply_locom_correction_(p, update, group["lr"])
                dist.all_gather(params_pad[base_i:base_i + world_size], params_pad[base_i + rank])


########################################
#             LocoProp-M               #
########################################

def parse_layer_set(spec: str, num_layers: int) -> frozenset[int]:
    spec = spec.strip().lower()
    if spec in ("", "all", "*"):
        return frozenset(range(num_layers))
    layers = set()
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            lo, hi = part.split("-", 1)
            layers.update(range(int(lo), int(hi) + 1))
        else:
            layers.add(int(part))
    return frozenset(i for i in layers if 0 <= i < num_layers)

def parse_surface_set(spec: str) -> frozenset[str]:
    aliases = {
        "attn_q": "q",
        "query": "q",
        "q": "q",
        "attn_k": "k",
        "key": "k",
        "k": "k",
        "attn_v": "v",
        "value": "v",
        "v": "v",
        "attn_o": "o",
        "attn_proj": "o",
        "o": "o",
        "c_fc": "fc",
        "mlp_fc": "fc",
        "fc": "fc",
        "c_proj": "proj",
        "mlp_proj": "proj",
        "proj": "proj",
    }
    surfaces = set()
    for part in spec.lower().replace(";", ",").split(","):
        part = part.strip()
        if not part:
            continue
        if part in ("all", "*"):
            surfaces.update(("q", "k", "v", "o", "fc", "proj"))
            continue
        if part in ("attn", "all_attn"):
            surfaces.update(("q", "k", "v", "o"))
            continue
        if part in ("attn_clean", "linear_attn"):
            surfaces.update(("v", "o"))
            continue
        if part in ("mlp", "all_mlp"):
            surfaces.update(("fc", "proj"))
            continue
        if part not in aliases:
            raise ValueError(f"unknown TRACK3_LOCOM_SURFACES entry {part!r}")
        surfaces.add(aliases[part])
    return frozenset(surfaces or {"fc"})

LOCOM_SURFACES = parse_surface_set(LOCOM_SURFACES_SPEC)

def locom_active(step: int) -> bool:
    if not LOCOM_ENABLED:
        return False
    if step < LOCOM_START_STEP:
        return False
    if LOCOM_END_STEP >= 0 and step >= LOCOM_END_STEP:
        return False
    return (step - LOCOM_START_STEP) % LOCOM_INTERVAL == 0

def locom_sample_indices(num_tokens: int, sample_tokens: int, device: torch.device) -> Tensor:
    sample_tokens = min(max(sample_tokens, 1), num_tokens)
    if sample_tokens == num_tokens:
        return torch.arange(num_tokens, device=device)
    # Deterministic stride sampling avoids burning RNG state in checkpointed runs.
    return torch.linspace(0, num_tokens - 1, sample_tokens, device=device).long()

def clear_locom_corrections(model: GPT):
    for block in model.blocks:
        for module in (block.attn.q, block.attn.k, block.attn.v, block.attn.proj, block.mlp.fc, block.mlp.proj):
            p = module.weight
            p._loco_corr = None
            p._loco_bias_corr = None
            p._loco_bias_param = None
            p._loco_step = -1
            p._loco_layer = -1
            p._loco_surface = ""

def locom_module(model: GPT, surface: str, layer_idx: int) -> Linear:
    if surface == "q":
        return model.blocks[layer_idx].attn.q
    if surface == "k":
        return model.blocks[layer_idx].attn.k
    if surface == "v":
        return model.blocks[layer_idx].attn.v
    if surface == "o":
        return model.blocks[layer_idx].attn.proj
    if surface == "fc":
        return model.blocks[layer_idx].mlp.fc
    if surface == "proj":
        return model.blocks[layer_idx].mlp.proj
    raise ValueError(f"unknown LocoProp surface {surface!r}")

def locom_momentum_mode() -> str:
    mode = LOCOM_MOMENTUM_MODE
    if mode in ("", "none", "off", "0"):
        return "corr_ema" if LOCOM_CORR_MOMENTUM > 0 else "none"
    aliases = {
        "corr": "corr_ema",
        "correction": "corr_ema",
        "residual": "corr_ema",
        "corr_ema": "corr_ema",
        "prox": "prox_center",
        "center": "prox_center",
        "prox_center": "prox_center",
        "inertial_prox": "prox_center",
        "dual": "dual_residual",
        "dual_metric": "dual_residual",
        "dual_residual": "dual_residual",
        "metric_residual": "dual_residual",
    }
    if mode not in aliases:
        raise ValueError(f"unknown TRACK3_LOCOM_MOMENTUM_MODE={LOCOM_MOMENTUM_MODE!r}")
    return aliases[mode]

def locom_source_mode() -> str:
    aliases = {
        "": "grad",
        "0": "grad",
        "grad": "grad",
        "raw": "grad",
        "backprop": "grad",
        "muon": "muon_operand",
        "momentum": "muon_operand",
        "muon_momentum": "muon_operand",
        "muon_operand": "muon_operand",
        "muon_prepolar": "muon_operand",
        "prepolar": "muon_operand",
        "nesterov": "muon_operand",
        "muon_update": "muon_update",
        "polar": "muon_update",
        "postpolar": "muon_update",
    }
    if LOCOM_SOURCE not in aliases:
        raise ValueError(f"unknown TRACK3_LOCOM_SOURCE={LOCOM_SOURCE!r}")
    return aliases[LOCOM_SOURCE]

def _base_info_for_module(
    module: Linear,
    base_update_by_param: dict[int, tuple[Tensor, ...]],
) -> tuple[Tensor | None, float, Tensor | None]:
    info = base_update_by_param.get(id(module.weight))
    if info is None:
        return None, 0.0, None
    if len(info) == 2:
        base_update, base_lr = info
        return base_update, float(base_lr), None
    base_update, base_lr, base_operand = info[:3]
    return base_update, float(base_lr), base_operand

def locom_pseudo_dout_from_weight_source(
    x: Tensor,
    source_w: Tensor,
) -> Tensor:
    # Find the minimum-feature-metric output gradient D such that
    # D.T @ X / n is close to the supplied weight-space source.
    n = max(x.size(1), 1)
    gram = torch.bmm(x.transpose(1, 2), x).mul_(1.0 / n)
    eye = torch.eye(gram.size(-1), device=gram.device, dtype=gram.dtype).expand_as(gram)
    gram = gram.add(eye, alpha=LOCOM_SOURCE_DAMPING)
    coeff = torch.linalg.solve(gram, source_w.transpose(1, 2))
    return torch.bmm(x, coeff)

def maybe_override_locom_dout(
    dout: Tensor,
    x: Tensor,
    modules: list[Linear],
    base_update_by_param: dict[int, tuple[Tensor, ...]],
) -> Tensor:
    source_mode = locom_source_mode()
    if source_mode == "grad":
        return dout
    source_ws = []
    for module in modules:
        base_update, _, base_operand = _base_info_for_module(module, base_update_by_param)
        if source_mode == "muon_operand":
            source = base_operand
        elif source_mode == "muon_update":
            source = base_update
        else:
            source = None
        if source is None:
            source = module.weight.grad
        source_ws.append(source.detach().float())
    source_w = torch.stack(source_ws).to(x.device)
    return locom_pseudo_dout_from_weight_source(x, source_w)

def sync_locom_biases(model: GPT, target_owners: dict[tuple[str, int], int], step: int):
    if not locom_active(step) or not LOCOM_BIAS:
        return
    for (surface, layer_idx), owner in target_owners.items():
        dist.broadcast(locom_module(model, surface, layer_idx).bias.detach(), owner)

def locom_manual_forward_capture(
    model: GPT,
    inputs: Tensor,
    targets: Tensor,
    layers: tuple[int, ...],
) -> list[dict[str, Tensor | int]]:
    if not layers:
        return []
    wanted = set(layers)
    want_q = "q" in LOCOM_SURFACES
    want_k = "k" in LOCOM_SURFACES
    want_v = "v" in LOCOM_SURFACES
    want_o = "o" in LOCOM_SURFACES
    want_fc = "fc" in LOCOM_SURFACES
    want_proj = "proj" in LOCOM_SURFACES
    saved: list[dict[str, Tensor | int]] = []

    aux_inputs = inputs[:LOCOM_AUX_SEQS]
    aux_targets = targets[:LOCOM_AUX_SEQS]
    x = model.norm1(model.embed(aux_inputs))
    for layer_idx, block in enumerate(model.blocks):
        attn_in = block.norm1(x)
        B, T = attn_in.size(0), attn_in.size(1)
        q_raw = block.attn.q(attn_in)
        k_raw = block.attn.k(attn_in)
        q = q_raw.view(B, T, block.attn.num_heads, block.attn.head_dim)
        k = k_raw.view(B, T, block.attn.num_heads, block.attn.head_dim)
        v = block.attn.v(attn_in)
        v_heads = v.view(B, T, block.attn.num_heads, block.attn.head_dim)
        q, k = F.rms_norm(q, (q.size(-1),)), F.rms_norm(k, (k.size(-1),))
        q, k = block.attn.rotary(q), block.attn.rotary(k)
        attn_y = F.scaled_dot_product_attention(
            q.transpose(1, 2),
            k.transpose(1, 2),
            v_heads.transpose(1, 2),
            scale=0.12,
            is_causal=True,
        ).transpose(1, 2)
        attn_y = attn_y.contiguous().view(B, T, block.attn.num_heads * block.attn.head_dim)
        attn_out = block.attn.proj(attn_y)
        if layer_idx in wanted:
            saved.append({
                "layer_idx": layer_idx,
                "attn_in": attn_in,
                "q": q_raw,
                "k": k_raw,
                "v": v,
                "attn_y": attn_y,
                "attn_out": attn_out,
            })
        x = x + attn_out
        mlp_in = block.norm2(x)
        pre = block.mlp.fc(mlp_in)
        post = pre.relu().square()
        proj_out = block.mlp.proj(post)
        if layer_idx in wanted:
            saved[-1].update({
                "mlp_in": mlp_in,
                "pre": pre,
                "post": post,
                "proj_out": proj_out,
            })
        x = x + proj_out

    logits = model.proj(model.norm2(x)).float()
    logits = 15 * logits * (logits.square() + 15**2).rsqrt()
    loss = F.cross_entropy(logits.view(aux_targets.numel(), -1), aux_targets.view(-1), reduction="sum")
    grad_tensors = []
    grad_keys = []
    for item in saved:
        layer_idx = int(item["layer_idx"])
        if want_q:
            grad_tensors.append(item["q"])
            grad_keys.append((layer_idx, "q_dout"))
        if want_k:
            grad_tensors.append(item["k"])
            grad_keys.append((layer_idx, "k_dout"))
        if want_v:
            grad_tensors.append(item["v"])
            grad_keys.append((layer_idx, "v_dout"))
        if want_o:
            grad_tensors.append(item["attn_out"])
            grad_keys.append((layer_idx, "o_dout"))
        if want_fc:
            if LOCOM_MODE == "matching" and LOCOM_TRUE_RELU2_GRAD:
                grad_tensors.append(item["post"])
            else:
                grad_tensors.append(item["pre"])
            grad_keys.append((layer_idx, "fc_dout"))
        if want_proj:
            grad_tensors.append(item["proj_out"])
            grad_keys.append((layer_idx, "proj_dout"))
    grads = torch.autograd.grad(loss, grad_tensors, retain_graph=False) if grad_tensors else ()
    grad_by_layer = {
        key: grad for key, grad in zip(grad_keys, grads)
    }

    samples: list[dict[str, Tensor | int]] = []
    for item in saved:
        layer_idx = int(item["layer_idx"])
        attn_in = item["attn_in"]
        q = item["q"]
        k = item["k"]
        v = item["v"]
        attn_y = item["attn_y"]
        attn_out = item["attn_out"]
        mlp_in = item["mlp_in"]
        pre = item["pre"]
        post = item["post"]
        proj_out = item["proj_out"]
        flat_attn_in = attn_in.reshape(-1, attn_in.size(-1))
        flat_q = q.reshape(-1, q.size(-1))
        flat_k = k.reshape(-1, k.size(-1))
        flat_v = v.reshape(-1, v.size(-1))
        flat_attn_y = attn_y.reshape(-1, attn_y.size(-1))
        flat_attn_out = attn_out.reshape(-1, attn_out.size(-1))
        flat_x = mlp_in.reshape(-1, mlp_in.size(-1))
        flat_pre = pre.reshape(-1, pre.size(-1))
        flat_post = post.reshape(-1, post.size(-1))
        flat_proj_out = proj_out.reshape(-1, proj_out.size(-1))
        idx = locom_sample_indices(flat_x.size(0), LOCOM_SAMPLE_TOKENS, flat_x.device)
        sample: dict[str, Tensor | int] = {
            "layer_idx": layer_idx,
            "fc_x": flat_x.index_select(0, idx).detach(),
            "fc_pre": flat_pre.index_select(0, idx).detach(),
            "fc_post": flat_post.index_select(0, idx).detach(),
            "proj_x": flat_post.index_select(0, idx).detach(),
            "proj_y": flat_proj_out.index_select(0, idx).detach(),
            "q_x": flat_attn_in.index_select(0, idx).detach(),
            "q_y": flat_q.index_select(0, idx).detach(),
            "k_x": flat_attn_in.index_select(0, idx).detach(),
            "k_y": flat_k.index_select(0, idx).detach(),
            "v_x": flat_attn_in.index_select(0, idx).detach(),
            "v_y": flat_v.index_select(0, idx).detach(),
            "o_x": flat_attn_y.index_select(0, idx).detach(),
            "o_y": flat_attn_out.index_select(0, idx).detach(),
        }
        if want_q:
            dq = grad_by_layer[(layer_idx, "q_dout")]
            sample["q_dout"] = dq.reshape(-1, dq.size(-1)).index_select(0, idx).detach()
        if want_k:
            dk = grad_by_layer[(layer_idx, "k_dout")]
            sample["k_dout"] = dk.reshape(-1, dk.size(-1)).index_select(0, idx).detach()
        if want_v:
            dv = grad_by_layer[(layer_idx, "v_dout")]
            sample["v_dout"] = dv.reshape(-1, dv.size(-1)).index_select(0, idx).detach()
        if want_o:
            do = grad_by_layer[(layer_idx, "o_dout")]
            sample["o_dout"] = do.reshape(-1, do.size(-1)).index_select(0, idx).detach()
        if want_fc:
            dpre = grad_by_layer[(layer_idx, "fc_dout")]
            sample["fc_dout"] = dpre.reshape(-1, dpre.size(-1)).index_select(0, idx).detach()
        if want_proj:
            dproj = grad_by_layer[(layer_idx, "proj_dout")]
            sample["proj_dout"] = dproj.reshape(-1, dproj.size(-1)).index_select(0, idx).detach()
        samples.append(sample)
    return samples

def locom_inner_step(
    W: Tensor,
    b: Tensor,
    W0: Tensor,
    b0: Tensor,
    grad_w: Tensor,
    grad_b: Tensor,
    state: dict[str, Tensor],
    local_step: int,
    prox: float,
    inner_lr: float,
):
    if prox != 0:
        grad_w = grad_w.add(W - W0, alpha=prox)
        grad_b = grad_b.add(b - b0, alpha=prox)

    if LOCOM_INNER_OPT == "sgd":
        upd_w, upd_b = grad_w, grad_b
    elif LOCOM_INNER_OPT == "rmsprop":
        state["vw"].mul_(LOCOM_INNER_BETA2).addcmul_(grad_w, grad_w, value=1 - LOCOM_INNER_BETA2)
        state["vb"].mul_(LOCOM_INNER_BETA2).addcmul_(grad_b, grad_b, value=1 - LOCOM_INNER_BETA2)
        upd_w = grad_w / state["vw"].sqrt().add_(LOCOM_INNER_EPS)
        upd_b = grad_b / state["vb"].sqrt().add_(LOCOM_INNER_EPS)
    elif LOCOM_INNER_OPT == "adam":
        state["mw"].mul_(LOCOM_INNER_BETA1).add_(grad_w, alpha=1 - LOCOM_INNER_BETA1)
        state["mb"].mul_(LOCOM_INNER_BETA1).add_(grad_b, alpha=1 - LOCOM_INNER_BETA1)
        state["vw"].mul_(LOCOM_INNER_BETA2).addcmul_(grad_w, grad_w, value=1 - LOCOM_INNER_BETA2)
        state["vb"].mul_(LOCOM_INNER_BETA2).addcmul_(grad_b, grad_b, value=1 - LOCOM_INNER_BETA2)
        bc1 = 1 - LOCOM_INNER_BETA1 ** local_step
        bc2 = 1 - LOCOM_INNER_BETA2 ** local_step
        upd_w = (state["mw"] / bc1) / (state["vw"] / bc2).sqrt().add_(LOCOM_INNER_EPS)
        upd_b = (state["mb"] / bc1) / (state["vb"] / bc2).sqrt().add_(LOCOM_INNER_EPS)
    elif LOCOM_INNER_OPT == "muon":
        upd_w = zeropower_via_newtonschulz5(grad_w)
        upd_b = grad_b / grad_b.square().mean(dim=1, keepdim=True).sqrt().add_(LOCOM_INNER_EPS)
    else:
        raise ValueError(f"unknown TRACK3_LOCOM_INNER_OPT={LOCOM_INNER_OPT!r}")

    W.add_(upd_w, alpha=-inner_lr)
    if LOCOM_BIAS:
        b.add_(upd_b, alpha=-inner_lr)

def locom_soft_polar_weight(corr: Tensor) -> Tensor:
    if LOCOM_SOFT_POLAR_POWER <= 0:
        return corr
    gram = corr.T @ corr
    eye = torch.eye(gram.size(0), device=gram.device, dtype=gram.dtype)
    gram = gram.add(eye, alpha=LOCOM_SOFT_POLAR_EPS)
    evals, evecs = torch.linalg.eigh(gram)
    inv_power = evecs @ torch.diag(evals.clamp_min(LOCOM_SOFT_POLAR_EPS).pow(-LOCOM_SOFT_POLAR_POWER)) @ evecs.T
    return corr @ inv_power

@torch.no_grad()
def prepare_locom_mlp_corrections(
    model: GPT,
    inputs: Tensor,
    targets: Tensor,
    owned_targets: tuple[tuple[str, int], ...],
    base_update_by_param: dict[int, tuple[Tensor, ...]],
    step: int,
):
    clear_locom_corrections(model)
    if not locom_active(step) or not owned_targets:
        return

    layers = tuple(sorted({layer_idx for _, layer_idx in owned_targets}))
    with torch.enable_grad():
        samples = locom_manual_forward_capture(model, inputs, targets, layers)
    if not samples:
        return
    sample_by_layer = {int(sample["layer_idx"]): sample for sample in samples}

    stats = []
    for surface in ("q", "k", "v", "o", "fc", "proj"):
        target_layers = [
            layer_idx for target_surface, layer_idx in owned_targets
            if target_surface == surface and layer_idx in sample_by_layer
        ]
        if not target_layers:
            continue

        modules = [locom_module(model, surface, layer_idx) for layer_idx in target_layers]
        if surface == "fc":
            x = torch.stack([sample_by_layer[layer_idx]["fc_x"].float() for layer_idx in target_layers])
            y0 = torch.stack([sample_by_layer[layer_idx]["fc_pre"].float() for layer_idx in target_layers])
            post0 = torch.stack([sample_by_layer[layer_idx]["fc_post"].float() for layer_idx in target_layers])
            dout = torch.stack([sample_by_layer[layer_idx]["fc_dout"].float() for layer_idx in target_layers])
            dout = maybe_override_locom_dout(dout, x, modules, base_update_by_param)
            if LOCOM_MODE == "squared":
                target = y0 - LOCOM_TARGET_GAMMA * dout
            elif LOCOM_MODE == "matching":
                target = post0 - LOCOM_TARGET_GAMMA * dout
            else:
                raise ValueError(f"unknown TRACK3_LOCOM_MODE={LOCOM_MODE!r}")
        elif surface == "proj":
            x = torch.stack([sample_by_layer[layer_idx]["proj_x"].float() for layer_idx in target_layers])
            y0 = torch.stack([sample_by_layer[layer_idx]["proj_y"].float() for layer_idx in target_layers])
            dout = torch.stack([sample_by_layer[layer_idx]["proj_dout"].float() for layer_idx in target_layers])
            dout = maybe_override_locom_dout(dout, x, modules, base_update_by_param)
            target = y0 - LOCOM_TARGET_GAMMA * dout
        elif surface == "q":
            x = torch.stack([sample_by_layer[layer_idx]["q_x"].float() for layer_idx in target_layers])
            y0 = torch.stack([sample_by_layer[layer_idx]["q_y"].float() for layer_idx in target_layers])
            dout = torch.stack([sample_by_layer[layer_idx]["q_dout"].float() for layer_idx in target_layers])
            dout = maybe_override_locom_dout(dout, x, modules, base_update_by_param)
            target = y0 - LOCOM_TARGET_GAMMA * dout
        elif surface == "k":
            x = torch.stack([sample_by_layer[layer_idx]["k_x"].float() for layer_idx in target_layers])
            y0 = torch.stack([sample_by_layer[layer_idx]["k_y"].float() for layer_idx in target_layers])
            dout = torch.stack([sample_by_layer[layer_idx]["k_dout"].float() for layer_idx in target_layers])
            dout = maybe_override_locom_dout(dout, x, modules, base_update_by_param)
            target = y0 - LOCOM_TARGET_GAMMA * dout
        elif surface == "v":
            x = torch.stack([sample_by_layer[layer_idx]["v_x"].float() for layer_idx in target_layers])
            y0 = torch.stack([sample_by_layer[layer_idx]["v_y"].float() for layer_idx in target_layers])
            dout = torch.stack([sample_by_layer[layer_idx]["v_dout"].float() for layer_idx in target_layers])
            dout = maybe_override_locom_dout(dout, x, modules, base_update_by_param)
            target = y0 - LOCOM_TARGET_GAMMA * dout
        elif surface == "o":
            x = torch.stack([sample_by_layer[layer_idx]["o_x"].float() for layer_idx in target_layers])
            y0 = torch.stack([sample_by_layer[layer_idx]["o_y"].float() for layer_idx in target_layers])
            dout = torch.stack([sample_by_layer[layer_idx]["o_dout"].float() for layer_idx in target_layers])
            dout = maybe_override_locom_dout(dout, x, modules, base_update_by_param)
            target = y0 - LOCOM_TARGET_GAMMA * dout
        else:
            raise ValueError(f"unknown LocoProp surface {surface!r}")

        W0 = torch.stack([module.weight.detach().float() for module in modules])
        b0 = torch.stack([module.bias.detach().float() for module in modules])
        center_w = W0
        center_b = b0
        momentum_mode = locom_momentum_mode()
        if momentum_mode == "prox_center" and LOCOM_MOMENTUM_BETA > 0:
            center_ws = []
            center_bs = []
            for pos, module in enumerate(modules):
                w_vel = getattr(module.weight, "_loco_prox_velocity", None)
                if w_vel is None or w_vel.shape != W0[pos].shape:
                    w_vel = torch.zeros_like(W0[pos])
                center_ws.append(W0[pos] + LOCOM_MOMENTUM_BETA * w_vel)
                b_vel = getattr(module.weight, "_loco_bias_prox_velocity", None)
                if b_vel is None or b_vel.shape != b0[pos].shape:
                    b_vel = torch.zeros_like(b0[pos])
                center_bs.append(b0[pos] + LOCOM_MOMENTUM_BETA * b_vel)
            center_w = torch.stack(center_ws)
            center_b = torch.stack(center_bs)
        inv_n = 1.0 / max(x.size(1), 1)
        base_step_norms = []
        for module in modules:
            base_update, base_lr, _ = _base_info_for_module(module, base_update_by_param)
            if base_update is None:
                base_update = torch.zeros_like(module.weight)
            base_step_norms.append(base_update.float().norm().mul(base_lr))
        base_step_norms = torch.stack(base_step_norms).to(W0.device).clamp_min(0.0)
        trust_bounds = base_step_norms.mul(LOCOM_TRUST_CAP)

        candidates = [None] * len(target_layers)
        last = None
        max_tries = LOCOM_TRUST_MAX_TRIES if LOCOM_TRUST_REGION else 1
        for trust_attempt in range(max_tries):
            trust_prox = LOCOM_PROX * (LOCOM_TRUST_PROX_MULT ** trust_attempt) if LOCOM_TRUST_REGION else LOCOM_PROX
            trust_inner_lr = LOCOM_INNER_LR * (LOCOM_TRUST_INNER_LR_DECAY ** trust_attempt) if LOCOM_TRUST_REGION else LOCOM_INNER_LR
            W = W0.clone()
            b = b0.clone()
            state = {
                "mw": torch.zeros_like(W),
                "vw": torch.zeros_like(W),
                "mb": torch.zeros_like(b),
                "vb": torch.zeros_like(b),
            }
            loss0 = None
            loss_k = None
            for local_step in range(1, LOCOM_LOCAL_STEPS + 1):
                pred = torch.bmm(x, W.transpose(1, 2)).add_(b[:, None, :])
                if surface == "fc" and LOCOM_MODE == "matching":
                    relu_pred = pred.relu()
                    err = relu_pred.square().sub_(target)
                    grad_signal = err * (2.0 * relu_pred) if LOCOM_TRUE_RELU2_GRAD else err
                else:
                    err = pred - target
                    grad_signal = err
                loss_k = 0.5 * err.square().mean(dim=(1, 2))
                if loss0 is None:
                    loss0 = loss_k
                grad_w = torch.bmm(grad_signal.transpose(1, 2), x).mul_(inv_n)
                grad_b = grad_signal.mean(dim=1)
                locom_inner_step(
                    W,
                    b,
                    center_w,
                    center_b,
                    grad_w,
                    grad_b,
                    state,
                    local_step,
                    trust_prox,
                    trust_inner_lr,
                )

            pred = torch.bmm(x, W.transpose(1, 2)).add_(b[:, None, :])
            if surface == "fc" and LOCOM_MODE == "matching":
                err = pred.relu().square().sub_(target)
            else:
                err = pred - target
            loss_k = 0.5 * err.square().mean(dim=(1, 2))
            corr_stack = W - W0
            bias_corr_stack = b - b0
            joint_norms = (corr_stack.flatten(1).norm(dim=1).square() + bias_corr_stack.norm(dim=1).square()).sqrt()
            finite = torch.isfinite(joint_norms) & torch.isfinite(loss_k)
            trust_ok = finite
            if LOCOM_TRUST_REGION:
                trust_ok = trust_ok & (trust_bounds > 0) & (joint_norms <= trust_bounds.clamp_min(1e-12) * 1.001)
            last = (W, b, loss0, loss_k, corr_stack, bias_corr_stack, joint_norms, trust_ok, trust_attempt, trust_prox, trust_inner_lr)
            for pos in range(len(target_layers)):
                if candidates[pos] is None and bool(trust_ok[pos]):
                    candidates[pos] = (
                        W[pos].detach().clone(),
                        b[pos].detach().clone(),
                        loss0[pos].detach().clone(),
                        loss_k[pos].detach().clone(),
                        corr_stack[pos].detach().clone(),
                        bias_corr_stack[pos].detach().clone(),
                        joint_norms[pos].detach().clone(),
                        trust_ok[pos].detach().clone(),
                        trust_attempt,
                        trust_prox,
                        trust_inner_lr,
                    )
            if all(candidate is not None for candidate in candidates):
                break

        assert last is not None
        last_W, last_b, last_loss0, last_loss_k, last_corr_stack, last_bias_corr_stack, last_joint_norms, last_trust_ok, last_attempt, last_prox, last_inner_lr = last
        for pos, candidate in enumerate(candidates):
            if candidate is None:
                candidates[pos] = (
                    last_W[pos].detach().clone(),
                    last_b[pos].detach().clone(),
                    last_loss0[pos].detach().clone(),
                    last_loss_k[pos].detach().clone(),
                    last_corr_stack[pos].detach().clone(),
                    last_bias_corr_stack[pos].detach().clone(),
                    last_joint_norms[pos].detach().clone(),
                    last_trust_ok[pos].detach().clone(),
                    last_attempt,
                    last_prox,
                    last_inner_lr,
                )

        W = torch.stack([candidate[0] for candidate in candidates])
        b = torch.stack([candidate[1] for candidate in candidates])
        loss0 = torch.stack([candidate[2] for candidate in candidates])
        loss_k = torch.stack([candidate[3] for candidate in candidates])
        corr_stack = torch.stack([candidate[4] for candidate in candidates])
        bias_corr_stack = torch.stack([candidate[5] for candidate in candidates])
        joint_norms = torch.stack([candidate[6] for candidate in candidates])
        trust_ok = torch.stack([candidate[7] for candidate in candidates])
        trust_attempts = [int(candidate[8]) for candidate in candidates]
        trust_proxes = [float(candidate[9]) for candidate in candidates]
        trust_inner_lrs = [float(candidate[10]) for candidate in candidates]

        raw_corr_stack = corr_stack
        raw_bias_corr_stack = bias_corr_stack
        norm_cap = locom_norm_cap_for_step(step)
        dual_state_candidates = [None] * len(target_layers)
        dual_decode_scales = [1.0] * len(target_layers)
        dual_pre_norms = [0.0] * len(target_layers)
        if momentum_mode == "dual_residual" and surface == "fc":
            decoded_corrs = []
            decoded_biases = []
            for pos, module in enumerate(modules):
                p = module.weight
                x_i = x[pos]
                if LOCOM_BIAS:
                    ones = torch.ones(x_i.size(0), 1, device=x_i.device, dtype=x_i.dtype)
                    metric_x = torch.cat([x_i, ones], dim=1)
                    delta_metric = torch.cat([raw_corr_stack[pos], raw_bias_corr_stack[pos][:, None]], dim=1)
                else:
                    metric_x = x_i
                    delta_metric = raw_corr_stack[pos]
                P_batch = metric_x.T @ metric_x
                P_batch.mul_(1.0 / max(metric_x.size(0), 1))
                P_batch.diagonal().add_(LOCOM_METRIC_DAMPING + trust_proxes[pos])
                prev_P_ema = getattr(p, "_loco_metric_ema", None)
                if prev_P_ema is None or prev_P_ema.shape != P_batch.shape:
                    P_ema = P_batch.detach().clone()
                else:
                    P_ema = prev_P_ema.float().mul(LOCOM_METRIC_BETA).add(P_batch, alpha=1 - LOCOM_METRIC_BETA)

                q = -(delta_metric @ P_batch)
                prev_mom = getattr(p, "_loco_dual_momentum", None)
                if prev_mom is None or prev_mom.shape != q.shape:
                    prev_mom = torch.zeros_like(q)
                mom = prev_mom.float().mul(LOCOM_MOMENTUM_BETA).add(q, alpha=1 - LOCOM_MOMENTUM_BETA)
                dual_step = int(getattr(p, "_loco_dual_step", 0)) + 1
                mom_decode = mom
                if LOCOM_MOMENTUM_BIAS_CORRECTION and LOCOM_MOMENTUM_BETA > 0:
                    mom_decode = mom / max(1 - LOCOM_MOMENTUM_BETA ** dual_step, 1e-12)
                decoded_aug = -torch.linalg.solve(P_ema, mom_decode.T).T
                if LOCOM_BIAS:
                    decoded_weight = locom_soft_polar_weight(decoded_aug[:, :-1])
                    decoded_aug = torch.cat([decoded_weight, decoded_aug[:, -1:]], dim=1)
                    decoded_joint_norm = (
                        decoded_aug[:, :-1].norm().square() + decoded_aug[:, -1].norm().square()
                    ).sqrt().clamp_min(1e-12)
                else:
                    decoded_aug = locom_soft_polar_weight(decoded_aug)
                    decoded_joint_norm = decoded_aug.norm().clamp_min(1e-12)
                dual_pre_norms[pos] = float(decoded_joint_norm)
                dual_bound = base_step_norms[pos].mul(norm_cap)
                dual_scale = min(1.0, float(dual_bound / decoded_joint_norm)) if float(dual_bound) > 0 else 0.0
                dual_decode_scales[pos] = dual_scale
                if dual_scale < 1.0:
                    decoded_aug = decoded_aug.mul(dual_scale)
                    mom = mom.mul(dual_scale)
                if LOCOM_BIAS:
                    decoded_corrs.append(decoded_aug[:, :-1])
                    decoded_biases.append(decoded_aug[:, -1])
                else:
                    decoded_corrs.append(decoded_aug)
                    decoded_biases.append(torch.zeros_like(raw_bias_corr_stack[pos]))
                dual_state_candidates[pos] = (
                    P_ema.detach().clone(),
                    mom.detach().clone(),
                    dual_step,
                )
            corr_stack = torch.stack(decoded_corrs)
            bias_corr_stack = torch.stack(decoded_biases)
        for pos, layer_idx in enumerate(target_layers):
            module = modules[pos]
            p = module.weight
            b_param = module.bias
            corr = corr_stack[pos]
            bias_corr = bias_corr_stack[pos] if LOCOM_BIAS else torch.zeros_like(b0[pos])
            corr_norm = corr.norm()
            bias_corr_norm = bias_corr.norm()
            joint_corr_norm = (corr_norm.square() + bias_corr_norm.square()).sqrt().clamp_min(1e-12)
            grad = p.grad.float() if p.grad is not None else torch.zeros_like(corr)
            bias_grad = b_param.grad.float() if b_param.grad is not None else torch.zeros_like(bias_corr)
            desc = -grad
            bias_desc = -bias_grad
            desc_norm = (desc.norm().square() + bias_desc.norm().square()).sqrt().clamp_min(1e-12)
            cos_num = corr.flatten().dot(desc.flatten()) + bias_corr.flatten().dot(bias_desc.flatten())
            cos_desc = cos_num / (joint_corr_norm * desc_norm)
            accepted = (
                bool(torch.isfinite(corr).all())
                and bool(torch.isfinite(bias_corr).all())
                and bool(torch.isfinite(joint_corr_norm))
                and bool(torch.isfinite(loss0[pos]))
                and bool(torch.isfinite(loss_k[pos]))
                and bool(torch.isfinite(cos_desc))
            )
            accepted = accepted and (not LOCOM_TRUST_REGION or bool(trust_ok[pos]))
            if LOCOM_REQUIRE_LOSS_DECREASE:
                accepted = accepted and bool(loss_k[pos] <= loss0[pos])
            accepted = accepted and bool(cos_desc >= LOCOM_MIN_COS_DESC)
            if accepted:
                dual_state = dual_state_candidates[pos]
                if dual_state is not None:
                    p._loco_metric_ema = dual_state[0]
                    p._loco_dual_momentum = dual_state[1]
                    p._loco_dual_step = dual_state[2]
                p._loco_corr = corr.to(p.dtype)
                if LOCOM_BIAS:
                    p._loco_bias_corr = bias_corr.to(b_param.dtype)
                    p._loco_bias_param = b_param
                p._loco_step = step
                p._loco_layer = layer_idx
                p._loco_surface = surface
            if step in LOCOM_LOG_STEPS:
                stats.append(
                    f"{surface}l{layer_idx}:loss0={float(loss0[pos]):.3e}"
                    f",lossK={float(loss_k[pos]):.3e}"
                    f",corr_norm={float(joint_corr_norm):.3e}"
                    f",bias_corr_norm={float(bias_corr_norm):.3e}"
                    f",raw_corr_norm={float(joint_norms[pos]):.3e}"
                    f",base_step={float(base_step_norms[pos]):.3e}"
                    f",trust_ratio={float(joint_norms[pos] / trust_bounds[pos].clamp_min(1e-12)):.3e}"
                    f",trust_try={trust_attempts[pos]}"
                    f",trust_prox={trust_proxes[pos]:.3e}"
                    f",trust_inner_lr={trust_inner_lrs[pos]:.3e}"
                    f",dual_pre_norm={dual_pre_norms[pos]:.3e}"
                    f",dual_scale={dual_decode_scales[pos]:.3e}"
                    f",cos_desc={float(cos_desc):.3e}"
                    f",accepted={int(accepted)}"
                )
    if step in LOCOM_LOG_STEPS and stats:
        print0("locoprop_m_prepare step=" + str(step) + " " + " | ".join(stats), console=True)

@torch.no_grad()
def apply_locom_correction_(p: nn.Parameter, update: Tensor, lr: float):
    corr = getattr(p, "_loco_corr", None)
    if corr is None:
        return

    base_step_norm = update.float().norm().mul(lr).clamp_min(1e-12)
    p._loco_prev_base_step_norm = base_step_norm.detach().clone()
    step = getattr(p, "_loco_step", -1)
    layer = getattr(p, "_loco_layer", -1)
    surface = getattr(p, "_loco_surface", "")
    bias_corr = getattr(p, "_loco_bias_corr", None)
    bias_param = getattr(p, "_loco_bias_param", None)
    corr_f = corr.float()
    bias_corr_f = None if bias_corr is None else bias_corr.float()
    momentum_mode = locom_momentum_mode()
    if momentum_mode == "corr_ema" and LOCOM_MOMENTUM_BETA > 0:
        mom = getattr(p, "_loco_corr_momentum", None)
        if mom is None or mom.shape != corr_f.shape:
            mom = torch.zeros_like(corr_f)
        mom.mul_(LOCOM_MOMENTUM_BETA).add_(corr_f, alpha=1 - LOCOM_MOMENTUM_BETA)
        p._loco_corr_momentum = mom
        corr_f = mom
        if bias_corr_f is not None:
            bias_mom = getattr(p, "_loco_bias_corr_momentum", None)
            if bias_mom is None or bias_mom.shape != bias_corr_f.shape:
                bias_mom = torch.zeros_like(bias_corr_f)
            bias_mom.mul_(LOCOM_MOMENTUM_BETA).add_(bias_corr_f, alpha=1 - LOCOM_MOMENTUM_BETA)
            p._loco_bias_corr_momentum = bias_mom
            bias_corr_f = bias_mom
    corr_norm = corr_f.norm()
    bias_corr_norm = torch.zeros((), device=corr.device, dtype=torch.float32)
    if bias_corr_f is not None:
        bias_corr_norm = bias_corr_f.norm()
    joint_corr_norm = (corr_norm.square() + bias_corr_norm.square()).sqrt().clamp_min(1e-12)
    scale = torch.tensor(LOCOM_ALPHA, device=corr.device, dtype=torch.float32)
    norm_cap = locom_norm_cap_for_step(step)
    if norm_cap > 0:
        scale = torch.minimum(scale, norm_cap * base_step_norm / joint_corr_norm)

    skipped = 0
    sidecar_scale = 0.0
    sidecar_norm = 0.0
    finite = bool(torch.isfinite(corr_f).all()) and bool(torch.isfinite(joint_corr_norm))
    if bias_corr_f is not None:
        finite = finite and bool(torch.isfinite(bias_corr_f).all())
    finite = finite and bool(torch.isfinite(scale))
    if not finite or float(scale) == 0.0:
        skipped = 1
    else:
        applied_corr = corr_f.mul(float(scale))
        if LOCOM_MUON_SIDECAR_EPS > 0:
            side_update = -applied_corr / max(float(lr), 1e-12)
            if LOCOM_MUON_SIDECAR_RESIDUALIZE:
                base = update.float()
                denom = base.flatten().dot(base.flatten()).clamp_min(1e-12)
                coeff = side_update.flatten().dot(base.flatten()) / denom
                side_update = side_update - coeff * base
            side_norm_t = side_update.norm()
            if bool(torch.isfinite(side_update).all()) and bool(torch.isfinite(side_norm_t)):
                side_mom = getattr(p, "_loco_muon_sidecar", None)
                if side_mom is None or side_mom.shape != side_update.shape:
                    side_mom = torch.zeros_like(side_update)
                side_mom.mul_(LOCOM_MUON_SIDECAR_BETA).add_(side_update, alpha=1 - LOCOM_MUON_SIDECAR_BETA)
                p._loco_muon_sidecar = side_mom.detach().clone()
                sidecar_norm = float(side_norm_t)
                sidecar_scale = 1.0
        if LOCOM_DIRECT_APPLY:
            p.add_(applied_corr.to(p.dtype))
        p._loco_prox_velocity = applied_corr.detach().clone()
        if bias_param is not None and bias_corr_f is not None:
            applied_bias_corr = bias_corr_f.mul(float(scale))
            if LOCOM_DIRECT_APPLY:
                bias_param.add_(applied_bias_corr.to(bias_param.dtype))
            p._loco_bias_prox_velocity = applied_bias_corr.detach().clone()

    if step in LOCOM_LOG_STEPS and len(LOCOM_APPLY_STATS) < 12:
        LOCOM_APPLY_STATS.append(
            f"{surface}l{layer}:base_step={float(base_step_norm):.3e}"
            f",corr_norm={float(joint_corr_norm):.3e}"
            f",bias_corr_norm={float(bias_corr_norm):.3e}"
            f",cap={norm_cap:.3f}"
            f",mom={momentum_mode}:{LOCOM_MOMENTUM_BETA:.2f}"
            f",polar_p={LOCOM_SOFT_POLAR_POWER:.2f}"
            f",source={locom_source_mode()}"
            f",direct={int(LOCOM_DIRECT_APPLY)}"
            f",sidecar_eps={LOCOM_MUON_SIDECAR_EPS:.3e}"
            f",sidecar_norm={sidecar_norm:.3e}"
            f",sidecar_updated={sidecar_scale:.0f}"
            f",scale={float(scale):.3e}"
            f",skipped={skipped}"
        )

    p._loco_corr = None
    p._loco_bias_corr = None
    p._loco_bias_param = None
    p._loco_step = -1
    p._loco_layer = -1
    p._loco_surface = ""


########################################
#                Setup                 #
########################################

# torchrun sets these env variables
device = torch.device("cuda", int(os.environ["LOCAL_RANK"]))
torch.cuda.set_device(device)
dist.init_process_group(backend="nccl", device_id=device)
dist.barrier()
# this code can be run equivalently with 1, 2, 4, or 8 gpus.
assert 8 % dist.get_world_size() == 0

# logging setup
if dist.get_rank() == 0:
    os.makedirs("logs", exist_ok=True)
    logfile = f"logs/{uuid.uuid4()}.txt"
    print(logfile)
def print0(s, console=False, log=True):
    if dist.get_rank() == 0:
        if console:
            print(s)
        if log:
            with open(logfile, "a") as f:
                print(s, file=f)

def debug_first_nonfinite(named_tensors, kind: str, step: int) -> bool:
    if not TRACK3_DEBUG_FINITE:
        return False
    for name, tensor in named_tensors:
        if tensor is None:
            continue
        finite = bool(torch.isfinite(tensor.detach()).all())
        if not finite:
            tf = tensor.detach().float()
            print0(
                f"debug_nonfinite kind={kind} step={step} name={name}"
                f" min={float(torch.nan_to_num(tf, nan=0.0, posinf=0.0, neginf=0.0).min()):.6e}"
                f" max={float(torch.nan_to_num(tf, nan=0.0, posinf=0.0, neginf=0.0).max()):.6e}"
                f" norm={float(torch.nan_to_num(tf, nan=0.0, posinf=0.0, neginf=0.0).norm()):.6e}",
                console=True,
            )
            return True
    return False

def debug_print_top_norms(named_tensors, kind: str, step: int, limit: int = 12):
    if step not in TRACK3_DEBUG_NORM_STEPS:
        return
    rows = []
    for name, tensor in named_tensors:
        tf = tensor.detach().float()
        safe = torch.nan_to_num(tf, nan=0.0, posinf=0.0, neginf=0.0)
        rows.append((float(safe.norm()), float(safe.abs().max()), name))
    rows.sort(reverse=True)
    for norm, max_abs, name in rows[:limit]:
        print0(
            f"debug_norm kind={kind} step={step} name={name}"
            f" norm={norm:.6e} max_abs={max_abs:.6e}",
            console=True,
        )

# we begin by logging this file itself
print0(code)
print0("="*100)
print0(f"Running PyTorch {torch.version.__version__} compiled for CUDA {torch.version.cuda}"
       + f" on {torch.cuda.get_device_name(device)} with world_size {dist.get_world_size()}")
print0("="*100)
torch.manual_seed(TRACK3_SEED)
torch.cuda.manual_seed_all(TRACK3_SEED)
print0(f"Using seed={TRACK3_SEED}", console=True)

val_tokens = 20 * 524288
batch_size = 8 * 64 * 1024
mbs = 64
val_inputs, val_targets = next(distributed_data_generator("data/fineweb10B/fineweb_val_*.bin", val_tokens))

model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()
model.compile(dynamic=False)


num_trials = int(sys.argv[-1]) if len(sys.argv) > 1 else 1

for _ in range(num_trials):


    ########################################
    #       Init & Optim Hyperparams       #
    ########################################

    # we want to minimize this while still reaching 3.28 val loss
    train_steps = TRACK3_TRAIN_STEPS
    schedule_steps = TRACK3_SCHEDULE_STEPS
    stop_step = min(TRACK3_STOP_STEP, train_steps)
    assert schedule_steps > 0
    assert 0 <= stop_step <= train_steps

    # initialize model parameters
    for name, p in model.named_parameters():
        w = p.data
        if name.endswith("weight"):
            if "proj" in name:
                w.zero_()
            elif "embed" in name:
                w.normal_()  # default torch init
            else:
                w.normal_(std=0.33**0.5 / w.size(-1)**0.5)  # default torch init
        elif name.endswith("bias"):
            w.zero_()
        elif name.endswith("gains"):
            w.normal_(mean=1, std=0)
        else:
            raise Exception(f"Uninitialized parameter: {name}")

    # create the optimizer(s)
    optimizer1 = AdamW([dict(params=[model.embed.weight], lr=0.3),
                        dict(params=[model.proj.weight], lr=1/320),
                        dict(params=[p for p in model.parameters() if p.ndim < 2], lr=0.01)],
                       betas=(0.8, 0.95), eps=1e-10, weight_decay=0, fused=TRACK3_ADAM_FUSED)
    optimizer2 = Muon([p for p in model.blocks.parameters() if p.ndim >= 2],
                      lr=0.035, weight_decay=0.025)
    optimizers = [optimizer1, optimizer2]
    assert set(p for opt in optimizers for group in opt.param_groups
               for p in group["params"]) == set(model.parameters())
    for opt in optimizers:
        for group in opt.param_groups:
            group["initial_lr"] = group["lr"]
    saved_checkpoint_steps: set[int] = set()
    start_step = 0

    locom_layer_set = parse_layer_set(LOCOM_LAYERS_SPEC, len(model.blocks))
    muon_params = optimizer2.param_groups[0]["params"]
    locom_weight_to_target = {}
    for layer_idx, block in enumerate(model.blocks):
        if "q" in LOCOM_SURFACES:
            locom_weight_to_target[id(block.attn.q.weight)] = ("q", layer_idx)
        if "k" in LOCOM_SURFACES:
            locom_weight_to_target[id(block.attn.k.weight)] = ("k", layer_idx)
        if "v" in LOCOM_SURFACES:
            locom_weight_to_target[id(block.attn.v.weight)] = ("v", layer_idx)
        if "o" in LOCOM_SURFACES:
            locom_weight_to_target[id(block.attn.proj.weight)] = ("o", layer_idx)
        if "fc" in LOCOM_SURFACES:
            locom_weight_to_target[id(block.mlp.fc.weight)] = ("fc", layer_idx)
        if "proj" in LOCOM_SURFACES:
            locom_weight_to_target[id(block.mlp.proj.weight)] = ("proj", layer_idx)
    locom_target_owners = {
        locom_weight_to_target[id(p)]: idx % dist.get_world_size()
        for idx, p in enumerate(muon_params)
        if id(p) in locom_weight_to_target and locom_weight_to_target[id(p)][1] in locom_layer_set
    }
    owned_locom_targets = tuple(
        target for target, owner in sorted(locom_target_owners.items())
        if owner == dist.get_rank()
    )
    owned_locom_target_set = set(owned_locom_targets)
    print0(
        f"LocoProp-M enabled={LOCOM_ENABLED} mode={LOCOM_MODE} layers={LOCOM_LAYERS_SPEC}"
        f" surfaces={','.join(sorted(LOCOM_SURFACES))}"
        f" owned_targets={owned_locom_targets} sample_tokens={LOCOM_SAMPLE_TOKENS}"
        f" aux_seqs={LOCOM_AUX_SEQS} steps={LOCOM_LOCAL_STEPS}"
        f" inner_opt={LOCOM_INNER_OPT} inner_lr={LOCOM_INNER_LR}"
        f" prox={LOCOM_PROX} gamma={LOCOM_TARGET_GAMMA}"
        f" alpha={LOCOM_ALPHA} norm_cap={LOCOM_NORM_CAP} bias={LOCOM_BIAS}"
        f" norm_cap_windows={LOCOM_NORM_CAP_WINDOWS_SPEC or 'none'}"
        f" direct_apply={LOCOM_DIRECT_APPLY}"
        f" source={locom_source_mode()}"
        f" source_damping={LOCOM_SOURCE_DAMPING}"
        f" momentum_mode={locom_momentum_mode()}"
        f" momentum_beta={LOCOM_MOMENTUM_BETA}"
        f" muon_sidecar_eps={LOCOM_MUON_SIDECAR_EPS}"
        f" muon_sidecar_beta={LOCOM_MUON_SIDECAR_BETA}"
        f" muon_sidecar_residualize={LOCOM_MUON_SIDECAR_RESIDUALIZE}"
        f" legacy_corr_momentum={LOCOM_CORR_MOMENTUM}"
        f" active=[{LOCOM_START_STEP},{LOCOM_END_STEP}) interval={LOCOM_INTERVAL}"
        f" require_loss_decrease={LOCOM_REQUIRE_LOSS_DECREASE}"
        f" min_cos_desc={LOCOM_MIN_COS_DESC}"
        f" true_relu2_grad={LOCOM_TRUE_RELU2_GRAD}"
        f" trust_region={LOCOM_TRUST_REGION}"
        f" trust_cap={LOCOM_TRUST_CAP}"
        f" trust_max_tries={LOCOM_TRUST_MAX_TRIES}"
        f" metric_beta={LOCOM_METRIC_BETA}"
        f" metric_damping={LOCOM_METRIC_DAMPING}"
        f" soft_polar_power={LOCOM_SOFT_POLAR_POWER}"
        f" mom_bias_correction={LOCOM_MOMENTUM_BIAS_CORRECTION}"
        f" adam_fused={TRACK3_ADAM_FUSED}"
        f" debug_skip_adam={TRACK3_DEBUG_SKIP_ADAM}"
        f" debug_skip_muon={TRACK3_DEBUG_SKIP_MUON}",
        console=True,
    )
    print0(
        f"Track3 run_control train_steps={train_steps} schedule_steps={schedule_steps}"
        f" stop_step={stop_step} cooldown_frac={TRACK3_COOLDOWN_FRAC}"
        f" lr_mult_windows={TRACK3_LR_MULT_WINDOWS_SPEC or 'none'}"
        f" checkpoint_steps={sorted(TRACK3_CHECKPOINT_STEPS)}"
        f" checkpoint_dir={TRACK3_CHECKPOINT_DIR}"
        f" checkpoint_prefix={TRACK3_CHECKPOINT_PREFIX}",
        console=True,
    )

    # learning rate schedule: stable then decay
    def lr_scale_for_step(step, cooldown_frac=TRACK3_COOLDOWN_FRAC):
        progress = step / schedule_steps
        assert 0 <= progress < 1
        if progress < 1 - cooldown_frac:
            return 1.0
        return (1 - progress) / cooldown_frac

    def lr_effective_scale_for_step(step, cooldown_frac=TRACK3_COOLDOWN_FRAC):
        return lr_scale_for_step(step, cooldown_frac) * track3_lr_multiplier_for_step(step)

    def set_hparams(step, cooldown_frac=TRACK3_COOLDOWN_FRAC):
        eta = lr_effective_scale_for_step(step, cooldown_frac)
        for opt in optimizers:
            for group in opt.param_groups:
                group["lr"] = group["initial_lr"] * eta

    def maybe_save_track3_checkpoint(step: int, val_loss: Tensor | None = None):
        if step not in TRACK3_CHECKPOINT_STEPS or step in saved_checkpoint_steps:
            return
        saved_checkpoint_steps.add(step)
        dist.barrier()
        if dist.get_rank() != 0:
            return
        ckpt_dir = Path(TRACK3_CHECKPOINT_DIR)
        ckpt_dir.mkdir(parents=True, exist_ok=True)
        path = ckpt_dir / f"{TRACK3_CHECKPOINT_PREFIX}_seed{TRACK3_SEED}_step{step}.pt"
        checkpoint = {
            "model": model.state_dict(),
            "optimizers": [opt.state_dict() for opt in optimizers],
            "step": step,
            "seed": TRACK3_SEED,
            "train_steps": train_steps,
            "schedule_steps": schedule_steps,
            "cooldown_frac": TRACK3_COOLDOWN_FRAC,
            "lr_mult_windows": TRACK3_LR_MULT_WINDOWS_SPEC,
            "locoprop": {
                "enabled": LOCOM_ENABLED,
                "mode": LOCOM_MODE,
                "source": locom_source_mode(),
                "surfaces": sorted(LOCOM_SURFACES),
                "sample_tokens": LOCOM_SAMPLE_TOKENS,
                "aux_seqs": LOCOM_AUX_SEQS,
                "steps": LOCOM_LOCAL_STEPS,
                "inner_opt": LOCOM_INNER_OPT,
                "inner_lr": LOCOM_INNER_LR,
                "prox": LOCOM_PROX,
                "gamma": LOCOM_TARGET_GAMMA,
                "alpha": LOCOM_ALPHA,
                "norm_cap": LOCOM_NORM_CAP,
                "norm_cap_windows": LOCOM_NORM_CAP_WINDOWS_SPEC,
                "bias": LOCOM_BIAS,
                "direct_apply": LOCOM_DIRECT_APPLY,
            },
            "rng_state": torch.get_rng_state(),
            "cuda_rng_state_all": torch.cuda.get_rng_state_all(),
            "val_loss": float(val_loss.detach().cpu()) if val_loss is not None else None,
            "data_advance_steps": step,
        }
        torch.save(checkpoint, path)
        print0(
            f"track3_checkpoint_saved step:{step} path:{path} val_loss:{checkpoint['val_loss']}",
            console=True,
        )

    resume_data_advance_steps = 0
    if TRACK3_RESUME_CHECKPOINT:
        resume_checkpoint = torch.load(TRACK3_RESUME_CHECKPOINT, map_location="cuda")
        model.load_state_dict(resume_checkpoint["model"])
        for opt, opt_state in zip(optimizers, resume_checkpoint["optimizers"]):
            opt.load_state_dict(opt_state)
        start_step = int(resume_checkpoint["step"])
        resume_data_advance_steps = int(resume_checkpoint.get("data_advance_steps", start_step))
        if "rng_state" in resume_checkpoint:
            torch.set_rng_state(resume_checkpoint["rng_state"].cpu())
        if "cuda_rng_state_all" in resume_checkpoint:
            torch.cuda.set_rng_state_all([state.cpu() for state in resume_checkpoint["cuda_rng_state_all"]])
        print0(
            f"track3_checkpoint_loaded path:{TRACK3_RESUME_CHECKPOINT}"
            f" step:{start_step} data_advance_steps:{resume_data_advance_steps}",
            console=True,
        )


    ########################################
    #        Training and Validation       #
    ########################################

    train_loader = distributed_data_generator("data/fineweb10B/fineweb_train_*.bin", batch_size)
    for _ in range(resume_data_advance_steps):
        next(train_loader)
    for p in model.parameters():
        dist.broadcast(p.detach(), 0)
    # start the clock
    training_time = 0
    last_val_step = start_step
    dist.barrier()
    t0 = time.perf_counter()
    for step in range(start_step, stop_step + 1):

        # --------------- VALIDATION SECTION -----------------
        val_step_freq = 125 if step / train_steps < 0.9 else 25
        if step == stop_step or step % val_step_freq == 0:
            # stop the clock
            dist.barrier()
            time_since_last_val = time.perf_counter() - t0
            step_avg = time_since_last_val / (step - last_val_step) if step > 0 else float("nan")
            last_val_step = step
            training_time += time_since_last_val
            model.eval()
            val_loss = 0
            with torch.no_grad():
                assert len(val_inputs) % mbs == 0
                for i in range(len(val_inputs) // mbs):
                    val_loss += model(val_inputs[i*mbs:(i+1)*mbs], val_targets[i*mbs:(i+1)*mbs])
            dist.all_reduce(val_loss, op=dist.ReduceOp.SUM)
            val_loss /= val_tokens
            print0(f"step:{step}/{train_steps} val_loss:{val_loss:.5f} train_time:{training_time:.3f}s"
                   + f" step_avg:{1000*step_avg:.2f}ms", console=True)
            maybe_save_track3_checkpoint(step, val_loss)
            if TRACK3_ABORT_ON_NONFINITE_VAL and step > 0 and not bool(torch.isfinite(val_loss)):
                print0(f"aborting_nonfinite_val step={step} val_loss={float(val_loss)}", console=True)
                break
            model.train()
            # start the clock again
            dist.barrier()
            t0 = time.perf_counter()

        if step == stop_step:
            break

        # --------------- TRAINING SECTION -----------------
        inputs, targets = next(train_loader)
        # accumulate across microbatches in case we are running with fewer than 8 gpus
        assert len(inputs) % mbs == 0
        for i in range(len(inputs) // mbs):
            model(inputs[i*mbs:(i+1)*mbs], targets[i*mbs:(i+1)*mbs]).backward()
        for name, p in model.named_parameters():
            assert p.grad is not None, name
            dist.all_reduce(p.grad, op=dist.ReduceOp.SUM)
        debug_print_top_norms(((name, p.grad) for name, p in model.named_parameters()), "grad", step)
        if debug_first_nonfinite(((name, p.grad) for name, p in model.named_parameters()), "grad", step):
            break
        base_update_by_param: dict[int, tuple[Tensor, ...]] = {}
        if locom_active(step) and owned_locom_targets:
            eta = lr_effective_scale_for_step(step)
            params = optimizer2.param_groups[0]["params"]
            world_size = dist.get_world_size()
            rank = dist.get_rank()
            for base_i in range(0, len(params), world_size):
                if base_i + rank >= len(params):
                    continue
                p = params[base_i + rank]
                target = locom_weight_to_target.get(id(p))
                if target not in owned_locom_target_set:
                    continue
                state = optimizer2.state[p]
                momentum = state.get("momentum")
                if momentum is None:
                    momentum = torch.zeros_like(p)
                group = optimizer2.param_groups[0]
                base_operand = muon_operand_preview(p.grad, momentum, mu=group["mu"]).detach()
                base_update_by_param[id(p)] = (
                    muon_update_from_operand(base_operand).detach(),
                    group["initial_lr"] * eta,
                    base_operand,
                )
        prepare_locom_mlp_corrections(model, inputs, targets, owned_locom_targets, base_update_by_param, step)
        # set optimization hyperparameters and take a step
        set_hparams(step)
        LOCOM_APPLY_STATS.clear()
        for opt in optimizers:
            if opt is optimizer1 and TRACK3_DEBUG_SKIP_ADAM:
                continue
            if opt is optimizer2 and TRACK3_DEBUG_SKIP_MUON:
                continue
            opt.step()
        sync_locom_biases(model, locom_target_owners, step)
        debug_print_top_norms(model.named_parameters(), "param", step)
        if debug_first_nonfinite(model.named_parameters(), "param", step):
            break
        if step in LOCOM_LOG_STEPS and LOCOM_APPLY_STATS:
            print0("locoprop_m_apply step=" + str(step) + " " + " | ".join(LOCOM_APPLY_STATS), console=True)
        model.zero_grad(set_to_none=True)
        maybe_save_track3_checkpoint(step + 1)
        approx_training_time = training_time + (time.perf_counter() - t0)
        progress_steps = max(step + 1 - start_step, 1)
        print0(f"step:{step+1}/{train_steps} train_time:{approx_training_time:.3f}s"
               + f" step_avg:{1000*approx_training_time/progress_steps:.2f}ms", console=True, log=False)

dist.destroy_process_group()
