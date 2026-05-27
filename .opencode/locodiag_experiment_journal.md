# LocoDiag Experiment Journal

Branch: `codex/wr-fresh-20260526`

This is the rolling summary log for the active diagonal Feature-Gram /
LocoProp-S-on-NorMuon probe. Raw logs are copied into `.opencode/` after each
remote H100 run; this file records the decision-relevant result and next action.

## Baselines

| run | log | checkpoint | val_loss | train_time | step_avg | note |
| --- | --- | --- | ---: | ---: | ---: | --- |
| baseline | `.opencode/baseline_screen60.log` | 60 | 4.8502 | 40.365s | 672.76ms | 60-step reference |
| baseline | `.opencode/baseline_screen200.log` | 50 | 5.6502 | 18.000s | 360.00ms | 200-step reference |
| baseline | `.opencode/baseline_screen200.log` | 100 | 4.6931 | 46.212s | 462.12ms | 200-step reference |
| baseline | `.opencode/baseline_screen200.log` | 150 | 4.1320 | 85.215s | 568.10ms | 200-step reference |
| baseline | `.opencode/baseline_screen200.log` | 200 | 3.8998 | 134.977s | 674.88ms | 200-step reference |

## Invalidated Attention-Only Runs

These logs were generated before `1dd9139 Fix attention feature Gram
preconditioning`. They captured feature diagonals, but the optimizer-side
preconditioner was incorrectly gated on MLP being enabled. Treat them as
capture-overhead and variance probes, not true V/O/QKVO optimizer evidence.

| run | log | checkpoint | val_loss | step_avg | decision |
| --- | --- | --- | ---: | ---: | --- |
| requested V/O normquarter | `.opencode/locodiag_vo_normquarter_screen60.log` | 60 | 4.8334 | 684.16ms | invalid attention optimizer evidence |
| requested V/O normquarter | `.opencode/locodiag_vo_normquarter_screen200.log` | 200 | 3.8937 | 683.35ms | invalid attention optimizer evidence |
| requested late V/O normquarter | `.opencode/locodiag_vo_late_normquarter_screen60.invalid-gated.log` | 60 | 4.8492 | 675.39ms | invalid attention optimizer evidence |

## Post-Fix Attention Runs

All runs below use true optimizer preconditioning after `1dd9139`, with
`LOCO_DIAG_MODE=normuon`, `LOCO_DIAG_NORMUON_PRECOND=normquarter`,
`LOCO_DIAG_RIDGE_REL=0.01`, and `LOCO_DIAG_BLEND_STEPS=300` unless noted.

