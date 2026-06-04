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
LOCO_M_NORM_TARGET = float(os.environ.get("TRACK3_LOCOM_NORM_TARGET", "0.0"))
LOCO_M_NORM_CAP = float(os.environ.get("TRACK3_LOCOM_NORM_CAP", "0.20"))
LOCO_M_NORM_CAP_WINDOWS_SPEC = os.environ.get("TRACK3_LOCOM_NORM_CAP_WINDOWS", "")
LOCO_M_ACTIVE_WINDOWS_SPEC = os.environ.get("TRACK3_LOCOM_ACTIVE_WINDOWS", "")
LOCO_M_START_STEP = int(os.environ.get("TRACK3_LOCOM_START_STEP", "0"))
LOCO_M_END_STEP = int(os.environ.get("TRACK3_LOCOM_END_STEP", "1000000000"))
LOCO_M_INTERVAL = int(os.environ.get("TRACK3_LOCOM_INTERVAL", "1"))
LOCO_M_GATHER_SAMPLES = _env_flag("TRACK3_LOCOM_GATHER_SAMPLES", "1")
LOCO_M_ACCUM_SAMPLES = _env_flag("TRACK3_LOCOM_ACCUM_SAMPLES", "0")
LOCO_M_MICRO_SAMPLE_TOKENS = int(os.environ.get("TRACK3_LOCOM_MICRO_SAMPLE_TOKENS", "32"))
LOCO_M_AUX_CAPTURE = _env_flag("TRACK3_LOCOM_AUX_CAPTURE", "0")
LOCO_M_AUX_SEQS = int(os.environ.get("TRACK3_LOCOM_AUX_SEQS", "16"))
LOCO_M_BATCHED_PREP = _env_flag("TRACK3_LOCOM_BATCHED_PREP", "0")
LOCO_M_LOCAL_OPT = os.environ.get("TRACK3_LOCOM_LOCAL_OPT", "sgd").lower()
LOCO_M_TARGET_SPACE = os.environ.get("TRACK3_LOCOM_TARGET_SPACE", "post").lower()
LOCO_M_RANDOM_CORRECTION = _env_flag("TRACK3_LOCOM_RANDOM_CORRECTION", "0") or LOCO_M_LOCAL_OPT == "random"
LOCO_M_LOCAL_LR_DECAY = _env_flag("TRACK3_LOCOM_LOCAL_LR_DECAY", "0")
LOCO_M_RMS_BETA1 = float(os.environ.get("TRACK3_LOCOM_RMS_BETA1", "0.999"))
LOCO_M_RMS_BETA2 = float(os.environ.get("TRACK3_LOCOM_RMS_BETA2", "0.9"))
LOCO_M_RMS_EPS = float(os.environ.get("TRACK3_LOCOM_RMS_EPS", "1e-5"))
LOCO_M_RMS_RESET_EACH_STEP = _env_flag("TRACK3_LOCOM_RMS_RESET_EACH_STEP", "0")
LOCO_M_REQUIRE_LOSS_DECREASE = _env_flag("TRACK3_LOCOM_REQUIRE_LOSS_DECREASE", "0")
LOCO_M_MIN_COS_DESC = float(os.environ.get("TRACK3_LOCOM_MIN_COS_DESC", "-inf"))
LOCO_M_CORRECTION_MODE = os.environ.get("TRACK3_LOCOM_CORRECTION_MODE", "normal").lower().replace("-", "_")
TRACK3_TARGET_LOSS = float(os.environ.get("TRACK3_TARGET_LOSS", "0"))
TRACK3_SEED_BASE = int(os.environ.get("TRACK3_SEED_BASE", "0"))
TRACK3_SEED_OFFSET = int(os.environ.get("TRACK3_SEED_OFFSET", "0"))
TRACK3_RESET_TRIAL_SEED = _env_flag("TRACK3_RESET_TRIAL_SEED", "1")
TRACK3_COOLDOWN_FRAC = float(os.environ.get("TRACK3_COOLDOWN_FRAC", "0.7"))
TRACK3_LR_SCHEDULE = os.environ.get("TRACK3_LR_SCHEDULE", "linear").lower()
TRACK3_LR_POWER = float(os.environ.get("TRACK3_LR_POWER", "1.0"))
TRACK3_LR_SCHEDULE_STEPS = int(os.environ.get("TRACK3_LR_SCHEDULE_STEPS", "0"))
TRACK3_LR_MIN_ETA = float(os.environ.get("TRACK3_LR_MIN_ETA", "0.0"))
TRACK3_LR_SWITCH_STEP = int(os.environ.get("TRACK3_LR_SWITCH_STEP", "-1"))
TRACK3_LR_AFTER_SWITCH = os.environ.get("TRACK3_LR_AFTER_SWITCH", "").lower()
TRACK3_LR_AFTER_SWITCH_POWER = float(os.environ.get("TRACK3_LR_AFTER_SWITCH_POWER", str(TRACK3_LR_POWER)))
TRACK3_LR_AFTER_SWITCH_STEPS = int(os.environ.get("TRACK3_LR_AFTER_SWITCH_STEPS", "0"))
TRACK3_LR_BLEND_START = int(os.environ.get("TRACK3_LR_BLEND_START", "-1"))
TRACK3_LR_BLEND_END = int(os.environ.get("TRACK3_LR_BLEND_END", "-1"))
TRACK3_LR_BLEND_TARGET = os.environ.get("TRACK3_LR_BLEND_TARGET", "").lower()
TRACK3_LR_BLEND_TARGET_POWER = float(os.environ.get("TRACK3_LR_BLEND_TARGET_POWER", str(TRACK3_LR_POWER)))
TRACK3_LR_BLEND_TARGET_STEPS = int(os.environ.get("TRACK3_LR_BLEND_TARGET_STEPS", "0"))
TRACK3_LR_BUMP_WINDOWS_SPEC = os.environ.get("TRACK3_LR_BUMP_WINDOWS", "")
TRACK3_ADAM_EMBED_POWER_C = float(os.environ.get("TRACK3_ADAM_EMBED_POWER_C", "4.976805410800738e-05"))
TRACK3_ADAM_PROJ_POWER_C = float(os.environ.get("TRACK3_ADAM_PROJ_POWER_C", "5.184172302917436e-07"))
TRACK3_ADAM_OTHER_POWER_C = float(os.environ.get("TRACK3_ADAM_OTHER_POWER_C", "1.6589351369335795e-06"))
TRACK3_MUON_POWER_C = float(os.environ.get("TRACK3_MUON_POWER_C", "3.3169534699576625e-06"))
if TRACK3_LR_SCHEDULE not in {"linear", "power", "pr287"}:
    raise ValueError("TRACK3_LR_SCHEDULE must be 'linear', 'power', or 'pr287'")
