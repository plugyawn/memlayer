#!/usr/bin/env python3
"""Generate a WR train_gpt.py variant with sampled MLP c_fc LocoProp-M.

The generated script keeps the baseline WR optimizer path intact, then adds a
state-decoupled local matching-loss displacement to owned MLP c_fc matrices.
It is intentionally narrow: c_fc only, sampled tokens, no extra full-model
forward/backward passes.
"""

from __future__ import annotations

import argparse
from pathlib import Path


WR_LOCOM_CONFIG = r'''
def _wr_locom_env_flag(name: str, default: str = "0") -> bool:
    return os.environ.get(name, default).lower() in {"1", "true", "yes", "on"}

def _wr_locom_parse_layer_set(spec: str, total_layers: int = 11) -> set[int]:
    spec = spec.strip().lower()
    if spec in {"all", "*"}:
        return set(range(total_layers))
    if spec in {"", "none"}:
        return set()
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

WR_LOCOM_ENABLED = _wr_locom_env_flag("WR_LOCOM_ENABLED", "1")
WR_LOCOM_LAYERS_SPEC = os.environ.get("WR_LOCOM_LAYERS", "all")
WR_LOCOM_LAYER_SET = _wr_locom_parse_layer_set(WR_LOCOM_LAYERS_SPEC)
WR_LOCOM_SAMPLE_TOKENS = int(os.environ.get("WR_LOCOM_SAMPLE_TOKENS", "2048"))
WR_LOCOM_LOCAL_STEPS = int(os.environ.get("WR_LOCOM_STEPS", "4"))
WR_LOCOM_INNER_LR = float(os.environ.get("WR_LOCOM_INNER_LR", "0.1"))
WR_LOCOM_TARGET_GAMMA = float(os.environ.get("WR_LOCOM_TARGET_GAMMA", "1.0"))
WR_LOCOM_PROX = float(os.environ.get("WR_LOCOM_PROX", "0.1"))
WR_LOCOM_ALPHA = float(os.environ.get("WR_LOCOM_ALPHA", "1.0"))
WR_LOCOM_NORM_TO_BASE = _wr_locom_env_flag("WR_LOCOM_NORM_TO_BASE", "0")
WR_LOCOM_NORM_CAP = float(os.environ.get("WR_LOCOM_NORM_CAP", "0.20"))
WR_LOCOM_START_STEP = int(os.environ.get("WR_LOCOM_START_STEP", "0"))
WR_LOCOM_END_STEP = int(os.environ.get("WR_LOCOM_END_STEP", "1000000000"))
WR_LOCOM_INTERVAL = int(os.environ.get("WR_LOCOM_INTERVAL", "1"))
WR_LOCOM_LOG_STEPS = {
    int(x)
    for x in os.environ.get("WR_LOCOM_LOG_STEPS", "0,1,2,10,50,125,250,500").split(",")
    if x.strip()
}

WR_LOCOM_CURRENT_STEP = -1
WR_LOCOM_OWNED_LAYER_SET: set[int] = set()
WR_LOCOM_LAYER_SAMPLES: dict[int, dict[str, Tensor]] = {}
WR_LOCOM_LAYER_CORR: dict[int, Tensor] = {}
WR_LOCOM_APPLY_STATS: list[str] = []

def _wr_locom_active(step: int) -> bool:
    return (
        WR_LOCOM_ENABLED
        and WR_LOCOM_LOCAL_STEPS > 0
        and step >= WR_LOCOM_START_STEP
        and step < WR_LOCOM_END_STEP
        and step % max(WR_LOCOM_INTERVAL, 1) == 0
    )

def _wr_locom_layer_active(layer_idx: int) -> bool:
    return layer_idx in WR_LOCOM_LAYER_SET

@torch.no_grad()
def _wr_locom_begin_step(step: int):
    global WR_LOCOM_CURRENT_STEP
    WR_LOCOM_CURRENT_STEP = step
    WR_LOCOM_LAYER_SAMPLES.clear()
    WR_LOCOM_LAYER_CORR.clear()
    WR_LOCOM_APPLY_STATS.clear()

@torch.no_grad()
def _wr_locom_local_sample_rows(x: Tensor) -> Tensor:
    flat = x.reshape(-1, x.size(-1))
    sample_tokens = WR_LOCOM_SAMPLE_TOKENS
    if dist.is_available() and dist.is_initialized() and dist.get_world_size() > 1 and sample_tokens > 0:
        sample_tokens = max(1, (sample_tokens + dist.get_world_size() - 1) // dist.get_world_size())
    if sample_tokens <= 0 or flat.size(0) <= sample_tokens:
        return flat.detach()
    stride = max(flat.size(0) // sample_tokens, 1)
    return flat[::stride][:sample_tokens].detach()

@torch.no_grad()
def _wr_locom_capture_forward_sample(layer_idx: int, x: Tensor, post: Tensor):
    if not (_wr_locom_active(WR_LOCOM_CURRENT_STEP) and _wr_locom_layer_active(layer_idx)):
        return
    WR_LOCOM_LAYER_SAMPLES[layer_idx] = {
        "x": _wr_locom_local_sample_rows(x).to(torch.bfloat16),
        "post": _wr_locom_local_sample_rows(post).to(torch.bfloat16),
    }

@torch.no_grad()
def _wr_locom_capture_backward_sample(layer_idx: int, dpre: Tensor):
    if not (_wr_locom_active(WR_LOCOM_CURRENT_STEP) and _wr_locom_layer_active(layer_idx)):
        return
    sample = WR_LOCOM_LAYER_SAMPLES.get(layer_idx)
    if sample is None:
        return
    sample["dpre"] = _wr_locom_local_sample_rows(dpre).to(torch.bfloat16)

@torch.no_grad()
def _wr_locom_gather_sample(t: Tensor) -> Tensor:
    if not (dist.is_available() and dist.is_initialized()) or dist.get_world_size() == 1:
        return t.float()
    gathered = [torch.empty_like(t) for _ in range(dist.get_world_size())]
    dist.all_gather(gathered, t.contiguous())
    return torch.cat(gathered, dim=0).float()

@torch.no_grad()
def attach_wr_locoprop_m_optimizer(loco_model: nn.Module, optimizer) -> None:
    global WR_LOCOM_OWNED_LAYER_SET
    if not WR_LOCOM_ENABLED:
        return
    mlp_param = optimizer._param_by_label["mlp_bank"]
    mlp_cfg = optimizer.param_cfgs[mlp_param]
    local_rank = dist.get_rank() if dist.is_initialized() else 0
    start_idx = local_rank * mlp_cfg.chunk_size
    end_idx = start_idx + mlp_cfg.chunk_size
    owned = set()
    num_mlp_real = 22
    for global_idx in range(start_idx, end_idx):
        if global_idx >= num_mlp_real:
            continue
        if global_idx % 2 == 0:
            layer_idx = global_idx // 2
            if layer_idx in WR_LOCOM_LAYER_SET:
                owned.add(layer_idx)
    WR_LOCOM_OWNED_LAYER_SET = owned
    print0(
        f"wr_locom_owner rank={local_rank} world={world_size} "
        f"owned_layers={sorted(owned)} global_sample_tokens={WR_LOCOM_SAMPLE_TOKENS}",
        console=True,
    )

@torch.no_grad()
def prepare_wr_locoprop_m(loco_model: nn.Module, step: int) -> None:
    if not _wr_locom_active(step):
        return
    stats = []
    for layer_idx in sorted(WR_LOCOM_OWNED_LAYER_SET):
        sample = WR_LOCOM_LAYER_SAMPLES.get(layer_idx)
        if sample is None or "x" not in sample or "post" not in sample or "dpre" not in sample:
            continue
        x = _wr_locom_gather_sample(sample["x"])
        post0 = _wr_locom_gather_sample(sample["post"])
        dpre = _wr_locom_gather_sample(sample["dpre"])
        target = post0 - WR_LOCOM_TARGET_GAMMA * dpre

        W0 = loco_model.mlp_bank[layer_idx, 0].detach().float()
        W = W0.clone()
        inv_n = 1.0 / max(x.size(0), 1)
        loss0 = None
        loss_k = None

        for _ in range(WR_LOCOM_LOCAL_STEPS):
            pre = x @ W.mT
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

        corr = (W - W0).to(loco_model.mlp_bank.dtype)
        WR_LOCOM_LAYER_CORR[layer_idx] = corr

        if step in WR_LOCOM_LOG_STEPS and len(stats) < 6:
            raw_grad = loco_model.mlp_bank.grad[layer_idx, 0].float() if loco_model.mlp_bank.grad is not None else None
            corr_f = corr.float()
            if raw_grad is not None:
                raw_desc = -raw_grad
                denom = corr_f.norm().mul(raw_desc.norm()).clamp_min(1e-12)
                cosine = corr_f.flatten().dot(raw_desc.flatten()) / denom
                grad_norm = float(raw_grad.norm())
                cos_desc = float(cosine)
            else:
                grad_norm = float("nan")
                cos_desc = float("nan")
            stats.append(
                f"l{layer_idx}:loss0={float(loss0):.3e}"
                f",lossK={float(loss_k):.3e}"
                f",corr_norm={float(corr_f.norm()):.3e}"
                f",grad_norm={grad_norm:.3e}"
                f",cos_desc={cos_desc:.3f}"
                f",tokens={x.size(0)}"
            )

    if step in WR_LOCOM_LOG_STEPS and stats:
        print0("wr_locom_prepare step=" + str(step) + " " + " | ".join(stats), console=True)

@torch.no_grad()
def _wr_locom_apply_mlp_chunk_corrections(optimizer, p_slice: Tensor, p_cfg, p_state: dict, v_chunk: Tensor, local_rank: int) -> None:
    if not (WR_LOCOM_ENABLED and p_cfg.label == "mlp_bank" and _wr_locom_active(WR_LOCOM_CURRENT_STEP)):
        return
    start_idx = local_rank * p_cfg.chunk_size
    for mat_idx in range(p_cfg.chunk_size):
        global_idx = start_idx + mat_idx
        if global_idx >= 22 or global_idx % 2 == 1:
            continue
        layer_idx = global_idx // 2
        corr = WR_LOCOM_LAYER_CORR.get(layer_idx)
        if corr is None:
            continue

        lr_mul = p_cfg.lr_mul
        if p_cfg.per_matrix_lr_mul is not None:
            lr_mul *= p_cfg.per_matrix_lr_mul[mat_idx]
        base_step_norm = v_chunk[mat_idx].float().norm().mul(p_cfg.lr * lr_mul)
        corr_norm = corr.float().norm().clamp_min(1e-12)
        scale = torch.ones((), device=corr.device, dtype=torch.float32)
        if WR_LOCOM_NORM_TO_BASE:
            scale = base_step_norm / corr_norm
        if WR_LOCOM_NORM_CAP > 0:
            max_norm = WR_LOCOM_NORM_CAP * base_step_norm
            scale = torch.minimum(scale, max_norm / corr_norm)
        scale = scale * WR_LOCOM_ALPHA
        optimizer._loco_full_add_lr_t.fill_(float(scale))
        neg_corr = corr.neg()
        NorMuonAndAdam._cautious_wd_and_update_inplace(
            p_slice[mat_idx].view(torch.uint16),
            p_state["mantissa"][mat_idx],
            neg_corr,
            optimizer._zero_t,
            optimizer._loco_full_add_lr_t,
        )
        if WR_LOCOM_CURRENT_STEP in WR_LOCOM_LOG_STEPS and len(WR_LOCOM_APPLY_STATS) < 8:
            WR_LOCOM_APPLY_STATS.append(
                f"l{layer_idx}:base_step={float(base_step_norm):.3e}"
                f",corr_norm={float(corr_norm):.3e},scale={float(scale):.3e}"
            )

@torch.no_grad()
def flush_wr_locoprop_m_apply_stats(step: int) -> None:
    if step in WR_LOCOM_LOG_STEPS and WR_LOCOM_APPLY_STATS:
        print0("wr_locom_apply step=" + str(step) + " " + " | ".join(WR_LOCOM_APPLY_STATS[:8]), console=True)
    WR_LOCOM_APPLY_STATS.clear()

class FusedLinearReLUSquareLocoMFunction(torch.autograd.Function):
    @staticmethod
    def forward(ctx, x, W1, W2, layer_idx: int):
        pre, post = linear_relu_square(x.view((-1, x.shape[-1])), W1)
        y = post @ W2
        ctx.save_for_backward(x, W1, W2, pre, post)
        ctx.layer_idx = int(layer_idx)
        _wr_locom_capture_forward_sample(ctx.layer_idx, x, post)
        return y.view(x.shape)

    @staticmethod
    def backward(ctx, grad_output):
        x, W1, W2, pre, post = ctx.saved_tensors
        dW2 = post.T @ grad_output
        dpre = linear_relu_square(grad_output.view((-1, grad_output.shape[-1])), W2, aux=pre)
        _wr_locom_capture_backward_sample(ctx.layer_idx, dpre)
        dW1 = dpre.T @ x
        dx = dpre @ W1
        return dx.view(x.shape), dW1, dW2, None

ReLUSqrdMLPLocoM = FusedLinearReLUSquareLocoMFunction.apply

def _wr_locom_mlp(x: Tensor, W1: Tensor, W2: Tensor, layer_idx: int, training: bool) -> Tensor:
    if training and _wr_locom_active(WR_LOCOM_CURRENT_STEP) and _wr_locom_layer_active(layer_idx):
        return ReLUSqrdMLPLocoM(x, W1, W2, layer_idx)
    return ReLUSqrdMLP(x, W1, W2)
'''