| run | log | checkpoint | val_loss | train_time | step_avg | decision |
| --- | --- | --- | ---: | ---: | ---: | --- |
| V/O all layers | `.opencode/locodiag_vo_normquarter_fixed_screen60.log` | 60 | 4.8523 | 41.056s | 684.27ms | true V/O is not the old win; drop as combined surface |
| V/O late layers 7-10 | `.opencode/locodiag_vo_late_normquarter_fixed_screen60.log` | 60 | 4.8552 | 40.489s | 674.82ms | timing ok but loss worse; drop late-layer V/O |
| V only | `.opencode/locodiag_v_normquarter_fixed_screen60.log` | 20 | 6.5194 | 7.337s | 366.86ms | strong early lead |
| V only | `.opencode/locodiag_v_normquarter_fixed_screen60.log` | 40 | 5.4018 | 20.852s | 521.29ms | still ahead |
| V only | `.opencode/locodiag_v_normquarter_fixed_screen60.log` | 60 | 4.8417 | 40.895s | 681.58ms | promising enough for 200-step |
| V only | `.opencode/locodiag_v_normquarter_fixed_screen200.log` | 50 | 5.6139 | 18.268s | 365.37ms | ahead, but slower |
| V only | `.opencode/locodiag_v_normquarter_fixed_screen200.log` | 100 | 4.6824 | 46.838s | 468.38ms | still ahead |
| V only | `.opencode/locodiag_v_normquarter_fixed_screen200.log` | 150 | 4.1310 | 86.345s | 575.63ms | nearly tied |
| V only | `.opencode/locodiag_v_normquarter_fixed_screen200.log` | 200 | 3.8987 | 136.660s | 683.30ms | tiny loss win, too much time cost; not promotable |
| V only, blend 100 | `.opencode/locodiag_v_blend100_normquarter_fixed_screen60.log` | 60 | 4.8583 | 41.004s | 683.39ms | stronger/faster warmup hurts; drop |
| O only | `.opencode/locodiag_o_normquarter_fixed_screen60.log` | 20 | 6.5277 | 7.241s | 362.03ms | early lead |
| O only | `.opencode/locodiag_o_normquarter_fixed_screen60.log` | 40 | 5.4054 | 20.632s | 515.80ms | ahead |
| O only | `.opencode/locodiag_o_normquarter_fixed_screen60.log` | 60 | 4.8393 | 40.494s | 674.90ms | best 60-step attention result; run 200-step |
| O only | `.opencode/locodiag_o_normquarter_fixed_screen200.log` | 50 | 5.6353 | 18.021s | 360.41ms | small early lead, baseline timing |
| O only | `.opencode/locodiag_o_normquarter_fixed_screen200.log` | 100 | 4.7024 | 46.292s | 462.92ms | worse than baseline; likely fading |
| O only | `.opencode/locodiag_o_normquarter_fixed_screen200.log` | 150 | 4.1377 | 85.341s | 568.94ms | worse than baseline |
| O only | `.opencode/locodiag_o_normquarter_fixed_screen200.log` | 200 | 3.9016 | 134.800s | 674.00ms | no loss parity; drop |
| O only, layers 0-5 | `.opencode/locodiag_o_early_normquarter_fixed_screen60.log` | 20 | 6.5455 | 7.249s | 362.46ms | weak early |
| O only, layers 0-5 | `.opencode/locodiag_o_early_normquarter_fixed_screen60.log` | 40 | 5.4553 | 20.645s | 516.12ms | worse than all-layer O |
| O only, layers 0-5 | `.opencode/locodiag_o_early_normquarter_fixed_screen60.log` | 60 | 4.8743 | 40.497s | 674.95ms | bad; drop early/mid O |
| O only, layers 7-10 | `.opencode/locodiag_o_late_normquarter_fixed_screen60.log` | 20 | 6.5727 | 7.252s | 362.60ms | bad early |
| O only, layers 7-10 | `.opencode/locodiag_o_late_normquarter_fixed_screen60.log` | 40 | 5.4573 | 20.640s | 515.99ms | bad |
| O only, layers 7-10 | `.opencode/locodiag_o_late_normquarter_fixed_screen60.log` | 60 | 4.8689 | 40.489s | 674.82ms | bad; drop late O |

Attention conclusion so far: O-only is cheap and improves the 60-step screen,
but it does not survive to 200 steps. V-only has a better 200-step loss but the
effect is too small for its step-time cost. V/O combined and late-layer V/O are
not useful. Early/mid O-only is actively bad, so the remaining layer hypothesis
was late O-only, which is also bad. The O all-layer 60-step win appears to be an
unstable interaction, not a useful layer-local improvement.

## Post-Fix MLP Split Runs

