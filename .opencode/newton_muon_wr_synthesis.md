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
