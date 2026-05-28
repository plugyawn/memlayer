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

## Modal Update - 2026-05-27

The fresh Modal H100 suite demotes the current Newton-V candidates. Raw logs and
parsed tables are in `.opencode/newtonv_modal_results_20260527.md`.

Short 80-step screen:

| case | val loss | step avg |
| --- | --- | --- |
| baseline | `4.5380` | `450.74ms` |
| no-op full path | `4.5231` | `451.94ms` |
| active dense inverse | `4.5186` | `453.32ms` |
| best block filter | `4.5315` | `466.46ms` |

Promotion 200-step screen:

| case | step 50 | step 100 | step 150 | step 200 |
| --- | --- | --- | --- | --- |
| baseline | `5.6052` | `4.6861` | `4.1150` | `3.8837` |
| all-layer inverse, window `0-48` | `5.5893` | `4.6956` | `4.1265` | `3.8954` |
| layers `0-1`, end step `100` | `5.5970` | `4.6782` | `4.1145` | `3.8875` |

Read:

```text
The short-screen V signal remains real.
The current inverse schedules fade by 200 steps.
The block/power filters did not rescue the cost or preserve the loss gain.
The current branch should not launch a WR attempt without a new hypothesis.
```

The strongest read:

```text
V-input eigensystem matters.
Literal inverse plus norm restoration keeps the useful direction.
Removing norm restoration or replacing inverse with top-shrink loses signal.
The cost problem is still every-step preconditioner application, not only refresh.
The 200-step problem is now at least as important as the cost problem.
```

On `world_size=1`, owner-local does not reduce the layer count because the one
rank owns every V matrix. On `world_size=8`, owner-local should be much more
representative: each rank owns only its `vo_bank` shard. That means the current
1xH100 timing is pessimistic for the true distributed update path, but not
enough to justify an 8x launch before another short distributed smoke.

## Candidate Status

The previous best loss candidate was:

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

The Modal promotion run remeasured this family and landed at `3.8875` versus
the same-suite baseline `3.8837`, so it is no longer a WR candidate as-is. Keep
the runner for reproducibility, not for automatic promotion.

The follow-up Modal H100 ladder added 120-step init-aware screens. It did not
rescue the original Newton-V schedule:

| case | step 120 | read |
| --- | --- | --- |
| baseline | `4.1813` | control |
| V all `0-48`, polar4 | `4.1923` | worse |
| V `0-1 END_STEP=100`, polar4 | `4.1908` | worse |
| V `0-1 32-80`, polar4 | `4.1864` | still worse |
| V `0-1 48-112`, polar4 | `4.1793` | small positive |
| QK `32-80`, polar4 | `4.1874` | worse |
| O headwise `32-80`, polar4 | `4.1809` | tiny positive |

That points to an init/schedule issue, not a simple `polar_iters=4` fix. The
next principled test is to decouple collection and application windows:
collect `C` early, apply the preconditioner later.

The warm-metric Modal H100 ladder tested that directly. It worked mechanically,
but did not produce a durable win:

| case | step 80 | step 120 | read |
| --- | --- | --- | --- |
| baseline | `4.6326` | `4.1832` | control |
| V `0-1`, collect `0-48`, apply `48-112`, polar4 | `4.6256` | `4.1829` | tiny final positive |
| V `0-1`, collect `0-64`, apply `48-112`, polar4 | `4.6282` | `4.1846` | faded/worse |
| O, collect `0-64`, apply `48-112`, polar4 | `4.6339` | `4.1861` | worse |
| V+O `0-1`, collect `0-64`, apply `48-112`, polar4 | `4.6248` | `4.1847` | step-80 hit faded |

This demotes warm collection alone. The next active hypothesis is
overpreconditioning: `M C^{-1}` may be useful, but then full-strength
Polar/NorMuon variance reduction may erase or distort the correction. Commit
`62e7097` added `LOCO_FULL_SKIP_VARRED=1` plus an `overprecond` suite to test
that without changing the rest of the optimizer.

The overpreconditioning ladder produced the strongest same-suite result so far:

| case | step 80 | step 120 | read |
| --- | --- | --- | --- |
| baseline | `4.6244` | `4.1869` | control |
| warm V no-op polar4 | `4.6108` | `4.1798` | full-path no-op is strong |
| warm V active polar5 | `4.6183` | `4.1821` | worse than no-op |
| warm V active polar4 | `4.6182` | `4.1763` | best result |
| warm V active polar4, skip varred | `4.6192` | `4.1784` | worse than keeping varred |

The actionable synthesis changed:

```text
Use V 0-1, collect 0-64, apply 48-112.
Use LOCO_FULL_POLAR_ITERS=4.
Keep NorMuon variance reduction.
Always include the no-op full-path control.
```

Important caveat from the post-run audit: the overprecond no-op used the
timing-triplet runner's default `LOCO_DIAG_ATTN_LAYERS=all`, while the active
raw V cases used layers `0-1`. Active polar4 still beat a strong no-op, but it
was not a matched no-op control. The future `overprecond` and `overpromote`
suites now force `LOCO_DIAG_ATTN_LAYERS=0-1` for the no-op path.

The 200-step matched overpromote gate landed after this. It did not promote
Newton-specific V:

```text
baseline:                    3.8882
V 0-1 no-op polar4:          3.8918
V 0-1 no-op polar5:          3.8856
all-V no-op polar4:          3.8851
V 0-1 active polar5:         3.8869
V 0-1 active polar4:         3.8887
```

The best result was all-V no-op polar4, not active Newton-V. This means the
strongest current signal is the full after-momentum optimizer path itself:
explicit Nesterov operand, `polar_express_from_operand`, and NorMuon variance
reduction under the window schedule. The cached V-input right preconditioner is
not the winning part of this 200-step ladder.

This was not a pure early-speedup result. The best no-op controls were worse at
step 50 and only won by step 200, so the mechanism is likely a trajectory or
regularization change in the VO-bank optimizer path rather than a simple early
loss accelerator.

Important implementation nuance: the full-path switch is bank-level. Once
`LOCO_FULL_SURFACES=v` activates the `vo_bank`, the whole VO bank uses the
explicit after-momentum path. Layer selection controls feature collection and
the identity/preconditioner helper, not which matrices use
`polar_express_from_operand`.

Mechanism note: `LOCO_FULL_NOOP=1` is not the same as baseline. During the
apply window it sets the full-path blend to zero, but still routes the selected
matrix bank through:

```text
raw grad -> Nesterov operand -> full-path helper with blend=0
         -> polar_express_from_operand(LOCO_FULL_POLAR_ITERS)
         -> NorMuon variance reduction
```

So the no-op control is really a polar/full-path schedule ablation. The matched
200-step ladder says this ablation is currently more promising than
right-preconditioned Newton-V.

## Right-Preconditioner Read

Do not read the overpromote miss as "input geometry is useless." The stronger
and more defensible read is:

```text
The current literal Newton-V payload did not beat the matched VO-bank full-path
schedule, but the right-preconditioner family remains the mathematically
correct object to test.
```