| run | log | checkpoint | val_loss | train_time | step_avg | decision |
| --- | --- | --- | ---: | ---: | ---: | --- |
| MLP fc only | `.opencode/locodiag_mlp_fc_normquarter_fixed_screen60.log` | 20 | 6.5291 | 7.275s | 363.73ms | early lead |
| MLP fc only | `.opencode/locodiag_mlp_fc_normquarter_fixed_screen60.log` | 40 | 5.4264 | 20.664s | 516.60ms | ahead of baseline but behind O/V |
| MLP fc only | `.opencode/locodiag_mlp_fc_normquarter_fixed_screen60.log` | 60 | 4.8568 | 40.547s | 675.78ms | fades and ends worse; drop |
| MLP proj only | `.opencode/locodiag_mlp_proj_normquarter_fixed_screen60.log` | 20 | 6.5658 | 7.300s | 365.01ms | worse early |
| MLP proj only | `.opencode/locodiag_mlp_proj_normquarter_fixed_screen60.log` | 40 | 5.4430 | 20.826s | 520.64ms | worse |
| MLP proj only | `.opencode/locodiag_mlp_proj_normquarter_fixed_screen60.log` | 60 | 4.8625 | 40.897s | 681.61ms | clear offender; drop |

MLP conclusion so far: `mlp_fc` alone gives an early bump but fades by step 60.
`mlp_proj` is clearly harmful and has much stronger gradient-norm distortion
than `mlp_fc`. The earlier combined-MLP harm was not a sign/transposition bug;
it is consistent with the noisy projection-feature diagonal hypothesis.

## Diagnostics Notes

- `LOCO_DIAG_LOG_STEPS=0,1,2,10,50,100` is enabled on focused runs.
- Gradient-ratio logs prove the true optimizer path is active post-fix.
- Step 0 MLP fc ratio can be zero because `c_fc` sees near-zero gradient before
  zero-initialized `c_proj` has moved.
- O feature diagonals are much heavier-tailed than V/attention-input diagonals,
  but O-only timing is closer to baseline than V-only.

## Newton-Muon Conversion Plan

The next implementation target is not direct LocoProp-S. It is a narrow
Newton-Muon-style probe that keeps the NorMuon/Polar-Express stack and inserts a
right-side input preconditioner after momentum and before Polar Express.

Same-environment baseline on the current H100/software stack:

| run | log | checkpoint | val_loss | train_time | step_avg | decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| current no-feature baseline | `.opencode/baseline_current_screen200.log` | 50 | 5.6283 | 24.957s | 499.13ms | authoritative comparison for current pod |
| current no-feature baseline | `.opencode/baseline_current_screen200.log` | 100 | 4.6782 | 75.419s | 754.19ms | much faster old baseline is stale for this environment |
| current no-feature baseline | `.opencode/baseline_current_screen200.log` | 150 | 4.1168 | 148.254s | 988.36ms | current stage timing matches full-V runs |
| current no-feature baseline | `.opencode/baseline_current_screen200.log` | 200 | 3.8834 | 242.543s | 1212.71ms | resets promotion threshold |
| full QK, FP32 inverse cache | `.opencode/newtonv_fullqk_fp32_screen60.log` | 20 | 6.5175 | 9.255s | 462.75ms | QK is not immediately toxic |
| full QK, FP32 inverse cache | `.opencode/newtonv_fullqk_fp32_screen60.log` | 40 | 5.4129 | 30.826s | 770.66ms | weaker than V paths |
| full QK, FP32 inverse cache | `.opencode/newtonv_fullqk_fp32_screen60.log` | 60 | 4.8402 | 67.420s | 1123.67ms | worse than early V; QK-only is not first candidate |
| full QK+V, FP32 inverse cache | `.opencode/newtonv_fullqk_v_fp32_screen60.log` | 20 | 6.5404 | 9.303s | 465.17ms | combined QK+V is worse early |
| full QK+V, FP32 inverse cache | `.opencode/newtonv_fullqk_v_fp32_screen60.log` | 40 | 5.4332 | 31.724s | 793.10ms | QK hurts V signal |
| full QK+V, FP32 inverse cache | `.opencode/newtonv_fullqk_v_fp32_screen60.log` | 60 | 4.8533 | 69.981s | 1166.36ms | reject QK+V |

Implemented locally after the diagonal screens:

- `LOCO_FULL_SURFACES=v` enables only the V matrix in `vo_bank`.
- The collected statistic is local/cadenced full `C = X.T @ X` from the
  768-dimensional normalized attention input, not the 3072-dimensional MLP
  projection feature.
