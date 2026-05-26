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

Attention conclusion so far: O-only is cheap and improves the 60-step screen,
but it does not survive to 200 steps. V-only has a better 200-step loss but the
effect is too small for its step-time cost. V/O combined and late-layer V/O are
not useful.

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

## Current Next Actions

1. Commit/push this journal batch with the copied post-fix logs.
2. Continue layer-specific attention probes, starting with O-only layer subsets,
   because O-only is cheap and wins 60-step but fades in the full 200-step run.
3. If no attention layer subset survives, the current diagonal preconditioner is not
   speedrun-positive without kernel-side overhead removal or a stronger
   algorithmic variant.