if TRACK3_LR_AFTER_SWITCH and TRACK3_LR_AFTER_SWITCH not in {"linear", "power", "pr287"}:
    raise ValueError("TRACK3_LR_AFTER_SWITCH must be empty, 'linear', 'power', or 'pr287'")
if TRACK3_LR_BLEND_TARGET and TRACK3_LR_BLEND_TARGET not in {"linear", "power", "pr287"}:
    raise ValueError("TRACK3_LR_BLEND_TARGET must be empty, 'linear', 'power', or 'pr287'")
if TRACK3_LR_BLEND_TARGET and TRACK3_LR_BLEND_END < TRACK3_LR_BLEND_START:
    raise ValueError("TRACK3_LR_BLEND_END must be >= TRACK3_LR_BLEND_START")
if LOCO_M_TARGET_SPACE not in {"post", "pre"}:
    raise ValueError("TRACK3_LOCOM_TARGET_SPACE must be 'post' or 'pre'")
if LOCO_M_CORRECTION_MODE not in {
    "normal",
    "orthogonal",
    "parallel",
    "polar",
    "softpolar",
    "orthogonal_polar",
    "orthogonal_softpolar",
    "parallel_polar",
    "parallel_softpolar",
}:
    raise ValueError(
        "TRACK3_LOCOM_CORRECTION_MODE must be one of normal, orthogonal, parallel, "
        "polar, softpolar, orthogonal_polar, orthogonal_softpolar, parallel_polar, "
        "or parallel_softpolar"
    )
TRACK3_SOFT_MUON = _env_flag("TRACK3_SOFT_MUON", "0")
TRACK3_SOFT_MUON_BLEND = float(os.environ.get("TRACK3_SOFT_MUON_BLEND", "1.0"))
TRACK3_SOFT_MUON_NORM_RESTORE = _env_flag("TRACK3_SOFT_MUON_NORM_RESTORE", "1")
TRACK3_SOFT_MUON_START_STEP = int(os.environ.get("TRACK3_SOFT_MUON_START_STEP", "-1"))
TRACK3_SOFT_MUON_END_STEP = int(os.environ.get("TRACK3_SOFT_MUON_END_STEP", "-1"))
TRACK3_SOFT_MUON_CEIL = float(os.environ.get("TRACK3_SOFT_MUON_CEIL", "1.0"))
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
TRACK3_RESUME_LOAD_OPTIMIZERS = _env_flag("TRACK3_RESUME_LOAD_OPTIMIZERS", "1")
TRACK3_CHECKPOINT_SAVED_STEPS: set[int] = set()
LOCO_M_LOG_STEPS = {
    int(x)
    for x in os.environ.get("TRACK3_LOCOM_LOG_STEPS", "0,1,2,10,50,125,250,500").split(",")
    if x.strip()
}
LOCO_M_OWNED_LAYER_SET: set[int] = set()
LOCO_M_APPLY_STATS: list[str] = []
LOCO_M_CURRENT_STEP = -1
LOCO_M_CAPTURE_THIS_MICRO = True

def _parse_step_value_windows(spec: str) -> list[tuple[int, int, float]]:
    windows: list[tuple[int, int, float]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) != 3:
            raise ValueError("TRACK3_LOCOM_NORM_CAP_WINDOWS entries must be start:end:value")
        start, end, value = int(fields[0]), int(fields[1]), float(fields[2])
        if end < start:
            raise ValueError("TRACK3_LOCOM_NORM_CAP_WINDOWS end must be >= start")
        windows.append((start, end, value))
    return windows

def _parse_step_windows(spec: str) -> list[tuple[int, int]]:
    windows: list[tuple[int, int]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) != 2:
            raise ValueError("TRACK3_LOCOM_ACTIVE_WINDOWS entries must be start:end")
        start, end = int(fields[0]), int(fields[1])
        if end < start:
            raise ValueError("TRACK3_LOCOM_ACTIVE_WINDOWS end must be >= start")
        windows.append((start, end))
    return windows

LOCO_M_NORM_CAP_WINDOWS = _parse_step_value_windows(LOCO_M_NORM_CAP_WINDOWS_SPEC)
LOCO_M_ACTIVE_WINDOWS = _parse_step_windows(LOCO_M_ACTIVE_WINDOWS_SPEC)

def _parse_lr_bump_windows(spec: str) -> list[tuple[int, int, int, int, float]]:
    windows: list[tuple[int, int, int, int, float]] = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        fields = part.split(":")
        if len(fields) != 5:
            raise ValueError("TRACK3_LR_BUMP_WINDOWS entries must be start:ramp_end:hold_end:fade_end:mult")
        start, ramp_end, hold_end, fade_end = map(int, fields[:4])
        mult = float(fields[4])
        if not (start <= ramp_end <= hold_end <= fade_end):
            raise ValueError("TRACK3_LR_BUMP_WINDOWS requires start <= ramp_end <= hold_end <= fade_end")
        windows.append((start, ramp_end, hold_end, fade_end, mult))
    return windows

TRACK3_LR_BUMP_WINDOWS = _parse_lr_bump_windows(TRACK3_LR_BUMP_WINDOWS_SPEC)

def _track3_lr_multiplier(step: int) -> float:
    multiplier = 1.0
    for start, ramp_end, hold_end, fade_end, mult in TRACK3_LR_BUMP_WINDOWS:
        if step < start or step > fade_end:
            continue
        if ramp_end <= start or step >= ramp_end:
            if step <= hold_end:
                t = 1.0
            elif fade_end <= hold_end:
                t = 0.0
            else:
                t = max(0.0, (fade_end - step) / (fade_end - hold_end))
        else:
            t = (step - start) / (ramp_end - start)
        multiplier *= 1.0 + (mult - 1.0) * t
    return multiplier

def _track3_soft_muon_blend_for_step(step: int) -> float:
    if not TRACK3_SOFT_MUON:
        return 0.0
    if TRACK3_SOFT_MUON_START_STEP < 0:
        return min(TRACK3_SOFT_MUON_CEIL, TRACK3_SOFT_MUON_BLEND)
    if step < TRACK3_SOFT_MUON_START_STEP:
        return 0.0
    if TRACK3_SOFT_MUON_END_STEP <= TRACK3_SOFT_MUON_START_STEP:
        ramp = 1.0
    else:
        ramp = (step - TRACK3_SOFT_MUON_START_STEP) / (TRACK3_SOFT_MUON_END_STEP - TRACK3_SOFT_MUON_START_STEP)
        ramp = max(0.0, min(1.0, ramp))
    return min(TRACK3_SOFT_MUON_CEIL, TRACK3_SOFT_MUON_BLEND * ramp)