- `LOCO_FULL_REFRESH_INTERVAL` gates collection; default `8`.
- `LOCO_FULL_LOCAL_STATS=1` avoids a per-refresh cross-rank all-reduce by
  default.
- `LOCO_FULL_EMA_BETA`, `LOCO_FULL_RIDGE_REL`, and
  `LOCO_FULL_DENOM_SCALE` control the cached Cholesky/inverse preconditioner.
- The optimizer path is `raw grad -> Nesterov operand -> cached right
  preconditioner -> norm-preserving blend -> Polar Express -> NorMuon variance
  reduction`.
- `LOCO_FULL_NOOP=1` keeps the collection/factorization/application overhead
  while setting blend to zero, so it is a wall-clock control rather than an
  algorithmic candidate.
- `LOCO_FULL_SURFACES=qk` reuses the same attention-input Gram for the Q/K bank
  and applies the cached right preconditioner after momentum before Polar
  Express.

Important correction after rerunning baseline: the older `3.8998 / 134.977s`
baseline is not apples-to-apples with the current pod/software/screen harness.
Use `.opencode/baseline_current_screen200.log` for current decisions. Against
that baseline, all-layer full V and early-layer pulse are small loss wins in the
same wall-clock class, not yet WR-ready evidence.
Full QK is implemented and validated at 60 steps, but it is weaker than V:
`4.8402` at 60 versus `4.8313` for all-layer V and `4.8211` for V layers `0-1`.
The next QK check is interaction with V, not QK-only promotion.
QK+V interaction is negative: `4.8533` at 60. QK should be deprioritized unless
a later full-run hypothesis specifically needs it.

First H100 screens to run after local validation:

| run | env delta | checkpoint | purpose |
| --- | --- | ---: | --- |
| full V noop | `LOCO_FULL_SURFACES=v LOCO_FULL_NOOP=1 LOCO_FULL_REFRESH_INTERVAL=8` | 60 | measure full-C overhead floor |
| full V Newton-Muon | `LOCO_FULL_SURFACES=v LOCO_FULL_REFRESH_INTERVAL=8 LOCO_FULL_BLEND_MAX=0.25 LOCO_FULL_RIDGE_REL=0.03` | 60 | first algorithmic signal |
| full V refresh16 | same, `LOCO_FULL_REFRESH_INTERVAL=16` | 60 | overhead/cadence tradeoff if refresh8 is too slow |

First H100 result:

| run | log | checkpoint | val_loss | train_time | step_avg | decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| full V noop, solve path | `.opencode/newtonv_fullv_noop_screen60.log` | 60 | 4.8410 | 143.449s | 2390.81ms | correctness smoke only; timed section included a compile |
| full V refresh8, solve path | `.opencode/newtonv_fullv_refresh8_screen60.log` | 60 | 4.8345 | 82.347s | 1372.46ms | real loss signal, but per-step Cholesky solve overhead is not viable |
| full V refresh8, inverse cache | `.opencode/newtonv_fullv_inv_refresh8_screen60.log` | 60 | 4.8156 | 68.812s | 1146.87ms | strong 60-step algorithmic hit, still too slow |
| full V refresh8, inverse cache | `.opencode/newtonv_fullv_inv_refresh8_screen200.log` | 50 | 5.6335 | 27.941s | 558.83ms | beats 200-step baseline curve |
| full V refresh8, inverse cache | `.opencode/newtonv_fullv_inv_refresh8_screen200.log` | 100 | 4.6906 | 80.499s | 804.99ms | persists at 100 |
| full V refresh8, inverse cache | `.opencode/newtonv_fullv_inv_refresh8_screen200.log` | 150 | 4.1139 | 156.564s | 1043.76ms | strong loss, slow |
| full V refresh8, inverse cache | `.opencode/newtonv_fullv_inv_refresh8_screen200.log` | 200 | 3.8809 | 254.437s | 1272.19ms | strong persistence, engineering cost too high |
| full V refresh8, inverse cache, end120 | `.opencode/newtonv_fullv_inv_end120_screen200.log` | 50 | 5.6179 | 29.913s | 598.27ms | early-only schedule still ahead |
| full V refresh8, inverse cache, end120 | `.opencode/newtonv_fullv_inv_end120_screen200.log` | 100 | 4.6889 | 82.215s | 822.15ms | similar to always-on |
| full V refresh8, inverse cache, end120 | `.opencode/newtonv_fullv_inv_end120_screen200.log` | 150 | 4.1214 | 155.994s | 1039.96ms | loses some mid-run gain |
| full V refresh8, inverse cache, end120 | `.opencode/newtonv_fullv_inv_end120_screen200.log` | 200 | 3.8840 | 250.488s | 1252.44ms | still strong, but not faster enough |
| full V owner-local, FP32 inverse cache | `.opencode/newtonv_fullv_owned_fp32_screen60.log` | 20 | 6.5133 | 8.707s | 435.35ms | post-plumbing validation; world=1 owns all layers |
| full V owner-local, FP32 inverse cache | `.opencode/newtonv_fullv_owned_fp32_screen60.log` | 40 | 5.3848 | 28.408s | 710.19ms | still ahead of baseline-like screen loss |
| full V owner-local, FP32 inverse cache | `.opencode/newtonv_fullv_owned_fp32_screen60.log` | 60 | 4.8313 | 61.398s | 1023.29ms | loss signal survives; speed still not WR on 1xH100 |
| full V owner-local, BF16 inverse cache | `.opencode/newtonv_fullv_owned_bf16_screen60.log` | 20 | 6.5417 | 8.926s | 446.30ms | BF16 is already worse by step 20 |
| full V owner-local, BF16 inverse cache | `.opencode/newtonv_fullv_owned_bf16_screen60.log` | 40 | 5.4171 | 30.008s | 750.20ms | BF16 loses loss and time |
| full V owner-local, BF16 inverse cache | `.opencode/newtonv_fullv_owned_bf16_screen60.log` | 60 | 4.8414 | 64.847s | 1080.78ms | reject BF16 cached-preconditioner matmul for now |
| full V owner-local, FP32 inverse cache | `.opencode/newtonv_fullv_owned_fp32_screen200.log` | 50 | 5.5947 | 23.959s | 479.17ms | strong early gain; stage-1 timing is tolerable |
| full V owner-local, FP32 inverse cache | `.opencode/newtonv_fullv_owned_fp32_screen200.log` | 100 | 4.6754 | 70.860s | 708.60ms | signal persists at 100 |
| full V owner-local, FP32 inverse cache | `.opencode/newtonv_fullv_owned_fp32_screen200.log` | 150 | 4.1113 | 140.762s | 938.41ms | still ahead; later stages dominate time |
| full V owner-local, FP32 inverse cache | `.opencode/newtonv_fullv_owned_fp32_screen200.log` | 200 | 3.8820 | 231.162s | 1155.81ms | post-patch persistence confirmed, still too slow on 1xH100 |
| full V layers 0-1, FP32 inverse cache | `.opencode/newtonv_fullv_layers0_1_fp32_screen60.log` | 20 | 6.5215 | 8.728s | 436.41ms | early two-layer subset is viable |
| full V layers 0-1, FP32 inverse cache | `.opencode/newtonv_fullv_layers0_1_fp32_screen60.log` | 40 | 5.3882 | 29.197s | 729.93ms | similar curve to all-layer full V |
| full V layers 0-1, FP32 inverse cache | `.opencode/newtonv_fullv_layers0_1_fp32_screen60.log` | 60 | 4.8211 | 64.234s | 1070.57ms | best post-plumbing 60-step result; promote to 200 |
| full V layers 0-1, FP32 inverse cache | `.opencode/newtonv_fullv_layers0_1_fp32_screen200.log` | 50 | 5.6109 | 25.480s | 509.61ms | weaker than all-layer at 50 |
| full V layers 0-1, FP32 inverse cache | `.opencode/newtonv_fullv_layers0_1_fp32_screen200.log` | 100 | 4.6613 | 72.306s | 723.06ms | better than all-layer at 100 |
| full V layers 0-1, FP32 inverse cache | `.opencode/newtonv_fullv_layers0_1_fp32_screen200.log` | 150 | 4.1178 | 140.197s | 934.65ms | fades behind all-layer by 150 |
| full V layers 0-1, FP32 inverse cache | `.opencode/newtonv_fullv_layers0_1_fp32_screen200.log` | 200 | 3.8833 | 227.467s | 1137.34ms | still ahead of baseline; slightly worse than all-layer full V |
| full V layers 7-10, FP32 inverse cache | `.opencode/newtonv_fullv_layers7_10_fp32_screen60.log` | 20 | 6.5388 | 8.677s | 433.84ms | late V is not the 60-step signal |
| full V layers 7-10, FP32 inverse cache | `.opencode/newtonv_fullv_layers7_10_fp32_screen60.log` | 40 | 5.4445 | 28.463s | 711.58ms | much worse than early/all-layer V |
| full V layers 7-10, FP32 inverse cache | `.opencode/newtonv_fullv_layers7_10_fp32_screen60.log` | 60 | 4.8640 | 61.288s | 1021.47ms | reject late-only V |
| full V layers 0-1, end100 | `.opencode/newtonv_fullv_layers0_1_end100_fp32_screen200.log` | 50 | 5.5969 | 25.501s | 510.03ms | better than 0-1 no-end at 50 |
| full V layers 0-1, end100 | `.opencode/newtonv_fullv_layers0_1_end100_fp32_screen200.log` | 100 | 4.6931 | 74.494s | 744.94ms | weak at 100; no early advantage this run |
| full V layers 0-1, end100 | `.opencode/newtonv_fullv_layers0_1_end100_fp32_screen200.log` | 150 | 4.1143 | 147.653s | 984.35ms | recovers by 150 |
| full V layers 0-1, end100 | `.opencode/newtonv_fullv_layers0_1_end100_fp32_screen200.log` | 200 | 3.8793 | 241.799s | 1209.00ms | best loss so far, but not wall-clock viable |
| full V layers 0-1, end100, apply every 2 | `.opencode/newtonv_fullv_layers0_1_end100_apply2_fp32_screen200.log` | 50 | 5.6250 | 25.347s | 506.94ms | weaker than apply-every-step |
| full V layers 0-1, end100, apply every 2 | `.opencode/newtonv_fullv_layers0_1_end100_apply2_fp32_screen200.log` | 100 | 4.6908 | 75.472s | 754.72ms | no useful speed win |
| full V layers 0-1, end100, apply every 2 | `.opencode/newtonv_fullv_layers0_1_end100_apply2_fp32_screen200.log` | 150 | 4.1211 | 148.546s | 990.31ms | worse loss, same cost class |
| full V layers 0-1, end100, apply every 2 | `.opencode/newtonv_fullv_layers0_1_end100_apply2_fp32_screen200.log` | 200 | 3.8893 | 242.317s | 1211.58ms | reject apply cadence 2 |

