# Newton-Muon WR Synthesis

Branch: `codex/wr-fresh-20260526`

## Read Of WR History

The WR table says the largest jumps came from changing either optimization
geometry, the attention/computation regime, or the training objective plumbing:

- Muon itself moved the record from `31.4` to `24.9` minutes, then Muon
  improvements and distributed Muon took it to `13.1` minutes.
- Modern architecture changes (`ReLU^2`, zero-init projections, QK norm),
  value/embedding skips, logit softcap, U-net/value embeddings, FP8 head, QKV
  merging, and batch/lr schedule changes supplied the next large losses.
- FlexAttention and window/data-shape work were the next major algorithmic
  compute shifts.
- After the timing-rule reset, most improvements became smaller systems and
  schedule gains: faster all-reduce, reduce-scatter, Torch upgrades, FA3,
  transpose kernels, loss-head kernels, data loading, and activation/layout
  tuning.
- The last genuinely new optimizer-geometry record was NorMuon and its nearby
  follow-ups. Later optimizer entries are mostly placement, precision, grouping,
  Adam/Muon interleaving, or Q/K orthogonalization granularity.

That makes the feature-Gram line unusually plausible: it is a real optimizer
geometry change in a benchmark where the optimizer core has not had a large
conceptual move since NorMuon.

## Paper Read

Newton-Muon derives the update

```text
W <- W - eta * msgn(G (Z Z^T)^-1)
```

up to momentum and weight decay. The key claim is that Muon is an implicit
Newton-like method missing the right-side preconditioner from the input second
moment. The paper reports a Modded-NanoGPT-style Muon reproduction where this
right preconditioning reaches target validation loss in `6%` fewer steps and
about `4%` less wall time.

Primary sources checked:

- README WR table in this checkout, records `#1-#82`.
- Newton-Muon: https://arxiv.org/abs/2604.01472
- NorMuon: https://arxiv.org/abs/2510.05491
- Polar Express: https://arxiv.org/abs/2505.16932

This matches our best interpretation of the experiments:

- direct LocoProp-S is the wrong primary path because it replaces NorMuon/Polar
  Express;
- diagonal `C` is too weak or too noisy to prove useful alpha;
- full 768-dimensional V-input `C` changes the direction enough to move loss;
- MLP-proj's 3072-dimensional feature matrix is not WR-compatible except as
  diagonal/block/sketch, and its diagonal path was harmful.

## What We Learned

The important result is not any single screen; it is the pattern:

| family | result | read |
| --- | --- | --- |
| diagonal MLP | worse or faded | diagonal MLP, especially proj, is not the path |
| diagonal V/O | tiny or fading | diagonal signal exists but is below overhead/noise |
| full QK | `4.8402` at 60 | not toxic, but weaker than V |
| full QK+V | `4.8533` at 60 | interaction hurts current V signal |
| full O headwise | `4.8395` at 60, very slow | not first candidate |
| full V all layers | `3.8820` at 200 vs current baseline `3.8834` | real but marginal at 200; still slow |
| full V layers `0-1` | `4.8211` at 60, `3.8833` at 200 | strong early accelerator, fades |
| full V `0-1 END_STEP=100` | `3.8793` at 200 | best loss so far, not wall-clock viable on 1x |
| norminverse/no-norm | `4.8297` at 60 | cheaper, but lost too much signal |
| norminverse blend `0.50` | `4.8411` at 60 | over-application hurts |
| top-shrink | `4.8453` at 60 | top-eigenspace shrink alone is insufficient |

The strongest read:

```text
V-input eigensystem matters.
Literal inverse plus norm restoration keeps the useful direction.
Removing norm restoration or replacing inverse with top-shrink loses signal.
The cost problem is still every-step preconditioner application, not only refresh.
```

On `world_size=1`, owner-local does not reduce the layer count because the one
rank owns every V matrix. On `world_size=8`, owner-local should be much more
representative: each rank owns only its `vo_bank` shard. That means the current
1xH100 timing is pessimistic for the true distributed update path, but not
enough to justify an 8x launch before another short distributed smoke.

## Candidate To Keep Warm

Current best loss candidate:

```text
LOCO_FULL_SURFACES=v
LOCO_DIAG_ATTN_LAYERS=0-1
LOCO_FULL_END_STEP=100
LOCO_FULL_FILTER=inverse
LOCO_FULL_NORM_RESTORE=1
LOCO_FULL_LOCAL_STATS=1
LOCO_FULL_REFRESH_INTERVAL=8
LOCO_FULL_APPLY_INTERVAL=1
LOCO_FULL_RIDGE_REL=0.03
LOCO_FULL_BLEND_MAX=0.25
LOCO_FULL_PRECOND_DTYPE=fp32
```

Runner:

```bash
SCREEN_STEPS=200 SCREEN_VAL_EVERY=50 tools/run_newtonv_raw_v01_gate.sh
```

This is the candidate to remeasure first when a GPU is available. The cheaper
norminverse runner remains useful as a control, but it is no longer first in
queue.

## GPU-Ready Queue

For a fresh 1xH100 or Modal H100:

1. Run the Modal/Prime smoke: `nvidia-smi`, `nvcc`, `torch`, `kernels==0.11.7`,
   and a tiny `torchrun` compile.
2. Run a current-environment baseline screen if the image/hardware changed:
   `SCREEN_STEPS=200 SCREEN_VAL_EVERY=50` with no `LOCO_*` flags.
3. Run the raw V `0-1 END_STEP=100` gate:
   `SCREEN_STEPS=200 SCREEN_VAL_EVERY=50 tools/run_newtonv_raw_v01_gate.sh`.
4. If step-200 loss is still around `<=3.880` and timing is not worse than the
   same-environment baseline, run a second replicate.
5. If 1x remains wall-clock negative but loss positive, run a small 8-GPU smoke
   only to measure owner-local distributed overhead, not a full WR attempt.
6. Launch a full 8xH100 record attempt only after the distributed overhead smoke
   says the preconditioner path is near-baseline time.

Kill criteria:

- `60-step > 4.835` for the raw V candidate on comparable data/cache.
- `200-step >= baseline - 0.002`.
- non-refresh step time remains clearly above baseline after owner-local on
  multi-GPU.
- any QK/O combination is worse than the V-only queue on a 60-step screen.

## Implementation Notes Before Next GPU

- `tools/run_newtonv_raw_v01_gate.sh` is the prepared runner for the best raw
  inverse candidate.
- `tools/run_norminverse_v01_gate.sh` is retained for the failed cheap variant.
- `tools/run_newtonv_timing_triplet_gate.sh` is the clean cost-shape screen:
  run `baseline`, `noop`, then `active` with the same `SCREEN_STEPS` so we can
  split plain baseline cost from full-path compile/optimizer overhead and active
  preconditioner overhead.
- `tools/run_newtonv_block_power_gate.sh` is the next cheap Newton-Muon filter
  probe. It uses block `C` on the V input, spectral power/finite filters,
  static preconditioner norm, no per-step norm restoration, and fewer Polar
  Express iterations on the full-path operand. First candidate:

  ```bash
  SCREEN_STEPS=80 SCREEN_VAL_EVERY=20 tools/run_newtonv_block_power_gate.sh
  ```

  Then quickly test:

  ```bash
  LOCO_FULL_POWER_ALPHA=0.5 SCREEN_STEPS=80 SCREEN_VAL_EVERY=20 tools/run_newtonv_block_power_gate.sh
  LOCO_FULL_SHRINK_ONLY=1 LOCO_FULL_STATIC_NORM=0 SCREEN_STEPS=80 SCREEN_VAL_EVERY=20 tools/run_newtonv_block_power_gate.sh
  LOCO_FULL_FILTER=finite SCREEN_STEPS=80 SCREEN_VAL_EVERY=20 tools/run_newtonv_block_power_gate.sh
  ```

- Modal launch should pass runner-specific env through `MODAL_EXTRA_ENV_JSON`,
  for example:

  ```bash
  MODAL_RUNNER=tools/run_newtonv_timing_triplet_gate.sh \
  MODAL_EXTRA_ENV_JSON='{"NEWTONV_VARIANT":"baseline"}' \
  SCREEN_STEPS=120 SCREEN_VAL_EVERY=0 tools/run_modal_newtonv_raw_gate.sh
  ```

- `tools/modal_h100_probe.py` and `tools/modal_billing_check.sh` are ready, but
  Modal still needs the token secret half before they can authenticate.
- Do not spend 8xH100 on direct LocoProp-S or full MLP-proj.