def _locom_current_norm_cap(step: int) -> float:
    cap = LOCO_M_NORM_CAP
    for start, end, value in LOCO_M_NORM_CAP_WINDOWS:
        if start <= step <= end:
            cap = value
    return cap


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
        self._loco_pre = None
        self._loco_post = None
        self._loco_dpre = None
        self._loco_x_chunks = []
        self._loco_pre_chunks = []
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
            and not LOCO_M_RANDOM_CORRECTION
            and self.training
            and LOCO_M_CAPTURE_THIS_MICRO
            and self.layer_idx in LOCO_M_LAYER_SET
            and _locom_active(LOCO_M_CURRENT_STEP)
        ):
            return
        self._store_loco_sample("_loco_x", x)
        self._store_loco_sample("_loco_pre", pre)
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

def _track3_gram_frobenius_norm_estimate(x: torch.Tensor, keepdim: bool = False, eps: float = 1e-7):
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
def _track3_muon_update_soft(grad, momentum, soft_blend, mu=0.95, nesterov=True):
    momentum.lerp_(grad, 1 - mu)
    operand = grad.lerp_(momentum, mu) if nesterov else momentum
    update = zeropower_via_newtonschulz5(operand)
    update *= max(1, grad.size(-2) / grad.size(-1))**0.5
    soft_update = _track3_soft_muon_pr291_from_operand(operand)
    soft_update *= max(1, grad.size(-2) / grad.size(-1))**0.5
    if TRACK3_SOFT_MUON_NORM_RESTORE:
        soft_update = soft_update * update.float().norm().div(soft_update.float().norm().clamp_min(1e-12))
    update = update + soft_blend.to(update.dtype) * (soft_update - update)
    return update

@torch.compile
def muon_update(grad, momentum, mu=0.95, nesterov=True):
    momentum.lerp_(grad, 1 - mu)
    update = grad.lerp_(momentum, mu) if nesterov else momentum
    update = zeropower_via_newtonschulz5(update)
    update *= max(1, grad.size(-2) / grad.size(-1))**0.5
    return update

@torch.no_grad()
def _locom_active(step: int) -> bool:
    if not (LOCO_M_ENABLED and step % max(LOCO_M_INTERVAL, 1) == 0):
        return False
    if not LOCO_M_RANDOM_CORRECTION and LOCO_M_LOCAL_STEPS <= 0:
        return False
    if LOCO_M_ACTIVE_WINDOWS:
        return any(start <= step < end for start, end in LOCO_M_ACTIVE_WINDOWS)
    return step >= LOCO_M_START_STEP and step < LOCO_M_END_STEP

@torch.no_grad()
def _locom_adjust_correction_stack(corr_stack: Tensor, raw_desc: Tensor) -> tuple[Tensor, Tensor]:
    raw_corr = corr_stack
    mode = LOCO_M_CORRECTION_MODE
    if mode == "normal":
        return raw_corr, raw_corr

    corr_flat = raw_corr.flatten(1)
    desc_flat = raw_desc.flatten(1)
    desc_norm_sq = desc_flat.square().sum(dim=1).clamp_min(1e-12)
    coeff = (corr_flat * desc_flat).sum(dim=1) / desc_norm_sq
    parallel = coeff.view(coeff.shape[0], *([1] * (raw_corr.ndim - 1))) * raw_desc

    if mode.startswith("parallel"):
        adjusted = parallel
    elif mode.startswith("orthogonal"):
        adjusted = raw_corr - parallel
    else:
        adjusted = raw_corr

    if mode.endswith("softpolar"):
        adjusted = _track3_soft_muon_pr291_from_operand(adjusted.float()).float()
        adjusted *= max(1, adjusted.size(-2) / adjusted.size(-1))**0.5
    elif mode.endswith("polar"):
        adjusted = zeropower_via_newtonschulz5(adjusted.float()).float()
        adjusted *= max(1, adjusted.size(-2) / adjusted.size(-1))**0.5

    return adjusted, raw_corr

@torch.no_grad()
def _locom_adjust_correction(corr: Tensor, raw_desc: Tensor) -> tuple[Tensor, Tensor]:
    adjusted, raw = _locom_adjust_correction_stack(corr.unsqueeze(0), raw_desc.unsqueeze(0))
    return adjusted[0], raw[0]

@torch.no_grad()
def set_locoprop_m_current_step(step: int):
    global LOCO_M_CURRENT_STEP
    LOCO_M_CURRENT_STEP = step

@torch.no_grad()
def set_locoprop_m_capture_this_micro(enabled: bool):
    global LOCO_M_CAPTURE_THIS_MICRO
    LOCO_M_CAPTURE_THIS_MICRO = enabled

def _locoprop_m_active_layers(model: nn.Module) -> list[int]:
    return [
        i
        for i, _ in enumerate(model.blocks)
        if i in LOCO_M_LAYER_SET
    ]

def _locoprop_m_aux_forward_capture(model: nn.Module, inputs: Tensor, targets: Tensor, active_layers: list[int]) -> Tensor:
    active = set(active_layers)
    pre_tensors = []
    pre_layers = []

    x = model.norm1(model.embed(inputs))
    for layer_idx, block in enumerate(model.blocks):
        x = x + block.attn(block.norm1(x))
        if layer_idx in active:
            mlp = block.mlp
            mlp_in = block.norm2(x)
            pre = mlp.fc(mlp_in)
            post = pre.relu().square()
            mlp._store_loco_sample("_loco_x", mlp_in)
            mlp._store_loco_sample("_loco_pre", pre)
            mlp._store_loco_sample("_loco_post", post)
            if not LOCO_M_ACCUM_SAMPLES:
                mlp._loco_dpre = None
            mlp._loco_corr = None
            pre_layers.append(layer_idx)
            pre_tensors.append(pre)
            x = x + mlp.proj(post)
        else:
            x = x + block.mlp(block.norm2(x))

    logits = model.proj(model.norm2(x)).float()
    logits = 15 * logits * (logits.square() + 15**2).rsqrt()
    aux_loss = F.cross_entropy(logits.view(targets.numel(), -1), targets.view(-1), reduction="sum")
    if not pre_tensors:
        return aux_loss
    dpre_tensors = torch.autograd.grad(
        aux_loss,
        pre_tensors,
        retain_graph=False,
        create_graph=False,
        allow_unused=True,
    )
    for layer_idx, dpre in zip(pre_layers, dpre_tensors):
        if dpre is not None:
            model.blocks[layer_idx].mlp._store_loco_sample("_loco_dpre", dpre)
    return aux_loss

