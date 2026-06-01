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
TRACK3_SEED_BASE = int(os.environ.get("TRACK3_SEED_BASE", "0"))
TRACK3_SEED_OFFSET = int(os.environ.get("TRACK3_SEED_OFFSET", "0"))
LOCO_M_LOG_STEPS = {
    int(x)
    for x in os.environ.get("TRACK3_LOCOM_LOG_STEPS", "0,1,2,10,50,125,250,500").split(",")
    if x.strip()
}
LOCO_M_OWNED_LAYER_SET: set[int] = set()
LOCO_M_APPLY_STATS: list[str] = []


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

class Block(nn.Module):
    def __init__(self, dim: int, layer_idx: int):
        super().__init__()
        self.attn = CausalSelfAttention(dim)
        self.mlp = MLP(dim, layer_idx)
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
        self.blocks = nn.ModuleList([Block(model_dim, i) for i in range(num_layers)])
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
                    state["last_update_norm"] = update.float().norm()
                    p.mul_(1 - group["lr"] * group["weight_decay"])
                    p.add_(update, alpha=-group["lr"])
                    _locom_apply_owned_param_(p, update, group["lr"])
                dist.all_gather(params_pad[base_i:base_i + world_size], params_pad[base_i + rank])


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
print0("Track3 LocoProp-M generated run: source=records/track_3_optimization/train_gpt_simple.py train_steps=3350")
print0(f"LocoM enabled={LOCO_M_ENABLED} layers={LOCO_M_LAYERS_SPEC} steps={LOCO_M_LOCAL_STEPS} sample_tokens={LOCO_M_SAMPLE_TOKENS} gather={LOCO_M_GATHER_SAMPLES} accum={LOCO_M_ACCUM_SAMPLES} micro_sample_tokens={LOCO_M_MICRO_SAMPLE_TOKENS} inner_lr={LOCO_M_INNER_LR} target_gamma={LOCO_M_TARGET_GAMMA} prox={LOCO_M_PROX} alpha={LOCO_M_ALPHA} norm_to_base={LOCO_M_NORM_TO_BASE} norm_cap={LOCO_M_NORM_CAP} target_loss={TRACK3_TARGET_LOSS} seed_base={TRACK3_SEED_BASE} seed_offset={TRACK3_SEED_OFFSET}")
print0(f"Running PyTorch {torch.version.__version__} compiled for CUDA {torch.version.cuda}"
       + f" on {torch.cuda.get_device_name(device)} with world_size {dist.get_world_size()}")
print0("="*100)

val_tokens = 20 * 524288
batch_size = 8 * 64 * 1024
mbs = int(os.environ.get("TRACK3_MBS", "64"))
val_inputs, val_targets = next(distributed_data_generator("data/fineweb10B/fineweb_val_*.bin", val_tokens))

model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()
if not LOCO_M_ENABLED or _env_flag("TRACK3_LOCOM_COMPILE", "0"):
    model.compile(dynamic=False)


num_trials = int(sys.argv[-1]) if len(sys.argv) > 1 else 1

for trial_idx in range(num_trials):
    track3_trial_seed = TRACK3_SEED_BASE + TRACK3_SEED_OFFSET + trial_idx
    torch.manual_seed(track3_trial_seed)
    torch.cuda.manual_seed_all(track3_trial_seed)
    print0(f"track3_trial_seed={track3_trial_seed} trial={trial_idx}", console=True)


    ########################################
    #       Init & Optim Hyperparams       #
    ########################################

    # we want to minimize this while still reaching 3.28 val loss
    train_steps = 3350  # generated by tools/make_track3_locoprop_m.py

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
    attach_locoprop_m_optimizer(model, optimizer2)
    optimizers = [optimizer1, optimizer2]
    assert set(p for opt in optimizers for group in opt.param_groups
               for p in group["params"]) == set(model.parameters())
    for opt in optimizers:
        for group in opt.param_groups:
            group["initial_lr"] = group["lr"]

    # learning rate schedule: stable then decay
    def set_hparams(step, cooldown_frac=0.7):
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
        val_step_freq = int(os.environ.get("SCREEN_VAL_EVERY", "125")) if step / train_steps < 0.9 else 25
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
            if TRACK3_TARGET_LOSS > 0 and float(val_loss) <= TRACK3_TARGET_LOSS:
                print0(f"target_loss_reached step:{step} val_loss:{val_loss:.5f} target:{TRACK3_TARGET_LOSS:.5f}", console=True)
                break
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
        # set optimization hyperparameters and take a step
        set_hparams(step)
        prepare_locoprop_m(model, step)
        for opt in optimizers:
            opt.step()
        flush_locoprop_m_apply_stats(step)
        model.zero_grad(set_to_none=True)
        approx_training_time = training_time + (time.perf_counter() - t0)
        print0(f"step:{step+1}/{train_steps} train_time:{approx_training_time:.3f}s"
               + f" step_avg:{1000*approx_training_time/(step + 1):.2f}ms", console=True, log=False)

dist.destroy_process_group()