Why:

- Newton-Muon's claim is exactly that Muon neglects the right preconditioning
  induced by the input second moment.
- LocoProp-S reaches the same right-factor through local affine squared-loss
  optimization.
- K-FAC reaches the same object as the activation covariance factor in a
  Kronecker approximation to natural gradient.
- Our own full-V inverse runs showed algorithmic signal before the matched
  no-op controls exposed the schedule confound.

What failed locally is more specific:

```text
raw/near-literal C^{-1}
+ weak/restarted blend in a short warm window
+ already tuned Polar/NorMuon normalization
+ VO-bank full-path schedule confound
```

That does not falsify right preconditioning. It says the right next question is
not "V or no V?" but "what filter f(C), what schedule, and what matched
Muon/Polar baseline?"

The next Newton-family test, after the schedule-only proof, should be
schedule-matched:

```text
baseline: ordinary NorMuon/Polar
control:  VO-bank schedule-only full path
treatment: same VO-bank schedule + damped f(C)
```

Candidate right filters should avoid unbounded bottom-eigenspace amplification:

```text
finite-time inverse, clipped:      h_t(lambda)
power inverse, clipped:            lambda^-alpha with alpha <= 0.5
top-eigenspace shrink only:        I + U_top (s - 1) U_top^T
relative-ridge normalized inverse: (C + rho mean_diag I)^-1, normalized
```

Literal `C^{-1}` stays a reference, not the final answer. Promotion requires
beating the schedule-only control, not just the ordinary baseline.

## Diagnostic Predictions

The next diagnostic run should not be judged only by loss. It should tell us
whether the intended right-preconditioning mechanism is present.

What would support the mechanism:

```text
1. C is anisotropic:
   eig_cond and eig_p99/eig_p50 are meaningfully above 1.

2. The unblended target is not tiny:
   target_delta is nontrivial even when applied delta is small because blend is
   still warming.

3. The update changes in the C eigenbasis in the right direction:
   gain_corr_target is negative, and high_low_target < high_low_before.

4. C does not commute with the update's right geometry:
   comm_norm and offdiag_frac are nontrivial. If C is diagonal in the right
   singular basis of the Nesterov operand, exact polar will erase the
   preconditioner.

5. The effect is stable across steps/layers:
   the sign and order of magnitude persist after the first refresh, not just at
   one noisy early point.

6. Polar does not erase it:
   postpolar delta is nontrivial versus the same Nesterov operand without
   f(C). If postpolar cos is essentially 1, the right filter is being absorbed
   before it can matter.
```

What would falsify the current literal Newton-V form:

```text
1. C is nearly identity or the target_delta is tiny.
2. gain_corr_target is near zero or positive.
3. high_low_target increases, meaning high-feature-variance directions are not
   actually being suppressed.
4. comm_norm/offdiag_frac are near zero, meaning C mostly only rescales the
   right singular directions Muon will discard anyway.
5. postpolar delta is near zero even when target_delta is nontrivial.
6. target_delta is huge and target_cos is low, suggesting C^-1 is rotating too
   sharply for the tuned Polar/NorMuon stack.
```

The key ambiguity to resolve is "too weak" versus "wrong shape." If applied
delta is tiny but target_delta/gain_corr look right, the next move is schedule
or blend. If target_delta is large but unstable, the next move is clipped
finite-time inverse or power inverse, not stronger literal inverse.

The exact-sign caveat matters: `polar(G C^-1)` can only beat `polar(G)` through
changing singular subspaces, not through keeping Newton singular values. If the
logs show low commutator/off-diagonal mass but high raw target_delta, the
preconditioner is mostly doing work that exact Muon discards. If the commutator
is high but post-Polar delta is low, practical Polar/NorMuon is washing out the
useful rotation.

Prepared follow-up suite if the diagnostic run supports "right metric exists,
literal inverse is too sharp":

```text
NEWTONV_SUITE=rightfilter
```

It matches baseline and schedule-only controls against:

```text
inverse V 0-1, polar4
topshrink V 0-1, rank 64, t=1, clip=2
dense finite-time inverse V 0-1, t=1, clip=2
dense power inverse V 0-1, alpha=0.5, clip=2
```

## Reference Mismatch

The public Newton-Muon reproduction code is not the same experiment as our
current Newton-V ladder. The reference implementation:

```text
applies inverse activation covariance before momentum
uses PRECOND_EVERY=16
uses PRECOND_EWMA=0.80
uses ridge = 0.2 * trace(C) / d
preconditions packed QKV together, O, MLP expansion, and blockwise MLP contraction
```

Our current branch has mostly tested a narrower, after-momentum V/O/QK variant
with weaker ridge. That is still a valid speedrun probe, but it is not a
faithful reproduction of the paper's NanoGPT claim.

Prepared follow-up suite for the ordering/damping question:

```text
NEWTONV_SUITE=paperstyle
```

This does not yet reproduce the full paper surface set, but it tests the most
important mismatch for V: precondition raw grad before momentum with
`refresh=16`, `ema=0.8`, and `ridge_rel=0.2`. It also includes a QK+V shared
attention-input-Gram case, which is closer to the reference packed-QKV
treatment. Full MLP block parity is more invasive because the current fused MLP
path does not cheaply expose the 4x768 block feature Grams.

## GPU-Ready Queue

For a fresh 1xH100 or Modal H100:

1. Run the Modal/Prime smoke: `nvidia-smi`, `nvcc`, `torch`, `kernels==0.11.7`,
   and a tiny `torchrun` compile.
2. Run a current-environment baseline screen if the image/hardware changed:
   `SCREEN_STEPS=200 SCREEN_VAL_EVERY=50` with no `LOCO_*` flags.
3. Do not rerun the old raw V `0-1 END_STEP=100` gate unless it is needed as a
   control.
4. Do not continue the current Newton-V promotion path without a new reason.
   The matched 200-step ladder failed the promotion rule.
5. Next isolate the full-path/no-op schedule with feature-stat work removed,
   and run sparse right-preconditioner diagnostics in the same H100 window if
   time permits.
   The target controls are baseline, no-refresh VO-bank no-op polar5,
   no-refresh VO-bank no-op polar4, all-window polar5/polar4 no-refresh
   controls, and matching collection-enabled no-op replicates.
   Prepared suite: `NEWTONV_SUITE=schedule_diag`.
   `LOCO_FULL_SCHEDULE_ONLY=1` preserves the explicit VO-bank after-momentum
   path but disables feature collection, factor refresh, preconditioner helper
   calls, and full-stat buffer allocation.
   Diagnostic cases enable `LOCO_FULL_LOG_PRECOND=1` and
   `LOCO_FULL_LOG_SPECTRUM=1`, plus eigenbasis energy and post-Polar survival
   checks, then parse with `tools/parse_loco_full_diagnostics.py`.
   Promotion bar: no-stats schedule-only must beat same-suite baseline by
   `>=0.003` at 200 steps, match or beat the collection-enabled no-op replicate,
   and keep non-refresh timing within roughly `2-3%` of baseline.
