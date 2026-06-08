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
LOCOM_BIAS = env_bool("TRACK3_LOCOM_BIAS", True)
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
LOCOM_LOG_STEPS = parse_step_set(os.environ.get(
    "TRACK3_LOCOM_LOG_STEPS",
    "0,1,2,10,50,125,250,500,1000,1500,2000,2400,2800",
))
TRACK3_TRAIN_STEPS = env_int("TRACK3_TRAIN_STEPS", 3350)
TRACK3_COOLDOWN_FRAC = env_float("TRACK3_COOLDOWN_FRAC", 0.7)
LOCOM_APPLY_STATS: list[str] = []


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
        for module in (block.mlp.fc, block.mlp.proj):
            p = module.weight
            p._loco_corr = None
            p._loco_bias_corr = None
            p._loco_bias_param = None
            p._loco_step = -1
            p._loco_layer = -1
            p._loco_surface = ""

def locom_module(model: GPT, surface: str, layer_idx: int) -> Linear:
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
    }
    if mode not in aliases:
        raise ValueError(f"unknown TRACK3_LOCOM_MOMENTUM_MODE={LOCOM_MOMENTUM_MODE!r}")
    return aliases[mode]

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
    want_fc = "fc" in LOCOM_SURFACES
    want_proj = "proj" in LOCOM_SURFACES
    saved: list[tuple[int, Tensor, Tensor, Tensor, Tensor]] = []

    aux_inputs = inputs[:LOCOM_AUX_SEQS]
    aux_targets = targets[:LOCOM_AUX_SEQS]
    x = model.norm1(model.embed(aux_inputs))
    for layer_idx, block in enumerate(model.blocks):
        x = x + block.attn(block.norm1(x))
        mlp_in = block.norm2(x)
        pre = block.mlp.fc(mlp_in)
        post = pre.relu().square()
        proj_out = block.mlp.proj(post)
        if layer_idx in wanted:
            saved.append((layer_idx, mlp_in, pre, post, proj_out))
        x = x + proj_out

    logits = model.proj(model.norm2(x)).float()
    logits = 15 * logits * (logits.square() + 15**2).rsqrt()
    loss = F.cross_entropy(logits.view(aux_targets.numel(), -1), aux_targets.view(-1), reduction="sum")
    grad_tensors = []
    grad_keys = []
    for layer_idx, _, pre, _, proj_out in saved:
        if want_fc:
            grad_tensors.append(pre)
            grad_keys.append((layer_idx, "fc_dout"))
        if want_proj:
            grad_tensors.append(proj_out)
            grad_keys.append((layer_idx, "proj_dout"))
    grads = torch.autograd.grad(loss, grad_tensors, retain_graph=False) if grad_tensors else ()
    grad_by_layer = {
        key: grad for key, grad in zip(grad_keys, grads)
    }

    samples: list[dict[str, Tensor | int]] = []
    for layer_idx, mlp_in, pre, post, proj_out in saved:
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
        }
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
):
    if LOCOM_PROX != 0:
        grad_w = grad_w.add(W - W0, alpha=LOCOM_PROX)
        grad_b = grad_b.add(b - b0, alpha=LOCOM_PROX)

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

    W.add_(upd_w, alpha=-LOCOM_INNER_LR)
    if LOCOM_BIAS:
        b.add_(upd_b, alpha=-LOCOM_INNER_LR)