Follow-up implementation change: cache an explicit inverse/preconditioner on
refresh and use a matrix multiply in the optimizer step. This keeps the
Newton-Muon semantics but moves the expensive triangular solve off the per-step
path.

Persistence verdict: full V is real algorithmic alpha. The final 200-step loss
gain is `0.0189` versus baseline (`3.8998 -> 3.8809`), much larger than the
diagonal V signal. It is not a WR candidate at current speed, so the next work is
pure plumbing.

Next plumbing patch:

- With `LOCO_FULL_LOCAL_STATS=1`, collect full Grams only for V layers owned by
  this rank's `vo_bank` shard.
- Factor/cache preconditioners only for owned V layers.
- Add `LOCO_FULL_PRECOND_DTYPE=bf16` to test BF16 cached-preconditioner matmul
  after the FP32 owner-local check.
- Log refresh-step and non-refresh-step timing separately.

Owner-local/BF16 verdict:

- On `world_size=1`, owner-local correctly reports all V layers owned, so this
  run validates the code path but does not exercise the expected 8-rank work
  reduction.
- FP32 owner-local kept the 60-step loss signal (`4.8313`) and improved over the
  prior inverse-cache timing, but it remains too slow for a record attempt on a
  single H100 (`1023.29ms/step`).
- BF16 preconditioner matmul is not useful as implemented: it was slower
  (`1080.78ms/step`) and worse in loss (`4.8414`) than FP32.