6. Only if the no-op schedule keeps a `>=0.002` 200-step gain with near-baseline
   timing should it get an 8-GPU smoke.
7. Launch a full 8xH100 record attempt only after both the 200-step loss gate
   and distributed overhead smoke are positive.

Kill criteria:

- `60-step > 4.835` for the raw V candidate on comparable data/cache.
- `200-step >= baseline - 0.002`.
- non-refresh step time remains clearly above baseline after owner-local on
  multi-GPU.
- any QK/O combination is worse than the V-only queue on a 60-step screen.

## Implementation Notes Before Next GPU

- `LOCO_FULL_METRIC_POLAR=1` is now the exact Cholesky-whitener probe for the
  activation-metric polar update:

  ```text
  Q = polar(G L^-T) L^-1, where C_lambda = L L^T
  ```

  The cached Cholesky is built from the mean-normalized activation Gram so the
  outside `L^-1` does not inherit raw token-count scale. This tests "Muon in
  whitened input coordinates" rather than Newton-Muon's `polar(G C^-1)` endpoint.
  It is intentionally gated and defaults to no norm restoration when enabled.
  Prepared suite:

  ```bash
  NEWTONV_SUITE=metricpolar MP_STEPS=120 MP_VAL_EVERY=40 tools/run_newtonv_experiment_suite.sh
  ```

  First comparisons: baseline, schedule-only polar4, Cholesky metric V `0-1`
  polar4/polar5, then QK+V `0-1` polar4.

  Promotion result on Modal H100, 200 steps:

  ```text
  baseline:                 3.8859, 670.37ms/step
  qk+v 0-1 metric polar4:   3.8859, 663.17ms/step
  qk+v 0-1 blend100:        3.8933, 660.27ms/step
  ```

  The 120-step QK+V metric-polar hit did not persist to 200. Blend100 briefly
  improved the 50-step screen (`5.6039` vs `5.6099`) but was worse by 100, 150,
  and 200. Treat this as "metric-polar has early surface sensitivity but needs
  damping/window/scale tuning", not as a hot surface-expansion candidate. Do not
  run `NEWTONV_SUITE=metricsurfaces` unless a later tuned promotion restores a
  200-step loss gain.

- `NEWTONV_SUITE=preconddiag` measured why the current right-preconditioner is
  not surviving as a WR candidate. The unblended target is a large rotation:

  ```text
  V 0-1 polar4 target_delta: 1.10-1.16
  V 0-1 polar4 target_cos:   0.32-0.39
  all-V polar4 target_delta: 1.11-1.20
  all-V polar4 target_cos:   0.28-0.38
  ```

  But the restarted blend window makes the actual pre-Polar operand nearly
  baseline:

  ```text
  step 50 blend=0.0017 actual_delta~0.0019
  step 80 blend=0.0267 actual_delta~0.031
  step 112 blend=0.0533 actual_delta~0.059
  ```

  Post-Polar deltas are larger but still modest: roughly `5-15%` for V `0-1`
  and `4-14%` averaged over all V layers. This supports the "washed away"
  hypothesis: the feature metric is not weak, but the applied correction is
  extremely damped and then further compressed by Polar/NorMuon.

  Follow-up run:

  ```bash
  NEWTONV_SUITE=paperfilter
  ```

  This tested schedule-matched controls, paper-style damping
  (`ridge_rel=0.2`, `refresh=16`, `ema=0.8`), preconditioning before momentum,
  faster bounded blend (`max=0.10`, `steps=32`), and finite/power clipped
  filters. Modal H100 result, 120 steps:

  ```text
  baseline:             4.1851, 572.28ms/step
  V 0-1 no-op polar4:   4.1803, 572.24ms/step
  V 0-1 inverse:        4.1834, 570.48ms/step
  all-V finite clipped: 4.1861, 574.58ms/step
  all-V power 0.5:      4.1866, 575.01ms/step
  ```

  The active filters did not beat the same-suite no-op/polar4 control. Also,
  the finite/power cases were mislabeled `v01`; they actually ran all V layers
  because the block-power runner defaulted `LOCO_DIAG_ATTN_LAYERS=all`. The
  suite is now patched so future paper-filter finite/power cases are genuinely
  V `0-1`.

  Code-audit caveat: the paperfilter active cases also set
  `LOCO_FULL_APPLY_BEFORE_MOMENTUM=1`, and before-momentum full-preconditioning
  falls back through the baseline fused `polar_express` path. Therefore their
  `polar4` label did not mean a true four-iteration `polar_express_from_operand`
  ablation; only the after-momentum full path honors `LOCO_FULL_POLAR_ITERS`.
  Treat paperfilter as a paper-style damping/before-momentum screen, not as a
  clean polar4 comparison.

  Current read: the feature metric still seems real in diagnostics, but this
  damping/filter family is not the next promotion path until it can beat a
  layer-correct no-op in the same suite.

- The same code audit found that `NEWTONV_SUITE=rightfilter` had the same
  finite/power `v01` default-layer bug. It is now patched so those cases force
  `LOCO_DIAG_ATTN_LAYERS=0-1`.

- Result-audit subagent read after the paperfilter run: active Newton-specific
  variants have not yet beaten no-op/full-path controls at 200, but the
  feature metric is mechanically real. The cleanest unresolved branch is
  V-only activation-metric polar: `metricpolar` showed a 120-step V `0-1`
  positive (`4.1802` vs baseline `4.1840` and schedule-only no-op `4.1868`),
  while only QK+V was promoted to 200 and tied baseline. The next suite is:

  ```bash
  NEWTONV_SUITE=metricv_promote
  ```

  It runs a 200-step baseline, V `0-1` full no-op polar4, V `0-1`
  metric-polar polar4 with the original ridge/blend/no-norm settings, and a
  safer ridge `0.20` / blend `0.10` / norm-restore variant. This directly tests
  `polar(G L^-T) L^-1` on the clean V surface and requires beating the matched
  no-op, not merely the ordinary baseline.

- Theory/literature subagent read: Newton-Muon, K-FAC, LocoProp, and
  Shampoo/SOAP all support the same broad idea, namely that the right activation
  covariance is a real missing factor. The unsettled speedrun choice is not
  whether the factor exists, but its spectral transfer function and placement:
  raw `C^-1`, clipped/power/finite inverse, or activation-metric
  `polar(G C^-1/2) C^-1/2`. The subagent's strongest theory recommendation was
  an MLP `c_fc` activation-metric/power ladder because `c_fc` is a 768-dim
  clean affine surface and avoids QK logit coupling. Current branch full-matrix
  support is only `qk,v,o`; MLP support is diagonal-only. Treat MLP `c_fc`
  full/metric as the next implementation branch if V-only metric-polar fails to
  beat no-op but diagnostics still say the right metric is surviving.

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

## Cycle 3, Revised Next Ladder

At `2026-05-27 21:29 IST`, the next H100 slot is still held until about
`22:06 IST` by the one-hour think/run cadence. PR233 is explicitly out of
scope; continue only on this branch.