def replace_exact(text: str, old: str, new: str) -> str:
    if old not in text:
        raise RuntimeError(f"pattern not found:\n{old[:300]}")
    return text.replace(old, new, 1)


def generate(source: Path, output: Path, train_steps: int) -> None:
    text = source.read_text()
    text = replace_exact(
        text,
        "from triton_kernels import XXT, XTX, ba_plus_cAA, FusedLinearReLUSquareFunction, FusedLinearReLUSquareWithDiagFunction, FusedSoftcappedCrossEntropy, transpose_add, transpose_copy\n",
        "from triton_kernels import XXT, XTX, ba_plus_cAA, FusedLinearReLUSquareFunction, FusedLinearReLUSquareWithDiagFunction, FusedSoftcappedCrossEntropy, linear_relu_square, transpose_add, transpose_copy\n",
    )
    text = replace_exact(
        text,
        "ReLUSqrdMLP = FusedLinearReLUSquareFunction.apply\nReLUSqrdMLPWithDiag = FusedLinearReLUSquareWithDiagFunction.apply\n",
        "ReLUSqrdMLP = FusedLinearReLUSquareFunction.apply\nReLUSqrdMLPWithDiag = FusedLinearReLUSquareWithDiagFunction.apply\n" + WR_LOCOM_CONFIG,
    )
    text = replace_exact(
        text,
        "args = Hyperparameters()\n",
        "args = Hyperparameters()\n"
        f"args.num_scheduled_iterations = {train_steps}  # generated by tools/make_wr_locoprop_m.py\n"
        "args.num_extension_iterations = 0\n"
        "args.val_loss_every = int(os.environ.get(\"SCREEN_VAL_EVERY\", str(args.val_loss_every)))\n",
    )
    text = text.replace(
        "mlp_out = ReLUSqrdMLP(mlp_in, c_fc, c_proj)",
        "mlp_out = _wr_locom_mlp(mlp_in, c_fc, c_proj, i, self.training)",
    )
    text = replace_exact(
        text,
        "        self.optimizer = NorMuonAndAdam(\n"
        "            model.named_parameters(),\n"
        "            param_table=self.param_table,\n"
        "            scatter_order=list(self.param_table),  # Dict order defines scatter priority\n"
        "            work_order=self.work_order,\n"
        "            adam_defaults=adam_defaults,\n"
        "            normuon_defaults=normuon_defaults,\n"
        "            loco_diag_model=getattr(model, \"_orig_mod\", model) if LOCO_FEATURE_ACTIVE else None,\n"
        "        )\n"
        "        if LOCO_FULL_ACTIVE:\n",
        "        self.optimizer = NorMuonAndAdam(\n"
        "            model.named_parameters(),\n"
        "            param_table=self.param_table,\n"
        "            scatter_order=list(self.param_table),  # Dict order defines scatter priority\n"
        "            work_order=self.work_order,\n"
        "            adam_defaults=adam_defaults,\n"
        "            normuon_defaults=normuon_defaults,\n"
        "            loco_diag_model=getattr(model, \"_orig_mod\", model) if (LOCO_FEATURE_ACTIVE or WR_LOCOM_ENABLED) else None,\n"
        "        )\n"
        "        if WR_LOCOM_ENABLED:\n"
        "            attach_wr_locoprop_m_optimizer(getattr(model, \"_orig_mod\", model), self.optimizer)\n"
        "        if LOCO_FULL_ACTIVE:\n",
    )
    text = replace_exact(
        text,
        "        return p_slice\n\n    def _loco_diag_col_update_fn(self):\n",
        "        _wr_locom_apply_mlp_chunk_corrections(self, p_slice, p_cfg, p_state, v_chunk, rank)\n"
        "        return p_slice\n\n    def _loco_diag_col_update_fn(self):\n",
    )
    text = replace_exact(
        text,
        "    def advance_schedule(self, step: int):\n        if LOCO_FULL_ACTIVE:\n",
        "    def advance_schedule(self, step: int):\n        _wr_locom_begin_step(step)\n        if LOCO_FULL_ACTIVE:\n",
    )
    text = replace_exact(
        text,
        "        self._prepare_loco_diag_buffers(step)\n        self._prepare_loco_full_buffers(step)\n        self.optimizer.step(do_adam=do_adam)\n        if LOCO_FEATURE_ACTIVE:\n",
        "        self._prepare_loco_diag_buffers(step)\n        self._prepare_loco_full_buffers(step)\n        prepare_wr_locoprop_m(getattr(self.model, \"_orig_mod\", self.model), step)\n        self.optimizer.step(do_adam=do_adam)\n        flush_wr_locoprop_m_apply_stats(step)\n        if LOCO_FEATURE_ACTIVE:\n",
    )
    text = replace_exact(
        text,
        "model: nn.Module = torch.compile(model, dynamic=False, fullgraph=True)\ntraining_manager = TrainingManager(model)\n",
        "if WR_LOCOM_ENABLED and not _wr_locom_env_flag(\"WR_LOCOM_COMPILE\", \"0\"):\n"
        "    print0(\"WR LocoProp-M: skipping torch.compile for Python-side sampled activation capture\", console=True)\n"
        "else:\n"
        "    model = torch.compile(model, dynamic=False, fullgraph=True)\n"
        "training_manager = TrainingManager(model)\n",
    )
    text = replace_exact(
        text,
        "if NEWTONV_PAIRED_CASES:\n    print0(f\"Using NEWTONV_PAIRED_CASES={','.join(NEWTONV_PAIRED_CASES)}\", console=True)\n",
        "if NEWTONV_PAIRED_CASES:\n"
        "    print0(f\"Using NEWTONV_PAIRED_CASES={','.join(NEWTONV_PAIRED_CASES)}\", console=True)\n"
        "print0(\n"
        "    f\"WR LocoProp-M generated run: total_steps={args.num_scheduled_iterations + args.num_extension_iterations} \"\n"
        "    f\"enabled={WR_LOCOM_ENABLED} layers={WR_LOCOM_LAYERS_SPEC} steps={WR_LOCOM_LOCAL_STEPS} \"\n"
        "    f\"sample_tokens={WR_LOCOM_SAMPLE_TOKENS} inner_lr={WR_LOCOM_INNER_LR} \"\n"
        "    f\"gamma={WR_LOCOM_TARGET_GAMMA} prox={WR_LOCOM_PROX} alpha={WR_LOCOM_ALPHA} \"\n"
        "    f\"norm_to_base={WR_LOCOM_NORM_TO_BASE} norm_cap={WR_LOCOM_NORM_CAP}\",\n"
        "    console=True,\n"
        ")\n",
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(text)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", default="train_gpt.py")
    parser.add_argument("--output", required=True)
    parser.add_argument("--steps", type=int, default=500)
    args = parser.parse_args()
    generate(Path(args.source), Path(args.output), args.steps)


if __name__ == "__main__":
    main()
