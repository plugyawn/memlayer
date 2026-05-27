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
   `LOCO_FULL_LOG_SPECTRUM=1`, then parse with
   `tools/parse_loco_full_diagnostics.py`.
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