The next run should be `NEWTONV_SUITE=paper_v_promote`, not broad surface
expansion. It is a 200-step, no-op-matched V `0-1` ladder:

```text
pvp_baseline
pvp_v01_noop_before_r020_blend010
pvp_v01_noop_after_polar4
pvp_finite_v01_before_r020_blend010
pvp_power05_v01_before_r020_blend010
pvp_inverse_v01_before_r020_blend010
pvp_cholmetric_v01_after_r020_blend005_norm
```

Why this ladder:

```text
1. The only persistent active signal remains full V inverse.
2. Prior active variants did not beat no-op/full-path controls at 200.
3. Paper-style Newton-Muon uses stronger damping than our first V screens:
   ridge_rel about 0.2, refresh 16/32, EMA 0.8/0.95.
4. Before-momentum variants need a before-momentum no-op control because
   LOCO_FULL_POLAR_ITERS only affects the after-momentum operand path.
5. Metric-polar keeps C^-1/2 outside Polar, so test it only as a damped V-only
   safety probe before touching QK/O again.
```

Promotion rule for this ladder:

```text
At 200 steps, an active treatment must beat both the ordinary baseline and the
matched no-op path by at least about 0.003 loss. A pure baseline win without a
no-op win is not enough.
```

More precise interpretation:

```text
B  = pvp_baseline @200
NB = pvp_v01_noop_before_r020_blend010 @200
NA = pvp_v01_noop_after_polar4 @200
A  = best(finite, power0.5, inverse) @200
M  = pvp_cholmetric_v01_after_r020_blend005_norm @200

Promote paper-style V only if:
  A <= B - 0.003 and A <= NB - 0.002 and A <= NA - 0.002.

Promote metric-polar V only if:
  M <= B - 0.003 and M <= NB - 0.002 and M <= NA - 0.002
  and M <= A - 0.002.

If NB or NA wins by these margins, the Newton-specific claim is dead for this
suite and the no-op/schedule path is the thing to isolate.
```

Runner audit before launch:

```text
The suite env vars do propagate through the nested runner scripts because env
does not clear inherited variables. To avoid accidental caller-state leakage,
run_case now explicitly unsets LOCO_* controls before applying each case's
case-local assignments.

Before-momentum cases still use the baseline fused polar_express path, so
LOCO_FULL_POLAR_ITERS is not a true polar4 knob for those cases. The
before-momentum no-op is therefore the matching control for finite/power/inverse
paper-style cases. The after-momentum no-op polar4 remains the matching control
for the metric-polar V safety case.
```

Launch command after the cadence window:

```bash
NANOGPT_MODAL_GPU=H100 \
MODAL_RUNNER=tools/run_newtonv_experiment_suite.sh \
MODAL_EXTRA_ENV_JSON='{"NEWTONV_SUITE":"paper_v_promote","NEWTONV_SUITE_LABEL":"modal_paper_v_promote_h100_20260527","PVP_STEPS":"200","PVP_VAL_EVERY":"50"}' \
SCREEN_STEPS=200 SCREEN_VAL_EVERY=50 \
tools/run_modal_newtonv_raw_gate.sh
```

Result on Modal H100:

```text
pvp_baseline:                              3.8794, 1590.01ms/step
pvp_v01_noop_before_r020_blend010:         3.8858,  709.20ms/step
pvp_v01_noop_after_polar4:                 3.8887,  713.78ms/step
pvp_finite_v01_before_r020_blend010:       3.8899,  712.27ms/step
pvp_power05_v01_before_r020_blend010:      3.8960,  713.71ms/step
pvp_inverse_v01_before_r020_blend010:      3.8855,  713.39ms/step
pvp_cholmetric_v01_after_r020_blend005:    3.8843,  712.87ms/step
```

The baseline timing included two large compile/cache stalls, so do not compare
step time literally against the later cases. The loss result is still decisive:
no active paper-style V filter beat baseline, and no active filter beat its
matched no-op by a useful margin. The metric-polar safety probe was the best
active treatment but still lost to baseline by `0.0049`.

Decision:

```text
Kill V 0-1 right-preconditioning as a WR candidate in this branch.
Do not run more V-only H100 sweeps unless a new implementation changes the
surface, placement, or interaction with Muon/NorMuon materially.
```

Next implementation branch, if continuing the right-preconditioner thesis:

```text
Narrow full/metric MLP c_fc only. It is the clean 768-dimensional surface that
the paper-family theory still supports, but current branch does not implement
full MLP support yet. Keep it 1xH100 only until it beats its own no-op.
```

## Cycle 4: MLP c_fc Full-Matrix Path

Prepared a narrow `mlp_fc` full feature-Gram path for the next H100 window.
Scope is deliberately limited to the first MLP affine matrix:

```text
surface: mlp_fc only
feature: mlp_in = norm(x), dimension 768
parameter bank: even global mlp_bank indices only
excluded: c_proj / 3072-dimensional post-ReLU feature
```

Implementation additions:

```text
LOCO_FULL_SURFACES=mlp_fc
owner-local collection/factorization via mlp_bank shard ownership
[num_layers,768,768] Gram/EMA/Cholesky/inverse buffers
before-momentum inverse and after-momentum inverse/metric-polar helpers
```

Prepared suite:

```text
NEWTONV_SUITE=mlpfc
MFC_STEPS=120
MFC_LAYERS=0-1
MFC_COLLECT_WINDOWS=0-64
MFC_WINDOWS=48-112
```

Promotion rule:

```text
Do not promote unless an active mlp_fc treatment beats same-suite baseline and
the same-suite mlp_fc no-op by at least ~0.002 at 120. If it does, repeat at
200 before widening layers.
```

Result:

```text
mfc_baseline:                                 4.1828
mfc_noop_after_polar4:                        4.1816
mfc_inverse_before_r020_blend010:             4.1781
mfc_inverse_after_polar4_r020_blend010:       4.1814
mfc_cholmetric_after_polar4_r020_blend005:    4.1788
```

Read:

```text
MLP c_fc now has a real same-suite active signal at 120.
Before-momentum inverse beats baseline by 0.0047 and no-op by 0.0035.
Metric-polar also beats baseline/no-op, but slightly trails before-momentum
inverse at the final screen.
After-momentum inverse is mostly a no-op-level result.
```

Next run:

```text
NEWTONV_SUITE=mlpfc_promote
MFP_STEPS=200
MFP_LAYERS=0-1
```

200-step promote result:

```text
mfp_baseline:                                3.8869
mfp_noop_after_polar4:                       3.8852
mfp_inverse_before_r020_blend010:            3.8832
mfp_cholmetric_after_polar4_r020_blend005:   3.8873
```

Read:

```text
Before-momentum MLP c_fc inverse persisted to 200 and beat both the baseline
and the after-polar4 no-op, but the no-op gap is narrow at 0.0020.
Metric-polar did not persist.
```

Immediate next control:

