# Diagonal LocoProp-S Compute Graph Plan

Branch: `codex/wr-fresh-20260526`

## Current conclusion

The design doc has two related but distinct optimizer rules:

- Newton-Muon: right-precondition `G` with feature Gram `C`, then apply the
  existing Muon/NorMuon-style matrix orthogonalization.
- Affine LocoProp-S: consume `(G, C)` directly for a finite-step or converged
  quadratic update.

For the speedrun branch, the safer next candidate is the first rule: feature-Gram
preconditioning on top of NorMuon. The direct LocoProp-S path remains useful as a
diagnostic, but it is not the primary parity target.

The direct diagonal LocoProp-S update is:

```text
delta_W = -gamma * G * diag(C + ridge I)^-1
```

for the conventional `W: out x in`, `Y = X @ W.T` storage. For transposed
`W: in x out`, the same logical update scales rows instead of columns.

## Storage-axis contract in this repo

| parameter surface | forward path | storage | feature source | scale axis |
| --- | --- | --- | --- | --- |
| `qk_bank` | `F.linear(attn_in_normed, qk)` | `out x in` | `attn_in_normed`, dim 768 | columns |
| `vo_bank` V rows | `F.linear(attn_in_normed, v)` | `out x in` | `attn_in_normed`, dim 768 | columns |
| `vo_bank` O rows | `F.linear(attn_y, o)` | `out x in` | gated/reassembled attention output, dim 768 | columns |
| `mlp_bank` c_fc | `linear_relu_square(x, W1)` | `out x in` | `norm(x)`, dim 768 | columns |
| `mlp_bank` c_proj | `post @ W2` | `in x out` | ReLU-squared `post`, dim 3072 | rows |

This mixed convention is the main invasive point. A single generic
`grad * scale[:, None, :]` transform is wrong for at least one real surface.

## Current implementation status

Implemented default-off in this branch:

- `LOCO_DIAG=1` enables diagonal feature-Gram capture for selected MLP and
  attention banks.
- `LOCO_DIAG_MODE=normuon` is the default: precondition MLP gradients with the
  diagonal feature Gram, then run the existing NorMuon path.
- `LOCO_DIAG_NORMUON_PRECOND=raw|normsqrt|normquarter` selects between literal
  `G/C` and mean-normalized inverse-power feature scaling before NorMuon. The
  normalized forms preserve baseline-scale update magnitude and only change
  direction.
- `LOCO_DIAG_MODE=direct` keeps the direct diagonal LocoProp-S update for
  comparison. It currently applies only to the MLP bank and is not the primary
  parity target.
- `LOCO_DIAG_SURFACES` supports `mlp_fc`, `mlp_proj`, `qk`, `v`, and `o`.
- `mlp_fc` and `mlp_proj` can now be isolated independently in `normuon` mode.
- `LOCO_DIAG_MLP_LAYERS` and `LOCO_DIAG_ATTN_LAYERS` restrict capture/update by
  model layer. `all` is the default; attention layer 6 is skipped because this
  repo skips that attention block.
- `LOCO_DIAG_NORMUON_PRECOND` defaults to `normquarter`, using a relative ridge
  and a `LOCO_DIAG_BLEND_STEPS` warmup. `raw` remains available as a diagnostic.
- `LOCO_DIAG_LOG_STEPS` prints feature-diagonal spread and preconditioned
  gradient-norm ratios for short-step debugging.
- `mlp_fc` accumulates `sum(norm(x)^2)` and column-preconditions c_fc.
- `mlp_proj` returns `sum(post^2)` from the fused MLP autograd function and
  row-preconditions c_proj.
- `qk` and `v` accumulate `sum(attn_in_normed^2)` and column-precondition their
  bank gradients.
- `o` accumulates the gated/reassembled attention output before the O projection
  and column-preconditions the O bank gradients.
- `LOCO_DIAG_DENOM_SCALE` defaults to `grad_scale`, matching loss-scaled
  gradients against the feature-Gram denominator. This fixes the earlier
  mismatch where `G` was scaled by gradient accumulation but `C` was not.

## H100 validation results

Pod: `8249f5e6edc947139c108f5da9c7b480`
H100: 1x H100 80GB PCIe, Prime, `$2.35/hr`

Environment notes:

- Fresh image needed `python3.10-venv`, `python3.10-dev`, build tools, and CUDA
  compiler/runtime packages.
- `torch==2.10.0` / Triton 3.6.0 worked. The newer nightly
  `torch-2.13.0.dev20260521+cu126` failed the repo CE kernel at `__tanhf`.
- `kernels==0.14.1` required unavailable Hugging Face auth for the FA3 kernel;
  `kernels==0.11.7` fetched `varunneal/flash-attention-3` unauthenticated.

Validation:

| run | evidence log | result |
| --- | --- | --- |
| focused fused-MLP/update smoke | terminal output | `torch.compile` fullgraph passed for MLP diag capture and both row/column bf16 mantissa update helpers |
| tiny full-entry smoke | `.opencode/locodiag_smoke.log` | 3 train steps completed with `LOCO_DIAG=1`; final val 8.4663; peak allocated 17.3 GiB |
| real-data 60-step baseline | `.opencode/baseline_screen60.log` | final val 4.8502; final step_avg 672.76ms; peak allocated 37.3 GiB |
| real-data 60-step direct MLP LocoProp-S, gamma 1, old denom scaling | `.opencode/locodiag_screen60.log` | final val 5.0387; final step_avg 683.12ms; peak allocated 37.3 GiB |
| real-data 60-step direct MLP LocoProp-S, gamma 4, old denom scaling | `.opencode/locodiag_gamma4_screen60.log` | final val 5.0265; final step_avg 684.05ms; peak allocated 37.3 GiB |
| real-data 60-step MLP `G/C` before NorMuon | `.opencode/locodiag_normuon_screen60.log` | final val 5.0237; final step_avg 686.04ms; peak allocated 37.3 GiB |
| real-data 60-step MLP normquarter before NorMuon | `.opencode/locodiag_normuon_normquarter_screen60.log` | final val 4.8794; final step_avg 686.33ms; peak allocated 37.3 GiB |
| real-data 60-step V/O normquarter requested | `.opencode/locodiag_vo_normquarter_screen60.log` | invalid attention-only run before optimizer gate fix; final val 4.8334; final step_avg 684.16ms; peak allocated 37.3 GiB |
| real-data 200-step baseline | `.opencode/baseline_screen200.log` | final val 3.8998; final step_avg 674.88ms; peak allocated 37.3 GiB |
| real-data 200-step V/O normquarter requested | `.opencode/locodiag_vo_normquarter_screen200.log` | invalid attention-only run before optimizer gate fix; final val 3.8937; final step_avg 683.35ms; peak allocated 37.3 GiB |
| real-data 60-step late-layer V/O normquarter requested | `.opencode/locodiag_vo_late_normquarter_screen60.invalid-gated.log` | invalid attention-only run before optimizer gate fix; final val 4.8492; final step_avg 675.39ms; peak allocated 37.3 GiB |

Current verdict: the direct MLP-only path is runtime-valid but not promotable.
The first NorMuon-composed raw `G/C` path is also not promotable: it is worse
than baseline in both early convergence and step time on the same 60-step screen.
Mean-normalized inverse-power variants are much more stable. The old
attention-only runs are not true V/O/QKVO optimizer evidence: the optimizer-side
preconditioner was incorrectly gated on MLP being enabled. That gate is now fixed,
so the next runs must rerun true attention-only ablations.

## First-hand cost estimate

Per optimizer step, the current world-size-1 schedule sees these total tokens:

| stage | total tokens/step | tokens/microbatch (`grad_accum_steps=8`) |
| --- | ---: | ---: |
| 1 | 131,072 | 16,384 |
| 2 | 262,144 | 32,768 |
| 3/ext | 393,216 | 49,152 |

All-surface diagonal capture reads roughly:

```text
(10 qkv inputs + 10 o inputs + 11 mlp_fc inputs) * 768
+ 11 mlp_proj inputs * 3072
= 57,600 feature elements per token
```

That is about 15.1 GB, 30.2 GB, and 45.3 GB of extra bf16 activation reads per
optimizer step in stages 1, 2, and 3. The writes are tiny: vectors totaling
about `75 * 768 = 57,600` fp32 scalars per microbatch if every logical surface
keeps a distinct diagonal.

The previous all-surface diagonal run slowed from the clean repeat control
(`931.476s`) to `945.054s`, about `+13.6s` total or about `+9.8ms/step`. Against
the other clean baseline (`937.278s`), the overhead is about `+5.6s` or
`+4.0ms/step`. That is consistent with the memory-traffic estimate plus launch
overhead.

The optimizer side can claw back less wallclock if feature Gram merely feeds
NorMuon, because it still pays Polar Express. That composed path is still worth
testing first because it preserves the current stabilizing optimizer structure
and is closer to the design doc's Newton-Muon rule.

## Inclusion threshold

Current clean H100 controls are `931.476s` and `937.278s` final train time for
1385 train steps, or about `672ms/step` to `677ms/step`.

Promotion should require both:

1. final validation loss not worse than baseline by more than about `0.002`
2. at least `2%` end-to-end train-time improvement before 8xH100, because
   one-rep timing noise and compile/warmup effects are already nontrivial