- Timing split from the FP32 run: refresh steps averaged `1265.87ms` and
  non-refresh steps averaged `982.06ms`, so reducing the every-step
  preconditioner/application path matters as much as reducing refresh spikes.
- The post-patch 200-step run confirmed persistence: `3.8820` versus baseline
  `3.8998`, essentially preserving the earlier full-V final gain while reducing
  average step time from `1272.19ms` to `1155.81ms`.
- Layer subset `LOCO_DIAG_ATTN_LAYERS=0-1` improved the 60-step result to
  `4.8211`, better than all-layer post-patch full V. Its single-GPU timing did
  not improve, which points to compiled-path overhead or later-stage schedule
  cost rather than only the raw count of preconditioned V matrices.
- The same `0-1` subset persisted to 200 but faded: it was better than all-layer
  at 100 (`4.6613` versus `4.6754`) but worse at 150/200 (`3.8833` final versus
  `3.8820`). The subset is still a good early-accelerator candidate, not a clear
  replacement for all-layer full V.
- Late-only V (`LOCO_DIAG_ATTN_LAYERS=7-10`, attention indices 6-9) was bad:
  `4.8640` at 60. This supports the read that the full-V signal is early-layer
  dominated, with later layers possibly helping persistence only when combined
  with the early layers.
- Early `0-1` with `LOCO_FULL_END_STEP=100` produced the best final loss so far
  (`3.8793`) but was slower than always-on `0-1` and all-layer runs. The
  optimizer already disables full-V application after `END_STEP`; the remaining
  cost is the first 100 active steps plus the base schedule, not a zero-blend
  matmul bug.
- `LOCO_FULL_APPLY_INTERVAL=2` did not help. It worsened final loss to `3.8893`
  and did not materially reduce wall time, so the current 1xH100 cost is not
  dominated by applying the cached inverse on skipped optimizer steps.

## Current Next Actions

1. Run layer-subset full-V probes to see whether a small set of V layers carries
   enough of the signal to cut single-GPU cost.
2. Do not pursue BF16 cached-preconditioner matmul further unless the kernel
   path changes.
3. Run a same-environment 200-step baseline on the current pod before using the
   older baseline timing/loss as a promotion gate.
4. For 1xH100, focus next on reducing every-step preconditioner cost or limiting
   full-V to fewer layers/steps; for 8xH100, remeasure owner-local because each
   rank will own only a subset of V layers.

## QK/O Surface Checks

| run | log | checkpoint | val_loss | train_time | step_avg | decision |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| headwise full O, FP32 inverse cache | `.opencode/newtonv_fullo_headwise_fp32_screen60.log` | 20 | 6.5519 | 9.245s | 462.27ms | not an early loss hit |
| headwise full O, FP32 inverse cache | `.opencode/newtonv_fullo_headwise_fp32_screen60.log` | 40 | 5.4137 | 100.230s | 2505.76ms | one-time refresh compile spike made timing unusable |
| headwise full O, FP32 inverse cache | `.opencode/newtonv_fullo_headwise_fp32_screen60.log` | 60 | 4.8395 | 134.701s | 2245.01ms | reject as current candidate |
| full V top-shrink r64 t1 clip2 apply4 | `.opencode/newtonv_fullv_topshrink_r64_t1_clip2_apply4_screen60.log` | 20 | 6.5495 | 9.325s | 466.23ms | no early V-inverse loss signal |
| full V top-shrink r64 t1 clip2 apply4 | `.opencode/newtonv_fullv_topshrink_r64_t1_clip2_apply4_screen60.log` | 40 | 5.4214 | 31.285s | 782.11ms | faster than dense V, but worse loss |
| full V top-shrink r64 t1 clip2 apply4 | `.opencode/newtonv_fullv_topshrink_r64_t1_clip2_apply4_screen60.log` | 60 | 4.8453 | 68.499s | 1141.66ms | reject first low-rank shrink filter |