```text
NEWTONV_SUITE=mlpfc_before_control
```

This runs only the true before-momentum no-op and the same before-momentum
inverse. If the active line does not beat this matched no-op, the apparent MLP
c_fc signal is not clean enough to tune further.

Matched before-momentum control result:

```text
mbc_noop_before_r020_blend010:     3.8824
mbc_inverse_before_r020_blend010:  3.8887
```

Decision:

```text
Kill MLP c_fc before-momentum inverse as a current WR candidate.
The 120/200-step positive read was mostly an ordering/window/full-path effect,
not reliable right-preconditioner geometry.
```

Prepared next H100 scan:

```text
NEWTONV_SUITE=surface_control
SC_STEPS=120
SC_LAYERS=0-1
```

This pairs QK, O, and QKVO activation-metric-polar probes with same-surface
no-op controls. Active-only surface screens are no longer trusted.

Surface-control 120-step result:

```text
sc_baseline:                  4.1777
sc_qk_noop_metric_polar4:     4.1865
sc_qk_cholmetric_polar4:      4.1938
sc_o_noop_metric_polar4:      4.1810
sc_o_cholmetric_polar4:       4.1843
sc_qkvo_noop_metric_polar4:   4.1801
sc_qkvo_cholmetric_polar4:    4.1761
```

Read:

```text
QK and O are cold in this configuration.
QKVO is the only matched-control hit: active beats no-op by 0.0040 and baseline
by 0.0016 at 120. This is small but worth a narrow 200-step promotion because
it is the first surface-combination signal that survives its own no-op.
```

Next run:

```text
NEWTONV_SUITE=qkvo_metric_promote
QMP_STEPS=200
QMP_LAYERS=0-1
```

QKVO metric promote result:

```text
qmp_baseline:                 3.8945
qmp_qkvo_noop_metric_polar4:  3.8948
qmp_qkvo_cholmetric_polar4:   3.8900
```

Read:

```text
QKVO 0-1 activation-metric polar is the current best surviving
right-preconditioner result. It beats the matched no-op by 0.0048 and the
same-suite baseline by 0.0045 at 200.
```

Next:

```text
Run the same qkvo_metric_promote suite at 120 steps with QMP_LAYERS=0-3.
If widened QKVO keeps a no-op-matched signal, promote the widened case to 200.
If not, replicate QKVO 0-1 before spending more time on tuning.
```

QKVO 0-3 screen:

```text
qmp_baseline:                 4.1873
qmp_qkvo_noop_metric_polar4:  4.1744
qmp_qkvo_cholmetric_polar4:   4.1833
```

Decision:

```text
Do not widen QKVO to 0-3 in this form. The full-path/window no-op is strong,
but the active metric-polar update loses to it by 0.0089 at 120.
Return to QKVO 0-1 and replicate the 200-step matched-control win.
```

QKVO 0-1 replicate:

```text
qmp_baseline:                 3.8856
qmp_qkvo_noop_metric_polar4:  3.8869
qmp_qkvo_cholmetric_polar4:   3.8872
```

Decision:

```text
The QKVO 0-1 metric-polar 200-step win did not replicate. Treat the active
metric result as variance-scale, not promotion-ready. The stronger repeated
observation is that full-path/window controls can move loss substantially.
```

Next isolation:

```text
NEWTONV_SUITE=qkvo_schedule
QS_STEPS=200
QS_LAYERS=0-3
```

This tests whether the strong QKVO 0-3 no-op/window signal survives as a
schedule-only full-path change without feature-stat/preconditioner work.

QKVO schedule/full-path isolation:

```text
qs_baseline:                    3.8824, 684.54ms/step
qs_qkvo_schedule_only_polar4:   3.8867, 669.62ms/step
qs_qkvo_noop_metric_polar4:     3.8881, 669.80ms/step
```

Decision:

```text
The QKVO 0-3 no-op/window result did not survive a same-suite 200-step
isolation. Schedule-only led at 50/100 but faded by 150 and lost by 200.
Full-path no-op also lost by 200. Treat broad QKVO control wins as
variance/early-pulse effects until a stronger active line appears.
```

Current synthesis:

```text
The right-preconditioner thesis is not dead, but the robust evidence has
narrowed again. The full-V inverse result remains the cleanest active
right-preconditioning hit we have seen. QKVO metric-polar had one positive
200-step run, failed its 0-1 replicate, failed 0-3 active widening, and its
schedule/full-path controls faded by 200.
```

V activation-metric promotion:

```text
mvp_baseline:                                3.8845
mvp_v01_noop_polar4:                        3.8876
mvp_cholmetric_v01_polar4_r003_blend025:    3.8892
mvp_cholmetric_v01_polar4_r020_blend010_norm 3.8844
```

Read:

```text
The safe/norm-restored V activation-metric update is not a WR candidate yet,
but it is the cleanest active matched-control result from this cycle. It beats
the V no-op by 0.0032 at 200 and ties baseline, after showing a much larger
step-150 gain. The signal faded after the 48-112 window ended, so the next
question is windowing, not broader surface search.
```

V activation-metric extended-window probe:

```text
48-160 baseline:       3.8861
48-160 V no-op:        3.8876
48-160 V metric safe:  3.8915
```

Read:

```text
Leaving the safe V metric on longer is worse. The 48-112 result should be
interpreted as a pulse with delayed benefit, not as a sign that more metric
application is better.
```

V activation-metric shifted-window probe:

```text
80-144 baseline:       3.8844
80-144 V no-op:        3.8850
80-144 V metric safe:  3.8864
```

Read:

```text
Shifting the safe V metric window later does not preserve the step-150 pulse
into the 200-step endpoint. The 80-144 active case loses to baseline and no-op
at 100, 150, and 200. Stop V metric-window tuning unless a new implementation
changes the update semantics materially.
```

V spectral-shape pulse probe:

```text
160-step baseline A:       4.0069
160-step baseline B:       4.0068
V no-op polar4:            4.0030
V metric-polar safe:       4.0080
V power alpha=0.5:         4.0066
V power alpha=0.75:        4.0098
```

Read:

```text
Changing the V transfer function does not rescue the 0-1 pulse. The no-op
path is the best line in the same suite. Metric-polar, C^-0.5, and C^-0.75 all
fail to beat it. The diagnostics are still useful: V Grams are anisotropic and
the metric update is not mathematically null, but the applied blended update is
small and the loss curve does not reward it.
```

Current decision:

```text
The right-preconditioner axis remains theoretically sound, but this branch's
V 0-1 post-momentum pulse is no longer the right WR lever. Further V work
needs a semantic change, not another window/ridge sweep. The most suspicious
remaining interaction is NorMuon variance reduction after the metric/power
update: it can leave optimizer-state tails and may erase or reweight the
intended right-preconditioned direction. If we test V again, the next probe
should isolate variance reduction or apply the metric in a form that does not
fight the post-polar NorMuon normalization.
```

QKVO power-shape probe:

```text
160-step baseline:         3.9992
QKVO no-op polar4:         4.0051
QKVO power alpha=0.5:      4.0061
QKVO power alpha=0.75:     4.0211
```