At current timing, `2%` is about `18s-19s` per full 1xH100 run, or
`13ms-14ms/step`. If a diagonal LocoProp-S variant adds `~8ms/step` of capture
overhead, it needs to save roughly 16 training steps just to break even, and
more than 35-40 steps to be a credible WR lever rather than noise.

## End-to-end capture plan

1. Add default-off compile-time env gates:
   - `LOCO_DIAG=0`
   - implemented now: `LOCO_DIAG_SURFACES=mlp_fc,mlp_proj,qk,v,o`
   - implemented now: `LOCO_DIAG_MODE=normuon|direct`
   - implemented now: `LOCO_DIAG_DENOM_SCALE`, defaulting to `grad_scale`
   - implemented now: `LOCO_DIAG_MLP_LAYERS` and `LOCO_DIAG_ATTN_LAYERS`
   - implemented now: `LOCO_DIAG_RIDGE`
   - `LOCO_DIAG_GAMMA`

2. Add model-owned fp32 accumulator buffers:
   - `attn_in_diag[10, 768]`
   - `attn_o_diag[10, 768]`
   - `mlp_fc_diag[11, 768]`
   - `mlp_proj_diag[11, 3072]`
   - matching count buffers if using mean feature Gram

3. Accumulate inside the compiled forward only when `LOCO_DIAG=1`:
   - after `attn_in_normed = norm(...)`, add `sum(attn_in_normed^2)`
   - after the attention output is gated/reassembled and before O projection,
     add `sum(attn_y^2)`
   - before `ReLUSqrdMLP(norm(x), ...)`, add `sum(mlp_input^2)`
   - inside or immediately after `FusedLinearReLUSquareFunction.forward`, add
     `sum(post^2)` for c_proj

4. After grad accumulation and before optimizer update:
   - for 1xH100, read local accumulators directly
   - for multi-GPU, all-reduce the diagonal buffers, because gradients are
     averaged across rank-local token shards
   - use sum-Gram scaling, matching the summed gradient convention, then reset
     buffers after update

5. In the optimizer, map bank row to logical feature diagonal:
   - `qk_bank`: `layer = global_idx // 6`; use `attn_in_diag[layer]`
   - `vo_bank`: `layer = global_idx // 2`; even rows use `attn_in_diag`, odd
     rows use `attn_o_diag`
   - `mlp_bank`: `layer = global_idx // 2`; even rows use `mlp_fc_diag`, odd
     rows use `mlp_proj_diag`

6. For `LOCO_DIAG_MODE=normuon`, precondition gradients before NorMuon:
   - `out x in`: divide gradient columns by `diag + ridge`
   - `in x out`: divide gradient rows by `diag + ridge`
   - then run existing momentum, Polar Express, variance reduction, cautious
     weight decay, and mantissa tracking

7. For `LOCO_DIAG_MODE=direct`, apply direct diagonal LocoProp-S update for
   selected matrices:
   - `out x in`: divide gradient columns by `diag + ridge`
   - `in x out`: divide gradient rows by `diag + ridge`
   - keep the existing cautious weight decay and mantissa tracking initially so
     the optimizer swap is isolated from the precision/regularization path

## Kernel plumbing plan

1. Reference phase:
   - use eager torch reductions and a compiled torch update helper
   - run only 1xH100 parity screens

2. Capture phase:
   - replace repeated torch reductions with one or two Triton reduction kernels
     that reduce `[tokens, features]` into fp32 vectors
   - for `mlp_proj`, prefer fusing the `post^2` accumulation into the existing
     `linear_relu_square_kernel` because `post` is already produced there

3. Update/precondition phase:
   - implemented now as compiled helpers for MLP:
     - column-preconditioned `out x in`
     - row-preconditioned `in x out`
   - for `normuon`, these helpers mutate fp32 gradients before Polar Express
   - for `direct`, they fuse weight decay, preconditioned update, and mantissa
     writes

4. Distributed phase:
   - add async all-reduce for diagonal buffers and overlap it with the existing
     gradient reduce-scatter where possible
   - verify that every rank uses the same global diagonal before updating its
     parameter shard

## Experiment order

1. CPU orientation check.
2. Local `py_compile` and static shape checks.
3. 1xH100 compile/backward smoke with `LOCO_DIAG=1` and
   `LOCO_DIAG_SURFACES=mlp_fc,mlp_proj`.
4. Short 1xH100 training screen with MLP-only `LOCO_DIAG_MODE=normuon`.
5. If MLP NorMuon-composed parity is acceptable, wire attention V/O next; only
   add QK after V/O is not obviously harmful.
6. Full 1xH100 baseline/control plus best feature-Gram NorMuon variant, two reps
   if the loss delta is within `0.002` or timing delta is under `2%`.
7. Only consider 8xH100 after loss parity and a clear 1x end-to-end win.
