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

## Current Next Actions

1. Commit/push owner-local full-V collection/factorization and BF16/timing
   instrumentation.
2. Keep the current H100 alive for focused plumbing screens.
3. Run owner-local FP32 60-step first.
4. If the loss signal survives, run owner-local BF16 60-step.
5. Promote only a near-baseline-time variant to another 200-step run.