Read:

```text
Broad QKVO right-preconditioning is not rescuing the line. The power filters
are mechanically active: QK/O target deltas are roughly 0.45-0.53 in the active
window, V target deltas are roughly 0.34-0.42, and post-polar QK deltas reach
about 0.15-0.18. The update is not being washed to zero. The loss simply
dislikes this broad attention-surface filter, and stronger spectral power is
worse.

This shifts the diagnosis away from "we need more surface coverage" and toward
"we need the right placement/normalization contract." Q/K are especially
entangled with softmax logits and entropy, O-headwise has a different metric
structure, and V remains the cleanest attention value regression surface. The
next productive probe should isolate the NorMuon variance-reduction interaction
or test a narrower shrink-only form, not increase alpha or widen QKVO.
```

V variance-reduction interaction:

```text
160-step baseline:             4.0065
V no-op polar4:                4.0061
V no-op polar4 skip-varred:    4.0073
V metric with varred:          4.0090
V metric skip-varred:          4.0080
```

Read:

```text
Skipping NorMuon variance reduction is not enough. It does not make the V
metric endpoint positive, and it worsens the matched no-op endpoint. That
weakens the "post-polar variance reduction is erasing the signal" hypothesis.

The one remaining lead is temporal: V metric skip-varred has a large step-50
hit, 5.5670 versus 5.5911 baseline and 5.5839 no-op, but fades by step 75 and
is worse by step 100. The metric is not washed out mechanically; it is too
strong or useful for too short a window. If we spend another H100 slice, the
only V metric follow-up worth running is a short-pulse screen such as 48-56
and 48-64. Longer V windows, broader QKVO, and stronger spectral powers should
not be promoted.
```

Short-pulse result:

```text
120-step baseline:              4.1902
V no-op polar4 48-56:           4.1832
V metric skip-varred 48-56:     4.1835
V no-op polar4 48-64:           4.1851
V metric skip-varred 48-64:     4.1842
```

Read:

```text
The shortest pulse preserved the early benefit, but the right-preconditioner
still did not add alpha. The best line is the 48-56 no-op/polar4 path. It beats
baseline at 50/75/100/120, and the active metric version is effectively tied
but slightly worse at the endpoint.

This changes the immediate WR lever: promote the cheap schedule/path effect,
not Newton-V. Before spending on a 200-step run, strip the feature-stat work
with LOCO_FULL_SCHEDULE_ONLY=1 and verify that a 48-56 polar4 pulse reproduces
the no-op win. If schedule-only holds, it is a plausible low-overhead optimizer
schedule tweak. If schedule-only fails, the no-op result is likely tied to the
feature-stat path or noise and should not be promoted.
```

Schedule-pulse control:

```text
120-step baseline:                      4.1799
V no-op polar4 48-56:                   4.1854
V schedule-only polar4 48-56:           4.1894
V schedule-only polar4 48-64:           4.1823
```

Read:

```text
The short V schedule lead did not reproduce. The same-suite baseline is better
than the 48-56 full no-op path, and stripping stats with SCHEDULE_ONLY makes
the 48-56 arm worse. The 48-64 schedule-only arm is the closest control, but it
still loses at 75/100/120. This kills the immediate "cheap polar4 pulse" WR
promotion.

The broader conclusion is unchanged but sharper: the current V implementation
can make mechanically nonzero right-preconditioned updates, and the exact
Cholesky metric-polar object has been tested, but the stable endpoint win is
not there. More V window/schedule tuning is now low value.
```

Current direction:

```text
Focus on the remaining 768-dimensional surface with a real same-code hint:
MLP-fc. Prior MLP-fc screens showed a small 200-step endpoint improvement for
before-momentum inverse, but a follow-up no-op-before control looked even
better. The next useful experiment is not another V run; it is a same-run
MLP-fc isolation with baseline, no-op-before, and active inverse-before.
```

MLP-fc before-momentum control:

```text
200-step baseline:                       3.8853
MLP-fc schedule-only before:             3.8909
MLP-fc no-op before, stats path:         3.8795
MLP-fc inverse before:                   3.8875
```

Read:

```text
The MLP-fc right-preconditioner did not survive the matched control. The
active inverse-before line is mechanically active, but it loses to baseline at
200 and is far worse than the zero-blend no-op-before control. The no-op
control's grad ratio is exactly 1.0, so its endpoint win is not an applied
Newton-Muon update.

This is the strongest warning so far that the screens are sensitive to control
path, compile path, or run noise at the 0.005-loss scale. Any future claim
must beat a matched no-op control, not just the baseline. By that standard,
current V, QKVO-power, and MLP-fc active preconditioners have not produced a
WR-ready signal.
```

Updated operating rule:

```text
Do not promote an active right-preconditioner unless it beats both:
  1. same-suite baseline
  2. same-suite no-op/control with identical stats and optimizer routing

If the no-op/control wins, log it as an optimizer-path/control effect and
separate it from Newton-Muon evidence.
```

MLP-fc replicate:

```text
Run A:
  baseline:        3.8853
  schedule-only:   3.8909
  no-op before:    3.8795
  inverse before:  3.8875

Run B:
  baseline:        3.8863
  schedule-only:   3.8808
  no-op before:    3.8907
  inverse before:  3.8789
```

Read:

```text
The MLP-fc result is mixed rather than dead. The first controlled run made
inverse look bad and no-op look good; the direct replicate made inverse best
and no-op bad. Averaging the two runs gives inverse-before around 0.0026 loss
better than baseline, but the ordering instability is too large to promote
yet.

This is now the only Newton-Muon/right-preconditioner line with a plausible
200-step mean after matched controls. V and broad QKVO power are lower priority.
The next decision should be a third MLP-fc before-control replicate, not a new
surface sweep.
```

MLP-fc three-run read:

```text
200-step means:
  baseline:        3.8873
  schedule-only:   3.8850
  no-op before:    3.8872
  inverse before:  3.8846

150-step means:
  baseline:        4.1232
  schedule-only:   4.1191
  no-op before:    4.1205
  inverse before:  4.1145
```

Read:

```text
MLP-fc inverse-before is now the best active right-preconditioner remaining,
but it is marginal at 200. The 150-step mean is meaningfully better, which
suggests the preconditioner can accelerate the middle of the run but does not
carry enough endpoint advantage under this window/blend.

The practical next lever is not "more C^{-1} everywhere"; it is making this
MLP-fc before-momentum signal survive to the endpoint with a cleaner schedule:
shorter or decayed application, lower blend, or a control-matched window study.
Do not call it WR-ready until it beats schedule-only by more than the current
0.0004 mean gap at 200.
```

MLP-fc window160 probe:

```text
200-step same-suite result:
  baseline:        3.8893
  schedule-only:   3.8860
  no-op before:    3.8902
  inverse before:  3.8828

150-step same-suite result:
  baseline:        4.1198
  schedule-only:   4.1223
  no-op before:    4.1210
  inverse before:  4.1139
```