def prepare_locoprop_m_aux(model: nn.Module, inputs: Tensor, targets: Tensor, step: int):
    if not (LOCO_M_AUX_CAPTURE and _locom_active(step) and not LOCO_M_RANDOM_CORRECTION):
        return
    active_layers = _locoprop_m_active_layers(model)
    if not active_layers:
        return
    seqs = max(1, min(int(LOCO_M_AUX_SEQS), inputs.size(0)))
    aux_inputs = inputs[-seqs:].detach()
    aux_targets = targets[-seqs:].detach()
    with torch.enable_grad():
        _locoprop_m_aux_forward_capture(model, aux_inputs, aux_targets, active_layers)

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
        f"accum_samples={LOCO_M_ACCUM_SAMPLES} micro_sample_tokens={LOCO_M_MICRO_SAMPLE_TOKENS} "
        f"aux_capture={LOCO_M_AUX_CAPTURE} aux_seqs={LOCO_M_AUX_SEQS} batched_prep={LOCO_M_BATCHED_PREP}",
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
def _prepare_locoprop_m_batched(model: nn.Module, step: int, stats: list[str]) -> bool:
    if not LOCO_M_BATCHED_PREP:
        return False
    if LOCO_M_RANDOM_CORRECTION or LOCO_M_LOCAL_OPT != "sgd":
        return False
    if LOCO_M_GATHER_SAMPLES and dist.is_initialized() and dist.get_world_size() > 1:
        return False

    layers = []
    xs = []
    pre0s = []
    posts = []
    dpres = []
    weights = []
    biases = []
    raw_grads = []
    for layer_idx in sorted(LOCO_M_LAYER_SET):
        if layer_idx < 0 or layer_idx >= len(model.blocks):
            continue
        if layer_idx not in LOCO_M_OWNED_LAYER_SET:
            continue
        mlp = model.blocks[layer_idx].mlp
        x_local = _locom_take_sample(mlp, "_loco_x")
        pre_local = _locom_take_sample(mlp, "_loco_pre")
        post_local = _locom_take_sample(mlp, "_loco_post")
        dpre_local = _locom_take_sample(mlp, "_loco_dpre")
        if x_local is None or pre_local is None or post_local is None or dpre_local is None:
            continue
        if mlp.fc.weight.grad is None:
            continue
        layers.append(layer_idx)
        xs.append(x_local.float())
        pre0s.append(pre_local.float())
        posts.append(post_local.float())
        dpres.append(dpre_local.float())
        weights.append(mlp.fc.weight.detach().float())
        biases.append(mlp.fc.bias.detach().float())
        raw_grads.append(mlp.fc.weight.grad.float())

    if not layers:
        return True

    try:
        x = torch.stack(xs, dim=0)
        pre0 = torch.stack(pre0s, dim=0)
        post = torch.stack(posts, dim=0)
        dpre = torch.stack(dpres, dim=0)
        W0 = torch.stack(weights, dim=0)
        bias = torch.stack(biases, dim=0)
        raw_grad = torch.stack(raw_grads, dim=0)
    except RuntimeError as exc:
        raise RuntimeError("batched LocoProp-M prep requires same-shaped owned-layer samples") from exc

    target = pre0 - LOCO_M_TARGET_GAMMA * dpre if LOCO_M_TARGET_SPACE == "pre" else post - LOCO_M_TARGET_GAMMA * dpre
    W = W0.clone()
    inv_n = 1.0 / max(x.size(1), 1)
    loss0 = None
    loss_k = None
    for local_step in range(LOCO_M_LOCAL_STEPS):
        pred = torch.bmm(x, W.transpose(1, 2)).add_(bias[:, None, :])
        if LOCO_M_TARGET_SPACE == "pre":
            err = pred - target
        else:
            err = pred.relu().square().sub_(target)
        loss_k = 0.5 * err.square().mean(dim=(1, 2))
        if loss0 is None:
            loss0 = loss_k
        grad_w = torch.bmm(err.transpose(1, 2), x).mul_(inv_n)
        if LOCO_M_PROX != 0:
            grad_w.add_(W - W0, alpha=LOCO_M_PROX)
        local_lr = LOCO_M_INNER_LR
        if LOCO_M_LOCAL_LR_DECAY:
            local_lr *= max(1.0 - float(local_step) / max(LOCO_M_LOCAL_STEPS, 1), 0.25)
        W.add_(grad_w, alpha=-local_lr)

    raw_desc = -raw_grad
    corr_stack, raw_corr_stack = _locom_adjust_correction_stack(W - W0, raw_desc)
    corr_norm = corr_stack.flatten(1).norm(dim=1).clamp_min(1e-12)
    raw_corr_norm = raw_corr_stack.flatten(1).norm(dim=1).clamp_min(1e-12)
    raw_norm = raw_desc.flatten(1).norm(dim=1).clamp_min(1e-12)
    raw_cosine = (raw_corr_stack.flatten(1) * raw_desc.flatten(1)).sum(dim=1) / (raw_corr_norm * raw_norm)
    cosine = (corr_stack.flatten(1) * raw_desc.flatten(1)).sum(dim=1) / (corr_norm * raw_norm)
    loss_decreased = loss_k <= loss0
    accepted = loss_decreased if LOCO_M_REQUIRE_LOSS_DECREASE else torch.ones_like(loss_decreased, dtype=torch.bool)
    accepted = accepted & (cosine >= float(LOCO_M_MIN_COS_DESC))

    for pos, layer_idx in enumerate(layers):
        mlp = model.blocks[layer_idx].mlp
        if bool(accepted[pos]):
            corr = corr_stack[pos].to(mlp.fc.weight.dtype)
            mlp._loco_corr = corr
            mlp.fc.weight._loco_corr = corr
            mlp.fc.weight._loco_step = step
        else:
            mlp._loco_corr = None
            mlp.fc.weight._loco_corr = None
            mlp.fc.weight._loco_step = step
        if step in LOCO_M_LOG_STEPS and len(stats) < 4:
            stats.append(
                f"l{layer_idx}:loss0={float(loss0[pos]):.3e}"
                f",lossK={float(loss_k[pos]):.3e}"
                f",corr_norm={float(corr_norm[pos]):.3e}"
                f",grad_norm={float(raw_norm[pos]):.3e}"
                f",raw_cos_desc={float(raw_cosine[pos]):.3f}"
                f",cos_desc={float(cosine[pos]):.3f}"
                f",accepted={int(bool(accepted[pos]))}"
                f",tokens={x.size(1)}"
                f",opt={LOCO_M_LOCAL_OPT}"
                f",mode={LOCO_M_CORRECTION_MODE}"
                f",batched=1"
            )
    return True