@torch.no_grad()
def prepare_locom_mlp_corrections(
    model: GPT,
    inputs: Tensor,
    targets: Tensor,
    owned_targets: tuple[tuple[str, int], ...],
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
    for surface in ("fc", "proj"):
        target_layers = [
            layer_idx for target_surface, layer_idx in owned_targets
            if target_surface == surface and layer_idx in sample_by_layer
        ]
        if not target_layers:
            continue

        if surface == "fc":
            x = torch.stack([sample_by_layer[layer_idx]["fc_x"].float() for layer_idx in target_layers])
            y0 = torch.stack([sample_by_layer[layer_idx]["fc_pre"].float() for layer_idx in target_layers])
            post0 = torch.stack([sample_by_layer[layer_idx]["fc_post"].float() for layer_idx in target_layers])
            dout = torch.stack([sample_by_layer[layer_idx]["fc_dout"].float() for layer_idx in target_layers])
            if LOCOM_MODE == "squared":
                target = y0 - LOCOM_TARGET_GAMMA * dout
            elif LOCOM_MODE == "matching":
                target = post0 - LOCOM_TARGET_GAMMA * dout
            else:
                raise ValueError(f"unknown TRACK3_LOCOM_MODE={LOCOM_MODE!r}")
        else:
            x = torch.stack([sample_by_layer[layer_idx]["proj_x"].float() for layer_idx in target_layers])
            y0 = torch.stack([sample_by_layer[layer_idx]["proj_y"].float() for layer_idx in target_layers])
            dout = torch.stack([sample_by_layer[layer_idx]["proj_dout"].float() for layer_idx in target_layers])
            target = y0 - LOCOM_TARGET_GAMMA * dout

        modules = [locom_module(model, surface, layer_idx) for layer_idx in target_layers]
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
        W = W0.clone()
        b = b0.clone()
        state = {
            "mw": torch.zeros_like(W),
            "vw": torch.zeros_like(W),
            "mb": torch.zeros_like(b),
            "vb": torch.zeros_like(b),
        }
        inv_n = 1.0 / max(x.size(1), 1)
        loss0 = None
        loss_k = None
        for local_step in range(1, LOCOM_LOCAL_STEPS + 1):
            pred = torch.bmm(x, W.transpose(1, 2)).add_(b[:, None, :])
            if surface == "fc" and LOCOM_MODE == "matching":
                err = pred.relu().square().sub_(target)
            else:
                err = pred - target
            loss_k = 0.5 * err.square().mean(dim=(1, 2))
            if loss0 is None:
                loss0 = loss_k
            grad_w = torch.bmm(err.transpose(1, 2), x).mul_(inv_n)
            grad_b = err.mean(dim=1)
            locom_inner_step(W, b, center_w, center_b, grad_w, grad_b, state, local_step)

        pred = torch.bmm(x, W.transpose(1, 2)).add_(b[:, None, :])
        if surface == "fc" and LOCOM_MODE == "matching":
            err = pred.relu().square().sub_(target)
        else:
            err = pred - target
        loss_k = 0.5 * err.square().mean(dim=(1, 2))

        corr_stack = W - W0
        bias_corr_stack = b - b0
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
            accepted = bool(torch.isfinite(corr).all()) and bool(torch.isfinite(bias_corr).all())
            if LOCOM_REQUIRE_LOSS_DECREASE:
                accepted = accepted and bool(loss_k[pos] <= loss0[pos])
            accepted = accepted and bool(cos_desc >= LOCOM_MIN_COS_DESC)
            if accepted:
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
    base_step_norm = update.float().norm().mul(lr).clamp_min(1e-12)
    scale = torch.tensor(LOCOM_ALPHA, device=corr.device, dtype=torch.float32)
    if LOCOM_NORM_CAP > 0:
        scale = torch.minimum(scale, LOCOM_NORM_CAP * base_step_norm / joint_corr_norm)

    skipped = 0
    finite = bool(torch.isfinite(corr_f).all())
    if bias_corr_f is not None:
        finite = finite and bool(torch.isfinite(bias_corr_f).all())
    if not finite or float(scale) == 0.0:
        skipped = 1
    else:
        applied_corr = corr_f.mul(float(scale))
        p.add_(applied_corr.to(p.dtype))
        p._loco_prox_velocity = applied_corr.detach().clone()
        if bias_param is not None and bias_corr_f is not None:
            applied_bias_corr = bias_corr_f.mul(float(scale))
            bias_param.add_(applied_bias_corr.to(bias_param.dtype))
            p._loco_bias_prox_velocity = applied_bias_corr.detach().clone()

    if step in LOCOM_LOG_STEPS and len(LOCOM_APPLY_STATS) < 12:
        LOCOM_APPLY_STATS.append(
            f"{surface}l{layer}:base_step={float(base_step_norm):.3e}"
            f",corr_norm={float(joint_corr_norm):.3e}"
            f",bias_corr_norm={float(bias_corr_norm):.3e}"
            f",cap={LOCOM_NORM_CAP:.3f}"
            f",mom={momentum_mode}:{LOCOM_MOMENTUM_BETA:.2f}"
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

# we begin by logging this file itself
print0(code)
print0("="*100)
print0(f"Running PyTorch {torch.version.__version__} compiled for CUDA {torch.version.cuda}"
       + f" on {torch.cuda.get_device_name(device)} with world_size {dist.get_world_size()}")
print0("="*100)

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
                       betas=(0.8, 0.95), eps=1e-10, weight_decay=0, fused=True)
    optimizer2 = Muon([p for p in model.blocks.parameters() if p.ndim >= 2],
                      lr=0.035, weight_decay=0.025)
    optimizers = [optimizer1, optimizer2]
    assert set(p for opt in optimizers for group in opt.param_groups
               for p in group["params"]) == set(model.parameters())
    for opt in optimizers:
        for group in opt.param_groups:
            group["initial_lr"] = group["lr"]

    locom_layer_set = parse_layer_set(LOCOM_LAYERS_SPEC, len(model.blocks))
    muon_params = optimizer2.param_groups[0]["params"]
    locom_weight_to_target = {}
    for layer_idx, block in enumerate(model.blocks):
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
    print0(
        f"LocoProp-M enabled={LOCOM_ENABLED} mode={LOCOM_MODE} layers={LOCOM_LAYERS_SPEC}"
        f" surfaces={','.join(sorted(LOCOM_SURFACES))}"
        f" owned_targets={owned_locom_targets} sample_tokens={LOCOM_SAMPLE_TOKENS}"
        f" aux_seqs={LOCOM_AUX_SEQS} steps={LOCOM_LOCAL_STEPS}"
        f" inner_opt={LOCOM_INNER_OPT} inner_lr={LOCOM_INNER_LR}"
        f" prox={LOCOM_PROX} gamma={LOCOM_TARGET_GAMMA}"
        f" alpha={LOCOM_ALPHA} norm_cap={LOCOM_NORM_CAP} bias={LOCOM_BIAS}"
        f" momentum_mode={locom_momentum_mode()}"
        f" momentum_beta={LOCOM_MOMENTUM_BETA}"
        f" legacy_corr_momentum={LOCOM_CORR_MOMENTUM}"
        f" active=[{LOCOM_START_STEP},{LOCOM_END_STEP}) interval={LOCOM_INTERVAL}"
        f" require_loss_decrease={LOCOM_REQUIRE_LOSS_DECREASE}"
        f" min_cos_desc={LOCOM_MIN_COS_DESC}",
        console=True,
    )

    # learning rate schedule: stable then decay
    def set_hparams(step, cooldown_frac=TRACK3_COOLDOWN_FRAC):
        progress = step / train_steps
        assert 0 <= progress < 1
        if progress < 1 - cooldown_frac:
            eta = 1.0
        else:
            eta = (1 - progress) / cooldown_frac
        for opt in optimizers:
            for group in opt.param_groups:
                group["lr"] = group["initial_lr"] * eta


    ########################################
    #        Training and Validation       #
    ########################################

    train_loader = distributed_data_generator("data/fineweb10B/fineweb_train_*.bin", batch_size)
    for p in model.parameters():
        dist.broadcast(p.detach(), 0)
    # start the clock
    training_time = 0
    last_val_step = 0
    dist.barrier()
    t0 = time.perf_counter()
    for step in range(train_steps + 1):

        # --------------- VALIDATION SECTION -----------------
        val_step_freq = 125 if step / train_steps < 0.9 else 25
        if step == train_steps or step % val_step_freq == 0:
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
            model.train()
            # start the clock again
            dist.barrier()
            t0 = time.perf_counter()

        if step == train_steps:
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
        prepare_locom_mlp_corrections(model, inputs, targets, owned_locom_targets, step)
        # set optimization hyperparameters and take a step
        set_hparams(step)
        LOCOM_APPLY_STATS.clear()
        for opt in optimizers:
            opt.step()
        sync_locom_biases(model, locom_target_owners, step)
        if step in LOCOM_LOG_STEPS and LOCOM_APPLY_STATS:
            print0("locoprop_m_apply step=" + str(step) + " " + " | ".join(LOCOM_APPLY_STATS), console=True)
        model.zero_grad(set_to_none=True)
        approx_training_time = training_time + (time.perf_counter() - t0)
        print0(f"step:{step+1}/{train_steps} train_time:{approx_training_time:.3f}s"
               + f" step_avg:{1000*approx_training_time/(step + 1):.2f}ms", console=True, log=False)

dist.destroy_process_group()