Read:

```text
Extending the active MLP-fc before-momentum window to 48-160 is the first
post-control result where the active right-preconditioner clearly beats both
same-suite controls at the endpoint. The active inverse gain is 0.0065 over
baseline and 0.0032 over schedule-only at 200, with a larger 150-step gain.

This does not make it WR-ready. It is still one replicate, and the Modal timing
path has a shared late-run slowdown that makes wall-clock conclusions dirty.
But it changes the next action: replicate window160 first. If it survives, the
next principled comparison is MLP-fc Cholesky metric-polar / half-whitening
against this inverse-before path, not another broad V or QKVO sweep.
```

MLP-fc window160 replicate:

```text
200-step r2 result:
  baseline:        3.8832
  schedule-only:   3.8862
  no-op before:    3.8834
  inverse before:  3.8880

Two-run window160 means:
  baseline:        3.8863
  schedule-only:   3.8861
  no-op before:    3.8868
  inverse before:  3.8854
```

Read:

```text
Window160 did not reproduce strongly. The first run was a clean active-inverse
hit, but the replicate made inverse-before the worst endpoint arm despite a
very good step-50 anchor. The two-run mean is still slightly positive, but the
edge is below promotion quality and not cleaner than the control noise.

The right conclusion is not "MLP-fc C^{-1} is solved"; it is "input metric
information is mechanically active but unstable under hard inverse-before
Muonization." The next high-information test is the Cholesky metric-polar /
half-whitened MLP-fc update, because that explicitly keeps a metric factor
after the polar step instead of relying on C^{-1} to only rotate the operand.
```

MLP-fc Cholesky metric-polar window160:

```text
200-step result:
  baseline:             3.8820
  no-op after polar4:   3.8862
  inverse before:       3.8856
  cholmetric after:     3.8896

100-step result:
  baseline:             4.7130
  no-op after polar4:   4.6839
  inverse before:       4.6764
  cholmetric after:     4.6713

150-step result:
  baseline:             4.1177
  no-op after polar4:   4.1170
  inverse before:       4.1270
  cholmetric after:     4.1150
```

Read:

```text
The exact Cholesky metric-polar update is mechanically active and is not just
washed out by the matrix-sign step: it was the best arm at 100 and 150.
However, with the 48-160 window it became the worst endpoint arm.

This supports the "right metric, wrong schedule/strength" interpretation more
than the "input metric is useless" interpretation. The next test is the same
metric-polar MLP-fc comparison with a shorter 48-112 active window. If that
still loses at 200, deprioritize MLP-fc metric-polar and move back to surface
selection or a much smaller blend.
```

MLP-fc Cholesky metric-polar window112:

```text
200-step result:
  baseline:             3.8829
  no-op after polar4:   3.8873
  inverse before:       3.8831
  cholmetric after:     3.8846

100-step result:
  baseline:             4.6831
  no-op after polar4:   4.6941
  inverse before:       4.6790
  cholmetric after:     4.6734

150-step result:
  baseline:             4.1234
  no-op after polar4:   4.1258
  inverse before:       4.1211
  cholmetric after:     4.1188
```

Read:

```text
Shortening the active metric-polar window to 48-112 did not preserve the
endpoint. Metric-polar was again best at 100 and 150, then lost at 200.
This makes "window too long" an incomplete explanation.

The remaining plausible MLP-fc metric-polar lever is strength. The update is
not washed out, but blend 0.05 appears too strong or too persistent. Add a
runner knob and run MFP_METRIC_BLEND_MAX=0.02 on the 48-112 suite before
deprioritizing the half-whitened MLP-fc branch.
```

MLP-fc Cholesky metric-polar window112, blend 0.02:

```text
200-step result:
  baseline:             3.8842
  no-op after polar4:   3.8886
  inverse before:       3.8816
  cholmetric after:     3.8871

100-step result:
  baseline:             4.6788
  no-op after polar4:   4.6928
  inverse before:       4.6648
  cholmetric after:     4.6744

150-step result:
  baseline:             4.1229
  no-op after polar4:   4.1177
  inverse before:       4.1160
  cholmetric after:     4.1199
```

Read:

```text
Lower blend did not fix MLP-fc metric-polar. The half-whitened update is
mechanically active, but its endpoint behavior remains worse than baseline and
worse than inverse-before. Do not spend the next H100 block on more
metric-polar MLP-fc strength tweaks unless there is a new implementation
reason.

The useful arm in this suite is MLP-fc inverse-before on layers 0-1, window
48-112. It beat baseline by 0.0026 and no-op-after by 0.0070. Because the
control placement is different, the next high-information experiment is the
matched before-momentum control ladder: baseline, schedule-only-before,
noop-before, inverse-before on the same layers/window.
```

MLP-fc before-control window112:

```text
200-step result:
  baseline:        3.8846
  schedule-only:   3.8915
  no-op before:    3.8849
  inverse before:  3.8852

100-step result:
  baseline:        4.6697
  schedule-only:   4.6884
  no-op before:    4.6903
  inverse before:  4.6801

150-step result:
  baseline:        4.1150
  schedule-only:   4.1190
  no-op before:    4.1203
  inverse before:  4.1227
```

Read:

```text
The Cycle 18 MLP-fc inverse-before hit was not control-stable. With matched
before-momentum controls, literal C^-1 loses to baseline and no-op at 200.
This should stop inverse-repeat spending for MLP-fc.

The remaining MLP-fc question is whether the input eigensystem helps when the
spectral transfer is bounded. The next suite should test power C^-0.5 and a
finite-time inverse on c_fc with the same before-momentum placement and
matched no-op. This follows the "C^-1 is a reference point, not the final
filter" lesson.
```

MLP-fc filter-control window112:

```text
200-step result:
  baseline:        3.8870
  no-op before:    3.8909
  inverse before:  3.8828
  power C^-0.5:    3.8858
  finite t=1:      3.8856

150-step result:
  baseline:        4.1212
  no-op before:    4.1235
  inverse before:  4.1129
  power C^-0.5:    4.1202
  finite t=1:      4.1260
```

Read:

```text
On c_fc, the bounded filters did not beat literal inverse. Power and finite
are mildly positive at 200, but inverse has the only meaningful same-suite
margin: 0.0042 over baseline and 0.0081 over no-op.

The uncomfortable part is reproducibility. The previous matched-control run
had inverse at 3.8852 versus baseline 3.8846 and no-op 3.8849. So the axis is
not dead, but it is brittle and late-acting. The next test should lower blend
to 0.05 on the same before-control ladder. If lower blend wins, tune strength.
If it loses, the practical conclusion is that MLP-fc C^-1 has too much
variance for WR use in this branch.
```

Lower-blend MLP-fc before-control result:

```text
mbc_baseline:                          3.8878
mbc_schedule_only_before_r02_blend005: 3.8800
mbc_noop_before_r02_blend005:          3.8855
mbc_inverse_before_r02_blend005:       3.8815
```

Read:

```text
Blend 0.05 made inverse-before look healthier than the prior matched-control
miss, but it still did not beat the schedule-only-before arm. The current hot
fork is therefore not "MLP-fc C^-1 works"; it is "the before-momentum full-path
schedule/window may be a cheap optimizer change, and C^-1 may add some but not
enough on this replicate."

The immediate GPU priority is an exact replicate of the lower-blend
before-control suite. If schedule-only repeats, promote a dedicated no-stats
schedule isolation. If inverse overtakes schedule-only, continue tuning c_fc
right-preconditioning strength. Do not widen surfaces until this fork is
resolved.
```

The exact lower-blend replicate resolved this fork in favor of c_fc inverse:

```text
                 run A    run B    mean
baseline         3.8878   3.8881   3.8880
schedule-only    3.8800   3.8860   3.8830
no-op before     3.8855   3.8864   3.8860
inverse before   3.8815   3.8815   3.8815
```

Read:

```text
MLP-fc layers 0-1, window 48-112, ridge 0.2, blend 0.05 is now the cleanest
surviving right-preconditioner line. It is stable across two runs and clears
the matched no-op by about 0.0045 on average.

The schedule-only run-A spike should not be promoted. In before-momentum mode
with schedule-only enabled, the code skips the preconditioner and falls through
the ordinary fused polar_express update. Its variability is useful as a noise
estimate, not as a mechanism.

Next: run a c_fc inverse strength ladder at 0.025/0.05/0.075/0.10 before
touching broader surfaces.
```

The strength ladder demoted the c_fc line:

```text
mbg_baseline:                      3.8797
mbg_noop_before_r02:               3.8848
mbg_inverse_before_r02_blend0025:  3.8810
mbg_inverse_before_r02_blend005:   3.8924
mbg_inverse_before_r02_blend0075:  3.8856
mbg_inverse_before_r02_blend010:   3.8847
```

Read:

```text
The c_fc inverse signal exists but is not a controlled WR lever yet. The same
configuration that previously landed at 3.8815 landed at 3.8924 inside the
strength ladder, and the best active strength still lost to the same-suite
baseline. This is too brittle to scale.

Move the next GPU block back toward the Newton-Muon paper mismatch: attention
input factors, before momentum, ridge 0.2, refresh 16, EMA 0.8, and QK+V/all
coverage. That tests the paper-like packed attention-input preconditioner
rather than the brittle c_fc slice.
```

The paper-style attention-input sweep partially supports the thesis:

```text
ps_baseline:                    3.8849
ps_v01_before_polar5_ridge020:  3.8874
ps_v01_before_polar4_ridge020:  3.8854
ps_vall_before_polar5_ridge020: 3.8822
ps_qkv_before_polar5_ridge020:  3.8819
```

Read:

```text
The right-preconditioner effect is not captured by V layers 0-1 alone in this
configuration. It appears only when attention-input coverage is broadened to
all V or QK+V layers. QK+V being slightly better than all-V is directionally
consistent with the paper-style packed attention-input story, but the margin is
too small to promote by itself.

The current dense C^-1 application is still not a WR mechanism. The positive
arms are about 0.003 better at 200, while the active-window dense path remains
heavy and shows large one-time stalls. The next principled question is whether
activation-metric polar, polar(G L^-T) L^-1, gives a stronger or cleaner effect
than Newton-Muon-style polar(G C^-1). That test is now queued as the metricpolar
screen.
```

The Cholesky activation-metric polar screen was negative:

```text
mp_baseline:                 4.1759
mp_schedule_noop_polar4:     4.1875
mp_cholmetric_v01_polar4:    4.1775
mp_cholmetric_v01_polar5:    4.1783
mp_cholmetric_qkv01_polar4:  4.1865
```

Read:

```text
polar(G L^-T) L^-1 is mathematically clean, but in the tested layer-0/1
attention setup it does not improve the curve. This weakens the theory that the
missing piece is simply retaining C^-1/2 scale after polar. It may still be
tunable, but it is not a hot WR path under the current window/blend/ridge.

The stronger surviving clue remains surface coverage: all-layer attention-input
C^-1 gave the small 200-step gain, while V0-1 and metric-polar 0-1 did not.
The next test should therefore combine broader QKVO surface coverage with
bounded spectral filters, not a stronger post-polar metric update.
```

The first QKVO all-layer control says to drop O for now:

```text
qps_baseline:          4.0043
qps_qkvo_noop_polar4:  4.0148
```

Read:

```text
O is currently a bad broad-surface addition. The no-op/stat path alone is
slower and worse, and the O headwise statistics are much more extreme than the
attention-input Gram. At step 100 the O headwise Gram has p50 around 4.49e3 but
p99 around 1.14e5, and the power-0.5 spectrum already clips many O directions
at gain 2.0.

The next bounded-filter test should be QK+V only, all layers. That keeps the
paper-style packed attention-input hypothesis while avoiding O's heavier-tailed
and costlier output-feature metric.
```

The QK+V all-layer bounded power filter was negative:

```text
qvp_baseline:                    4.0004
qvp_qkv_noop_polar4:             4.0016
qvp_qkv_power05_r020_blend010:   4.0061
qvp_qkv_power075_r020_blend010:  4.0074
```

Read:

```text
Removing O avoids the worst cost pathology, but bounded power filters on all
QK+V do not reproduce the earlier paper-style dense inverse gain. Diagnostics
show a real target-space change, especially for QK: at step 112 the power-0.75
target filter has target_cos around 0.85 for QK, but the actual blended update
still has cos around 0.9986 against the unpreconditioned operand. The effect is
being mostly damped or washed through the existing blend/polar/variance-reduction
stack.

This does not justify cranking the filter stronger. The stronger power-0.75 arm
was worse than power-0.5, and both lost to the matched no-op. For the next GPU
block, the highest-value test is a control-adjusted replication of the only
surviving positive line: all-layer attention-input dense inverse, QK+V, before
momentum, ridge 0.2, refresh 16, EMA 0.8, active in the 48-112 window.
```

The matched QK+V dense-inverse control demoted that attention line:

```text
qic_baseline:                 3.8845
qic_qkv_noop_before_r020:     3.8814
qic_vall_inverse_before_r020: 3.8806
qic_qk_inverse_before_r020:   3.8885
qic_qkv_inverse_before_r020:  3.8841
```

Read:

```text
Attention-input inverse is not dead, but it is not the current WR lever. The
only active winner was all-V, and it beat the matched no-op by just 0.0008.
That is below the no-op/control spread. QK-only was clearly harmful, and QK+V
lost to the matched no-op, so the packed-QKV version is not supported by this
run.

This shifts the near-term search back to MLP c_fc. It is still a
768-dimensional right-preconditioner surface, but unlike QK it does not perturb
softmax logits or Q/K pair geometry. The strongest controlled c_fc setting is
the blend-0.05 before-momentum inverse: two 200-step repeats landed at 3.8815
and beat matched no-op by about 0.004 to 0.005. It needs a 400-step persistence
test before any WR claims.
```