@torch.no_grad()
def prepare_locoprop_m(model: nn.Module, step: int):
    if not _locom_active(step):
        return
    stats = []
    if LOCO_M_RANDOM_CORRECTION:
        for layer_idx in sorted(LOCO_M_LAYER_SET):
            if layer_idx < 0 or layer_idx >= len(model.blocks):
                continue
            if layer_idx not in LOCO_M_OWNED_LAYER_SET:
                continue
            mlp = model.blocks[layer_idx].mlp
            if mlp.fc.weight.grad is None:
                continue
            corr_f = torch.randn(
                mlp.fc.weight.shape,
                device=mlp.fc.weight.device,
                dtype=torch.float32,
            )
            raw_grad = mlp.fc.weight.grad.float()
            raw_desc = -raw_grad
            corr_f, raw_corr_f = _locom_adjust_correction(corr_f, raw_desc)
            denom = corr_f.norm().mul(raw_desc.norm()).clamp_min(1e-12)
            raw_denom = raw_corr_f.norm().mul(raw_desc.norm()).clamp_min(1e-12)
            raw_cosine = raw_corr_f.flatten().dot(raw_desc.flatten()) / raw_denom
            cosine = corr_f.flatten().dot(raw_desc.flatten()) / denom
            corr = corr_f.to(mlp.fc.weight.dtype)
            mlp._loco_corr = corr
            mlp.fc.weight._loco_corr = corr
            mlp.fc.weight._loco_step = step
            if step in LOCO_M_LOG_STEPS and len(stats) < 4:
                stats.append(
                    f"l{layer_idx}:random=1"
                    f",corr_norm={float(corr_f.norm()):.3e}"
                    f",grad_norm={float(raw_grad.norm()):.3e}"
                    f",raw_cos_desc={float(raw_cosine):.3f}"
                    f",cos_desc={float(cosine):.3f}"
                    f",accepted=1"
                    f",opt={LOCO_M_LOCAL_OPT}"
                    f",mode={LOCO_M_CORRECTION_MODE}"
                )
        if step in LOCO_M_LOG_STEPS and stats:
            print0("locoprop_m_prepare step=" + str(step) + " " + " | ".join(stats), console=True)
        return

    if _prepare_locoprop_m_batched(model, step, stats):
        if step in LOCO_M_LOG_STEPS and stats:
            print0("locoprop_m_prepare step=" + str(step) + " " + " | ".join(stats), console=True)
        return

    for layer_idx in sorted(LOCO_M_LAYER_SET):
        if layer_idx < 0 or layer_idx >= len(model.blocks):
            continue
        mlp = model.blocks[layer_idx].mlp
        x_local = _locom_take_sample(mlp, "_loco_x")
        pre_local = _locom_take_sample(mlp, "_loco_pre")
        post_local = _locom_take_sample(mlp, "_loco_post")
        dpre_local = _locom_take_sample(mlp, "_loco_dpre")
        if x_local is None or pre_local is None or post_local is None or dpre_local is None:
            continue
        if mlp.fc.weight.grad is None:
            continue

        x = _locom_gather_sample(x_local)
        pre0 = _locom_gather_sample(pre_local)
        post = _locom_gather_sample(post_local)
        dpre = _locom_gather_sample(dpre_local)
        if layer_idx not in LOCO_M_OWNED_LAYER_SET:
            continue

        if LOCO_M_TARGET_SPACE == "pre":
            target = pre0 - LOCO_M_TARGET_GAMMA * dpre
        else:
            target = post - LOCO_M_TARGET_GAMMA * dpre
        W0 = mlp.fc.weight.detach().float()
        W = W0.clone()
        inv_n = 1.0 / max(x.size(0), 1)
        loss0 = None
        loss_k = None

        rms_avg = mlp._loco_rms_avg
        rms_mom = mlp._loco_rms_mom
        if LOCO_M_LOCAL_OPT == "rmsprop" and LOCO_M_RMS_RESET_EACH_STEP:
            rms_avg.zero_()
            rms_mom.zero_()

        for local_step in range(LOCO_M_LOCAL_STEPS):
            pred = x @ W.mT
            pred = pred + mlp.fc.bias.detach().float()
            if LOCO_M_TARGET_SPACE == "pre":
                err = pred - target
            else:
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

        raw_grad = mlp.fc.weight.grad.float()
        raw_desc = -raw_grad
        corr_f, raw_corr_f = _locom_adjust_correction(W - W0, raw_desc)
        corr = corr_f.to(mlp.fc.weight.dtype)
        denom = corr_f.norm().mul(raw_desc.norm()).clamp_min(1e-12)
        raw_denom = raw_corr_f.norm().mul(raw_desc.norm()).clamp_min(1e-12)
        raw_cosine = raw_corr_f.flatten().dot(raw_desc.flatten()) / raw_denom
        cosine = corr_f.flatten().dot(raw_desc.flatten()) / denom
        loss_decreased = bool(loss_k <= loss0)
        accepted = True
        if LOCO_M_REQUIRE_LOSS_DECREASE and not loss_decreased:
            accepted = False
        if float(cosine) < LOCO_M_MIN_COS_DESC:
            accepted = False
        if accepted:
            mlp._loco_corr = corr
            mlp.fc.weight._loco_corr = corr
            mlp.fc.weight._loco_step = step
        else:
            mlp._loco_corr = None
            mlp.fc.weight._loco_corr = None
            mlp.fc.weight._loco_step = step

        if step in LOCO_M_LOG_STEPS and len(stats) < 4:
            stats.append(
                f"l{layer_idx}:loss0={float(loss0):.3e}"
                f",lossK={float(loss_k):.3e}"
                f",corr_norm={float(corr_f.norm()):.3e}"
                f",grad_norm={float(raw_grad.norm()):.3e}"
                f",raw_cos_desc={float(raw_cosine):.3f}"
                f",cos_desc={float(cosine):.3f}"
                f",accepted={int(accepted)}"
                f",tokens={x.size(0)}"
                f",opt={LOCO_M_LOCAL_OPT}"
                f",mode={LOCO_M_CORRECTION_MODE}"
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
    if LOCO_M_NORM_TARGET > 0:
        scale = (LOCO_M_NORM_TARGET * base_step_norm) / corr_norm
    elif LOCO_M_NORM_TO_BASE:
        scale = base_step_norm / corr_norm
    norm_cap = _locom_current_norm_cap(step)
    if norm_cap > 0:
        max_norm = norm_cap * base_step_norm
        scale = torch.minimum(scale, max_norm / corr_norm)
    scale = scale * LOCO_M_ALPHA
    p.add_(corr, alpha=float(scale))
    if step in LOCO_M_LOG_STEPS and len(LOCO_M_APPLY_STATS) < 8:
        LOCO_M_APPLY_STATS.append(
            f"shape={tuple(p.shape)}:base_step={float(base_step_norm):.3e}"
            f",corr_norm={float(corr_norm):.3e},cap={norm_cap:.3f},scale={float(scale):.3e}"
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
    if step in TRACK3_CHECKPOINT_SAVED_STEPS:
        return False
    if not TRACK3_CHECKPOINT_DIR:
        raise ValueError("TRACK3_CHECKPOINT_STEPS is set but TRACK3_CHECKPOINT_DIR is empty")
    TRACK3_CHECKPOINT_SAVED_STEPS.add(step)
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
                "loco_m_norm_target": LOCO_M_NORM_TARGET,
                "loco_m_norm_cap": LOCO_M_NORM_CAP,
                "loco_m_norm_cap_windows": LOCO_M_NORM_CAP_WINDOWS_SPEC,
                "loco_m_active_windows": LOCO_M_ACTIVE_WINDOWS_SPEC,
                "loco_m_start_step": LOCO_M_START_STEP,
                "loco_m_end_step": LOCO_M_END_STEP,
                "loco_m_interval": LOCO_M_INTERVAL,
                "loco_m_gather_samples": LOCO_M_GATHER_SAMPLES,
                "loco_m_accum_samples": LOCO_M_ACCUM_SAMPLES,
                "loco_m_micro_sample_tokens": LOCO_M_MICRO_SAMPLE_TOKENS,
                "loco_m_aux_capture": LOCO_M_AUX_CAPTURE,
                "loco_m_aux_seqs": LOCO_M_AUX_SEQS,
                "loco_m_batched_prep": LOCO_M_BATCHED_PREP,
                "loco_m_local_opt": LOCO_M_LOCAL_OPT,
                "loco_m_target_space": LOCO_M_TARGET_SPACE,
                "loco_m_random_correction": LOCO_M_RANDOM_CORRECTION,
                "loco_m_local_lr_decay": LOCO_M_LOCAL_LR_DECAY,
                "loco_m_rms_beta1": LOCO_M_RMS_BETA1,
                "loco_m_rms_beta2": LOCO_M_RMS_BETA2,
                "loco_m_rms_eps": LOCO_M_RMS_EPS,
                "loco_m_rms_reset_each_step": LOCO_M_RMS_RESET_EACH_STEP,
                "loco_m_require_loss_decrease": LOCO_M_REQUIRE_LOSS_DECREASE,
                "loco_m_min_cos_desc": LOCO_M_MIN_COS_DESC,
                "track3_cooldown_frac": TRACK3_COOLDOWN_FRAC,
                "track3_lr_schedule": TRACK3_LR_SCHEDULE,
                "track3_lr_power": TRACK3_LR_POWER,
                "track3_lr_schedule_steps": TRACK3_LR_SCHEDULE_STEPS,
                "track3_lr_min_eta": TRACK3_LR_MIN_ETA,
                "track3_lr_bump_windows": TRACK3_LR_BUMP_WINDOWS_SPEC,
                "track3_lr_blend_start": TRACK3_LR_BLEND_START,
                "track3_lr_blend_end": TRACK3_LR_BLEND_END,
                "track3_lr_blend_target": TRACK3_LR_BLEND_TARGET,
                "track3_lr_blend_target_power": TRACK3_LR_BLEND_TARGET_POWER,
                "track3_lr_blend_target_steps": TRACK3_LR_BLEND_TARGET_STEPS,
                "track3_reset_trial_seed": TRACK3_RESET_TRIAL_SEED,
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
    if TRACK3_RESUME_LOAD_OPTIMIZERS:
        saved_optimizers = checkpoint.get("optimizers", [])
        if len(saved_optimizers) != len(optimizers):
            raise ValueError(
                f"checkpoint has {len(saved_optimizers)} optimizer states, expected {len(optimizers)}"
            )
        for optimizer, optimizer_state in zip(optimizers, saved_optimizers):
            optimizer.load_state_dict(optimizer_state)
    if TRACK3_LR_SCHEDULE == "pr287" or TRACK3_LR_AFTER_SWITCH == "pr287" or TRACK3_LR_BLEND_TARGET == "pr287":
        optimizers[0].param_groups[0]["power_c"] = TRACK3_ADAM_EMBED_POWER_C
        optimizers[0].param_groups[1]["power_c"] = TRACK3_ADAM_PROJ_POWER_C
        optimizers[0].param_groups[2]["power_c"] = TRACK3_ADAM_OTHER_POWER_C
        optimizers[1].param_groups[0]["power_c"] = TRACK3_MUON_POWER_C
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
        f"seed:{checkpoint.get('seed')} val_loss:{checkpoint.get('val_loss')} "
        f"load_optimizers:{TRACK3_RESUME_LOAD_OPTIMIZERS}",
        console=True,
    )
    return step

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
                    soft_blend = _track3_soft_muon_blend_for_step(LOCO_M_CURRENT_STEP)
                    if soft_blend > 0.0:
                        update = _track3_muon_update_soft(p.grad, state["momentum"], p.grad.new_tensor(soft_blend), mu=group["mu"])
                    else:
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
print0("Track3 LocoProp-M generated run: source=records/track_3_optimization/train_gpt_simple.py train_steps=3000")
print0(f"LocoM enabled={LOCO_M_ENABLED} layers={LOCO_M_LAYERS_SPEC} steps={LOCO_M_LOCAL_STEPS} sample_tokens={LOCO_M_SAMPLE_TOKENS} gather={LOCO_M_GATHER_SAMPLES} accum={LOCO_M_ACCUM_SAMPLES} micro_sample_tokens={LOCO_M_MICRO_SAMPLE_TOKENS} aux_capture={LOCO_M_AUX_CAPTURE} aux_seqs={LOCO_M_AUX_SEQS} batched_prep={LOCO_M_BATCHED_PREP} local_opt={LOCO_M_LOCAL_OPT} target_space={LOCO_M_TARGET_SPACE} random_correction={LOCO_M_RANDOM_CORRECTION} correction_mode={LOCO_M_CORRECTION_MODE} lr_decay={LOCO_M_LOCAL_LR_DECAY} rms_beta1={LOCO_M_RMS_BETA1} rms_beta2={LOCO_M_RMS_BETA2} rms_eps={LOCO_M_RMS_EPS} rms_reset_each_step={LOCO_M_RMS_RESET_EACH_STEP} require_loss_decrease={LOCO_M_REQUIRE_LOSS_DECREASE} min_cos_desc={LOCO_M_MIN_COS_DESC} inner_lr={LOCO_M_INNER_LR} target_gamma={LOCO_M_TARGET_GAMMA} prox={LOCO_M_PROX} alpha={LOCO_M_ALPHA} norm_to_base={LOCO_M_NORM_TO_BASE} norm_target={LOCO_M_NORM_TARGET} norm_cap={LOCO_M_NORM_CAP} norm_cap_windows={LOCO_M_NORM_CAP_WINDOWS_SPEC} active_windows={LOCO_M_ACTIVE_WINDOWS_SPEC} start_step={LOCO_M_START_STEP} end_step={LOCO_M_END_STEP} interval={LOCO_M_INTERVAL} target_loss={TRACK3_TARGET_LOSS} seed_base={TRACK3_SEED_BASE} seed_offset={TRACK3_SEED_OFFSET} cooldown_frac={TRACK3_COOLDOWN_FRAC} lr_schedule={TRACK3_LR_SCHEDULE} lr_power={TRACK3_LR_POWER} lr_schedule_steps={TRACK3_LR_SCHEDULE_STEPS} lr_min_eta={TRACK3_LR_MIN_ETA} lr_bump_windows={TRACK3_LR_BUMP_WINDOWS_SPEC} lr_switch_step={TRACK3_LR_SWITCH_STEP} lr_after_switch={TRACK3_LR_AFTER_SWITCH} lr_after_switch_power={TRACK3_LR_AFTER_SWITCH_POWER} lr_after_switch_steps={TRACK3_LR_AFTER_SWITCH_STEPS} lr_blend_start={TRACK3_LR_BLEND_START} lr_blend_end={TRACK3_LR_BLEND_END} lr_blend_target={TRACK3_LR_BLEND_TARGET} lr_blend_target_power={TRACK3_LR_BLEND_TARGET_POWER} lr_blend_target_steps={TRACK3_LR_BLEND_TARGET_STEPS} soft_muon={TRACK3_SOFT_MUON} soft_blend={TRACK3_SOFT_MUON_BLEND} soft_start={TRACK3_SOFT_MUON_START_STEP} soft_end={TRACK3_SOFT_MUON_END_STEP} soft_ceil={TRACK3_SOFT_MUON_CEIL} soft_norm_restore={TRACK3_SOFT_MUON_NORM_RESTORE} resume_checkpoint={TRACK3_RESUME_CHECKPOINT} resume_load_optimizers={TRACK3_RESUME_LOAD_OPTIMIZERS}")
print0(f"Running PyTorch {torch.version.__version__} compiled for CUDA {torch.version.cuda}"
       + f" on {torch.cuda.get_device_name(device)} with world_size {dist.get_world_size()}")
print0("="*100)

val_tokens = 20 * 524288
batch_size = 8 * 64 * 1024
mbs = int(os.environ.get("TRACK3_MBS", "64"))
val_inputs, val_targets = next(distributed_data_generator("data/fineweb10B/fineweb_val_*.bin", val_tokens))

model = GPT(vocab_size=50304, num_layers=12, model_dim=768).cuda()
if (not LOCO_M_ENABLED) or LOCO_M_AUX_CAPTURE or _env_flag("TRACK3_LOCOM_COMPILE", "0"):
    model.compile(dynamic=False)
compiled_model = model


num_trials = int(sys.argv[-1]) if len(sys.argv) > 1 else 1

for trial_idx in range(num_trials):
    track3_trial_seed = TRACK3_SEED_BASE + TRACK3_SEED_OFFSET + trial_idx
    if TRACK3_RESET_TRIAL_SEED:
        torch.manual_seed(track3_trial_seed)
        torch.cuda.manual_seed_all(track3_trial_seed)
    print0(f"track3_trial_seed={track3_trial_seed} trial={trial_idx}", console=True)


    ########################################
    #       Init & Optim Hyperparams       #
    ########################################

    # we want to minimize this while still reaching 3.28 val loss
    train_steps = 3000  # generated by tools/make_track3_locoprop_m.py

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
    if TRACK3_LR_SCHEDULE == "pr287" or TRACK3_LR_AFTER_SWITCH == "pr287":
        optimizer1.param_groups[0]["power_c"] = TRACK3_ADAM_EMBED_POWER_C
        optimizer1.param_groups[1]["power_c"] = TRACK3_ADAM_PROJ_POWER_C
        optimizer1.param_groups[2]["power_c"] = TRACK3_ADAM_OTHER_POWER_C
        optimizer2.param_groups[0]["power_c"] = TRACK3_MUON_POWER_C
    assert set(p for opt in optimizers for group in opt.param_groups
               for p in group["params"]) == set(model.parameters())
    for opt in optimizers:
        for group in opt.param_groups:
            group["initial_lr"] = group["lr"]

    # learning rate schedule: stable then decay
    def _track3_active_lr_schedule(step):
        if TRACK3_LR_SWITCH_STEP >= 0 and step >= TRACK3_LR_SWITCH_STEP and TRACK3_LR_AFTER_SWITCH:
            return TRACK3_LR_AFTER_SWITCH, TRACK3_LR_AFTER_SWITCH_STEPS, TRACK3_LR_AFTER_SWITCH_POWER
        return TRACK3_LR_SCHEDULE, TRACK3_LR_SCHEDULE_STEPS, TRACK3_LR_POWER

    def _track3_pr287_lr(step, initial_lr, power_c, schedule_steps, lr_power):
        schedule_steps = schedule_steps if schedule_steps > 0 else train_steps
        downward_lr = power_c * max(0.0, schedule_steps - step) ** lr_power
        return min(initial_lr, downward_lr)

    def _track3_schedule_lr(step, group, lr_schedule, schedule_steps, lr_power):
        schedule_steps = schedule_steps if schedule_steps > 0 else train_steps
        if lr_schedule == "pr287":
            return _track3_pr287_lr(step, group["initial_lr"], group["power_c"], schedule_steps, lr_power)
        progress = step / schedule_steps
        if progress < 1 - TRACK3_COOLDOWN_FRAC:
            eta = 1.0
        else:
            eta = (1 - progress) / TRACK3_COOLDOWN_FRAC
            if lr_schedule == "power":
                eta = eta ** lr_power
            eta = max(eta, TRACK3_LR_MIN_ETA)
        return group["initial_lr"] * eta

    def _track3_blend_lr(step, group, base_lr, lr_mult):
        if not TRACK3_LR_BLEND_TARGET or TRACK3_LR_BLEND_START < 0:
            return base_lr
        if step < TRACK3_LR_BLEND_START:
            return base_lr
        target_lr = _track3_schedule_lr(step, group, TRACK3_LR_BLEND_TARGET, TRACK3_LR_BLEND_TARGET_STEPS, TRACK3_LR_BLEND_TARGET_POWER) * lr_mult
        if TRACK3_LR_BLEND_END <= TRACK3_LR_BLEND_START or step >= TRACK3_LR_BLEND_END:
            t = 1.0
        else:
            t = (step - TRACK3_LR_BLEND_START) / (TRACK3_LR_BLEND_END - TRACK3_LR_BLEND_START)
            t = max(0.0, min(1.0, t))
            t = t * t * (3.0 - 2.0 * t)
        return base_lr + (target_lr - base_lr) * t

    def set_hparams(step, cooldown_frac=TRACK3_COOLDOWN_FRAC):
        lr_schedule, lr_schedule_steps, lr_power = _track3_active_lr_schedule(step)
        if lr_schedule == "pr287":
            lr_mult = _track3_lr_multiplier(step)
            for opt in optimizers:
                for group in opt.param_groups:
                    group["lr"] = _track3_pr287_lr(step, group["initial_lr"], group["power_c"], lr_schedule_steps, lr_power) * lr_mult
            return
        schedule_steps = lr_schedule_steps if lr_schedule_steps > 0 else train_steps
        progress = step / schedule_steps
        assert 0 <= progress < 1
        if progress < 1 - cooldown_frac:
            eta = 1.0
        else:
            eta = (1 - progress) / cooldown_frac
            if lr_schedule == "power":
                eta = eta ** lr_power
            eta = max(eta, TRACK3_LR_MIN_ETA)
        for opt in optimizers:
            for group in opt.param_groups:
                lr_mult = _track3_lr_multiplier(step)
                base_lr = group["initial_lr"] * eta * lr_mult
                group["lr"] = _track3_blend_lr(step, group, base_lr, lr_mult)


    ########################################
    #        Training and Validation       #
    ########################################

    train_loader = distributed_data_generator("data/fineweb10B/fineweb_train_*.bin", batch_size)
    start_step = maybe_load_track3_checkpoint(model, optimizers)
    if start_step > 0 and TRACK3_RESUME_ADVANCE_DATA:
        for _ in range(start_step):
            next(train_loader)
        print0(f"track3_resume_advanced_data steps:{start_step}", console=True)
    for p in model.parameters():
        dist.broadcast(p.detach(), 0)
    # start the clock
    training_time = 0
    last_val_step = start_step
    dist.barrier()
    t0 = time.perf_counter()
    for step in range(start_step, train_steps + 1):

        # --------------- VALIDATION SECTION -----------------
        val_step_freq = int(os.environ.get("SCREEN_VAL_EVERY", "125")) if step / train_steps < 0.9 else 25
        if step == train_steps or step % val_step_freq == 0:
            # stop the clock
            dist.barrier()
            time_since_last_val = time.perf_counter() - t0
            step_avg = time_since_last_val / (step - last_val_step) if step > last_val_step else float("nan")
            last_val_step = step
            training_time += time_since_last_val
            model.eval()
            val_loss = 0
            with torch.no_grad():
                assert len(val_inputs) % mbs == 0
                for i in range(len(val_inputs) // mbs):
                    val_loss += compiled_model(val_inputs[i*mbs:(i+1)*mbs], val_targets[i*mbs:(i+1)*mbs])
            dist.all_reduce(val_loss, op=dist.ReduceOp.SUM)
            val_loss /= val_tokens
            print0(f"step:{step}/{train_steps} val_loss:{val_loss:.5f} train_time:{training_time:.3f}s"
                   + f" step_avg:{1000*step_avg:.2f}ms", console=True)
            if maybe_save_track3_checkpoint(model, optimizers, step, train_steps, trial_idx, val_loss):
                break
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
        set_locoprop_m_current_step(step)
        inputs, targets = next(train_loader)
        # accumulate across microbatches in case we are running with fewer than 8 gpus
        assert len(inputs) % mbs == 0
        num_microbatches = len(inputs) // mbs
        for i in range(num_microbatches):
            capture_this_micro = (not LOCO_M_AUX_CAPTURE) and (LOCO_M_ACCUM_SAMPLES or i == num_microbatches - 1)
            set_locoprop_m_capture_this_micro(capture_this_micro)
            active_model = model if ((not LOCO_M_AUX_CAPTURE) and LOCO_M_ENABLED and _locom_active(step) and capture_this_micro) else compiled_model
            active_model(inputs[i*mbs:(i+1)*mbs], targets[i*mbs:(i+1)*mbs]).backward()
        set_locoprop_m_capture_this_micro(False)
        for name, p in model.named_parameters():
            assert p.grad is not None, name
            dist.all_reduce(p.grad, op=dist.ReduceOp.SUM)
        # set optimization hyperparameters and take a step
        set_hparams(step)
        prepare_locoprop_m_aux(model, inputs, targets, step)
        prepare_locoprop_m(model, step)
        for opt in optimizers:
            opt.step()
        flush_locoprop_m_apply_stats(step)
        model.zero_grad(set_to_none=True)
        if maybe_save_track3_checkpoint(model, optimizers, step + 1, train_steps, trial_idx, None):
            break
        approx_training_time = training_time + (time.perf_counter() - t0)
        print0(f"step:{step+1}/{train_steps} train_time:{approx_training_time:.3f}s"
               + f" step_avg:{1000*approx_training_time/(step + 1):.2f}ms", console=True, log=False)

dist.destroy_process_group()