Headwise O is cheaper in principle than dense 768-wide V, but the current
compiled path hit a `~74s` refresh compile spike at step 25 and still landed
behind the best V screens. The O Gram diagonal is much more heavy-tailed by step
50 (`p99=1.1395e5`, `max=2.4055e5`), and the preconditioned O operand norm ratio
had already moved to `~0.971`. This is not a reason to promote O before fixing
the V path.

## Low-Rank V Filter Plan

Implemented next: `LOCO_FULL_FILTER=topshrink` for V/QK attention-input Grams.
The refresh path eigendecomposes normalized `C`, caches top-rank eigenvectors
and finite-time shrink deltas, and the optimizer applies
`M <- M + blend * (M U diag(delta) U.T)` after momentum and before Polar
Express. It deliberately does no per-step norm restoration. First screen:

```text
LOCO_FULL_SURFACES=v
LOCO_FULL_FILTER=topshrink
LOCO_FULL_SHRINK_RANK=64
LOCO_FULL_SHRINK_T=1.0
LOCO_FULL_SHRINK_CLIP=2.0
LOCO_FULL_APPLY_INTERVAL=4
LOCO_FULL_REFRESH_INTERVAL=8
LOCO_FULL_RIDGE_REL=0.03
```

Verdict: the first top-shrink filter did not preserve the useful full-V inverse
loss signal. It avoided the catastrophic O refresh compile spike, but finished
at `4.8453`, behind full QK (`4.8402`), full O (`4.8395`), all-layer full V
inverse (`4.8313` post-plumbing), and V layers `0-1` (`4.8211`). This suggests
the current full-V win is not explained by top-eigenspace shrink alone at
`rank=64`, `t=1`, `clip=2`, `apply_interval=4`; either the inverse/bottom
eigenspace amplification matters, the shrinker needs a stronger application
schedule, or the low-rank approximation is too lossy.

## Next V 0-1 Candidate

The current best candidate should be restored to the front of the queue:

```text
LOCO_FULL_SURFACES=v
LOCO_DIAG_ATTN_LAYERS=0-1
LOCO_FULL_END_STEP=100
LOCO_FULL_FILTER=norminverse
LOCO_FULL_NORM_RESTORE=0
LOCO_FULL_REFRESH_INTERVAL=8
LOCO_FULL_APPLY_INTERVAL=1
LOCO_FULL_RIDGE_REL=0.03
LOCO_FULL_BLEND_MAX=0.25
```

`norminverse` caches the inverse of normalized
`(C + rho * mean_diag * I) / ((1 + rho) * mean_diag)` and therefore can skip the
two per-step matrix norms used by the original dense inverse path. This is the
right follow-up to `V 0-1 END_STEP=100`: it keeps the inverse eigensystem signal
instead of replacing it with top-shrink, while directly testing whether norm
restoration was a material part of the remaining every-step cost. If this loses
the signal, fall back to the existing raw inverse + norm-restore candidate and
replicate `V 0-1 END_STEP=100` before promoting.

Runnable gate command:

```bash
SCREEN_STEPS=60 tools/run_norminverse_v01_gate.sh
```

If the 60-step screen lands at or below `4.825` without a large timing
regression, promote the same script with `SCREEN_STEPS=200 SCREEN_VAL_EVERY=50`.
