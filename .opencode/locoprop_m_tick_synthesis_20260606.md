# LocoProp-M Tick Synthesis - 2026-06-06

Scope: Track 3 simple Muon + LocoProp-M from the known seed `3710` step-1600
checkpoint:

```text
/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt
```

## Current Answer

LocoProp-M only started to "tick" when all of these were true:

```text
target_space=post
true_post_grad=1
K >= 5 externally through the 1600->1800 prefix
inner_lr ~= 2e-4
require_loss_decrease=1
min_cos_desc=0.0
norm_to_base=0
norm_target=0
norm_cap=0.20
base schedule cold enough that the local correction is not diluted by Muon
```

This makes the applied correction a small, state-decoupled local displacement,
not a replacement for Muon momentum/state.

The newest read is sharper:

```text
It ticks as a prefix/trajectory intervention before ~1800-2000.
It does not tick as a continued suffix correction after 1800.
It does not tick as a late 2000+ normalized correction on the same c_fc surface.
It is not uniformly strong across all c_fc layers.
```

The 1800->2000 segment itself is not the failure. From the no-correction replay:

```text
1800->1900 drop 0.01393, 1.41x the straight-line rate needed for 3.28 @3000
1900->2000 drop 0.01141, 1.15x the straight-line rate needed for 3.28 @3000
2000->2100 drop 0.00913, 0.92x the straight-line rate needed for 3.28 @3000
2000->2125 drop 0.01118, 0.90x the straight-line rate needed for 3.28 @3000
```

So the slope break starts just after `2000`, not at `1900`. The better
intervention target is to preserve the `1800->2000` regime into `2000->2400`,
not to preemptively change the run at `1900`.

This is now codified by:

```text
tools/analyze_track3_locom_window_health.py
tools/analyze_track3_locom_lr_slope.py
.opencode/track3_locom_window_health_1800_suffix_20260607.md
.opencode/track3_locom_window_health_kdepth_20260607.md
.opencode/track3_locom_lr_slope_1800_suffix_20260607.md
```

The LR/slope join makes the post-2000 failure more concrete. In the exact
no-correction replay from the K5 step-1800 checkpoint:

```text
step 1800 lr_frac 0.160000
step 1900 lr_frac 0.134444
step 2000 lr_frac 0.111111
step 2100 lr_frac 0.090000
step 2125 lr_frac 0.085069
```

Window read:

```text
1800->1900: 1.41x rolling target slope, LR drop 16.0%, healthy
1900->2000: 1.20x rolling target slope, LR drop 17.4%, healthy
2000->2100: 0.98x rolling target slope, LR drop 19.0%, marginal
2100->2125: 0.89x rolling target slope, LR drop  5.5%, cold
```

So the "1900->2000 was good" correction is right. The 1900 window still
absorbs a substantial LR drop and remains above target slope. The first
actionable failure is the next transition, where LR falls from `0.111111` to
`0.090000` and the slope drops just below the future required average. By
`2100->2125`, the curve is cold even though the extra LR drop is small, which
suggests state/velocity has already decayed; a fix should preserve the
`1900->2000` regime across `2000->2250`, not wait until the endpoint.

This changes the intervention timing: `1900` is still inside the good regime.
The earliest place to intervene is `2000`, or slightly before it only as a
smooth continuity guard. A hard change at `1900` risks disturbing the last
confirmed healthy window.

The clean suffix replay from the exact K5 step-1800 checkpoint says:

```text
no-Loco 1800->1900: 1.41x target slope
no-Loco 1900->2000: 1.15x target slope
no-Loco 2000->2100: 0.92x target slope
no-Loco 2100->2125: 0.84x target slope

random  1800->1900: 1.41x target slope
random  1900->2000: 1.15x target slope
random  2000->2100: 0.92x target slope
random  2100->2125: 0.84x target slope
```

Read: after a good LocoProp prefix, `1900->2000` remains healthy even with
LocoProp off. Random same-shape correction does not change that. The state
created by the prefix is doing useful trajectory work through `2000`; the
later problem is slope preservation, not a missing LocoProp correction exactly
at `1900`.

The K-depth window report says K5/K8/K10 are validation-identical through
`1800`; every `1600->1800` subwindow is still healthy. For the few-iteration
question, this means `K=5` is already externally enough in this setup. K8/K10
improve the local objective more, but do not buy visible validation advantage
through the prefix screen.

The per-layer health report adds another narrowing:

```text
tools/analyze_track3_locom_layers.py
.opencode/track3_locom_layer_health_k5_20260607.md
.opencode/track3_locom_layer_health_k8_20260607.md
.opencode/track3_locom_layer_health_k10_20260607.md
```

K5 across the `1600,1625,...,1775` prefix diagnostics:

```text
strong c_fc layers:          2,7,8,9,10
accepted weak/strong layers: 0,1,2,3,4,5,6,7,8,9,10
risky/borderline layer:      11
```

Cross-K read:

```text
robust core across K5/K8/K10: 7,8,9,10
expanded K8/K10 core:         6,7,8,9,10
K10-only wider set:           5,6,7,8,9,10,11
unstable/inconsistent:        2,11
```

Layer `11` locally improves loss, but its cosine is inconsistent. Layer `2`
looks strong in the K5 log but becomes opposing/inconsistent in K8/K10. Layers
`0-1` are directionally accepted but weak. The next layer-subset probes should
therefore use:

```text
TRACK3_LOCOM_LAYERS=7,8,9,10
TRACK3_LOCOM_LAYERS=6,7,8,9,10
```

This does not replace the all-layer prefix specificity control. It says that
if the all-layer active prefix reproduces, the next cheap rung should be core
subset versus all-layer, not more K-depth.

The joined mechanism report adds the sharper falsification:

```text
tools/analyze_track3_locom_mechanism.py
.opencode/track3_locom_mechanism_kdepth_20260607.md
.opencode/track3_locom_mechanism_suffix_20260607.md
```

Prefix, from the exact step-1600 checkpoint:

```text
K5  @1600: med local loss/loss0 0.9038, med applied frac 1.04%
K8  @1600: med local loss/loss0 0.8589, med applied frac 1.58%
K10 @1600: med local loss/loss0 0.8327, med applied frac 1.92%

K5/K8/K10 validation @1800:
  K5  3.39870
  K8  3.39870
  K10 3.39873
```

So more local iterations do improve the local objective, but not the external
prefix validation. This makes `K=5` the right cheap default for the next
mechanism probes.

Suffix, from the post-prefix 2000 state:

```text
K10 norm002 @2000: med local loss/loss0 0.8609, eff applied frac 2.00%
K10 norm002 @2100: med local loss/loss0 0.8721, eff applied frac 2.00%
K10 norm002 @2125: med local loss/loss0 0.8588, eff applied frac 2.00%

validation slope:
  2000->2100: 0.98x needed, marginal
  2100->2125: 0.88-0.89x needed, cold
```

Read: the late failure is not that the local optimizer stopped solving its
local objective. The local solve still works, and a real 2%-of-base-step
correction is applied. The failure is that the local correction no longer
changes the global training trajectory. That points to prefix state formation
and LR/optimizer-state compatibility, not more K.

The random suffix is also informative:

```text
random from K5@1800 checkpoint:
  eff applied frac ~= 20% of base step
  validation matches no-Loco through 2125
```

That rules out "any bounded perturbation" as the reason for the prefix state.
The good prefix is direction/state-specific, but the remaining missing control
is still the exact prefix random/orthogonal/no-Loco comparison from 1600->1800.

The externally relevant correction size is small:

```text
prefix K5/K8/K10: raw/effective correction ~= 0.5-2% median of base step
late norm002:     forced effective correction = 2% of base step, still no gain
```

So the useful ingredient is not simply "make the LocoProp displacement larger."
The direction/state/timing has to be right.

Current implementation scope:

```text
surface: MLP c_fc only
layers: all real MLP layers when WR_LOCOM_LAYERS=all
not covered: MLP c_proj, QK, V, O, embeddings, output head
```

The name `WR_LOCOM_LAYERS=all` means all MLP layers, not all model surfaces.
Older V/O/QK/MLP surface screens were right-feature/LPA/soft-polar probes, not
this sampled true-post LocoProp-M correction.

## Untested Surface: MLP c_proj

`c_proj` is feasible on an 80GB H100 if it stays sampled and layer-sequential.
It is not likely to OOM at `sample_tokens=1024`: the main sampled tensors are
roughly `1024 x 3072` BF16 for `post` and `1024 x 768` BF16 for the output
target/gradient, plus a few `3072 x 768` local FP32 matrices. That is tens of
MiB per active layer, not multiple GiB, as long as we do not materialize all
layers' local solve temporaries at once.

The blocker is optimizer geometry, not memory:

```text
c_fc:
  local map: x -> relu(x W1.T)^2
  feature dim: 768
  target currently captured: post - gamma * dpre

c_proj:
  local map: post @ W2 -> mlp_out
  feature dim: 3072
  target needed: mlp_out - gamma * grad_output
```

Risks:

```text
post features are sparse/heavy-tailed;
c_proj directly changes residual-stream MLP output;
c_proj is zero-initialized in this codebase;
baseline gives c_proj a 2x per-matrix LR multiplier;
current LocoProp-M capture stores dpre for c_fc, not grad_output for c_proj;
current apply path skips odd MLP-bank indices, which are c_proj.
```

If tested, start with diagnostic-only `c_proj` K ladders before applying
anything. A first active probe should use a small layer subset, hard cap
`0.05-0.10`, and separate logs from `c_fc`.

## What Failed

The old post-approx path was not "more LocoProp." It was the wrong local target
and became numerically bad when K increased:

```text
post-approx current path:
  K1  median loss/loss0 9.133e-01, corr_norm 3.492e-02, bad_loss 4/12
  K4  median loss/loss0 2.132e+03, corr_norm 1.030e+00, bad_loss 10/12
  K10 median loss/loss0 3.128e+04, corr_norm 1.266e+02, bad_loss 8/12

preactivation:
  K1  median loss/loss0 2.274e+00, corr_norm 7.451e-02, bad_loss 11/12
  K10 median loss/loss0 6.590e+11, corr_norm 3.918e+04, bad_loss 11/12
```

Those variants were cap-rescued or unstable. Do not use them as evidence
against LocoProp-M.

## What Worked Locally

The true-post K-ladder at step 1600 was locally sane:

```text
inner_lr=2e-4, true post-gradient:
  K1  median loss/loss0 9.779e-01, corr_norm 9.401e-04, bad_loss 0/12
  K2  median loss/loss0 9.576e-01, corr_norm 1.845e-03, bad_loss 0/12
  K4  median loss/loss0 9.206e-01, corr_norm 3.534e-03, bad_loss 0/12
  K5  median loss/loss0 9.038e-01, corr_norm 4.124e-03, bad_loss 0/12
  K8  median loss/loss0 8.589e-01, corr_norm 5.750e-03, bad_loss 0/12
  K10 median loss/loss0 8.327e-01, corr_norm 6.757e-03, bad_loss 0/12
```

Scale ladder:

```text
1e-4: median loss/loss0 9.044e-01, corr_norm 4.069e-03, bad_loss 0/12
2e-4: median loss/loss0 8.327e-01, corr_norm 6.757e-03, bad_loss 0/12
3e-4: median loss/loss0 8.297e-01, corr_norm 9.128e-03, bad_loss 1/12
1e-3: median loss/loss0 7.789e-01, corr_norm 2.842e-02, bad_loss 3/12
```

Read: `2e-4` is the clean all-layer active default. `3e-4` is near the edge but
may still be useful as a scale probe. Local-step evidence says K8 is the local
objective knee, but the newer external K-depth screen says K5 is already enough
to reproduce the validation curve through `1800`. For this speedrun state,
validation is much less sensitive to K-depth than the local objective is.

K-effect read from the corrected coldp2 diagnostic window:

```text
every logged step 1600, 1625, ..., 1800:
  smallest K reaching 80% of K10 local gain = K8

representative step 1800:
  K5  gain/ref = 62.9%, corr/ref = 56.4%
  K8  gain/ref = 84.0%, corr/ref = 85.4%
  K10 gain/ref = 100.0%
```

Previously this pointed to `K8` versus `K10`. The latest external screen changes
that: K5/K8/K10 tied through `1800`, so the next question is no longer "how many
local steps are needed?" It is "why does the prefix state help but the same
correction later does nothing?"

## What Worked Externally

The corrected coldp2 K10/lr2e-4 lane:

```text
1600 3.48241
1625 3.45135
1650 3.43562
1675 3.42613
1700 3.41883
1725 3.41289
1750 3.40792
1775 3.40359
1800 3.39872
2000 3.37337
2125 3.36217
2250 3.35306
2400 3.34514
2450 3.34289
```

The corresponding apply-scale diagnostics:

```text
1600 eff_frac_med 0.01921, p90 0.04646
1625 eff_frac_med 0.01227, p90 0.02719
1700 eff_frac_med 0.01565, p90 0.04664
1800 eff_frac_med 0.02688, p90 0.08953
2000 eff_frac_med 0.01875, p90 0.04900
2250 eff_frac_med 0.03981, p90 0.11690
2400 eff_frac_med 0.05547, p90 0.20000
```

This says the working correction is not merely capped random noise: the median
applied correction is small, uncapped, and comes from accepted local solves.
The late rise in fraction happens because the Muon base step shrinks under the
cold schedule.

## What Did Not Matter

`sample_tokens=2048` did not move validation relative to `1024`:

```text
1024 coldp2: 3.39872 @1800
2048 coldp2: 3.39871 @1800
```

Larger samples reduced some diagnostic noise, but did not fix the remaining
training-dynamics problem. The bottleneck is not local sample count.

## Current Theory

LocoProp-M is helping as a small local post-feature correction during the phase
where the base Muon step is cold enough for that correction to matter but still
large enough to train. It does not need to be cap-saturated; in the best line,
the correction is usually only `~1-3%` of the base step before 2000.

The remaining failure is twofold:

1. The coldp2 suffix loses learning-rate velocity after ~2000.
2. Hard rewarming to WR-like LR hurt, so the state needs a floor/hold or a
   smoother schedule rather than a full PR287 rewarm.

Because `1900->2000` is still above target slope, the cleanest next suffix
questions are:

```text
2000 hold/pulse:
  keep the LR/correction conditions that produced the good 1900->2000 slope
  for another 200-400 steps.

2000 state-specific direction test:
  compare no-correction, random norm002, true-post norm002, and natural
  true-post from the same exact 2000 checkpoint.

2000 local-solve diagnostics:
  if true-post still improves local loss but validation stays tied, the
  problem is not local-solve quality; it is external direction/state alignment.
```

Prepared runner:

```text
tools/run_track3_locom_2000_suffix_probe.sh
```

Preflight manifest / LR preview:

```text
tools/check_track3_locom_suffix_manifest.py
.opencode/track3_locom_2000_suffix_manifest_20260607.md
```

The manifest confirms the intended schedule shapes:

```text
control:  0.111111 @2000 -> 0.090000 @2100 -> 0.062500 @2250
floor111: fixed 0.111111 through the preview window
ramp111:  0.111111 @2000 -> 0.118152 @2125 -> 0.111111 @2250
```

`ramp111` is not a no-overshoot floor; it is a smooth re-energization lane that
lands back at the step-2000 LR around 2250 and then decays. `floor111` is the
strict schedule-starvation control.

It is intentionally two-stage:

```text
MODE=save2000:
  resume the step-1600 checkpoint;
  run active true-post c_fc LocoProp-M K5 through 1800;
  continue the cold schedule to 2000;
  save track3_locom_good2000_seed3710_step2000.pt.

MODE=suffixes:
  branch from the exact saved 2000 state.
```

`MODE=suffixes` also writes an automatic decision report:

```text
track3_locom_2000_suffix_decision.md
```

generated by:

```text
tools/analyze_track3_locom_suffix_probe.py
```

Default suffix lanes:

```text
control:
  no LocoProp, cold schedule.

floor111:
  no LocoProp; floor power-tail LR at eta=0.111111, the step-2000 LR fraction.

floor111_norm002:
  floor111 plus true-post c_fc K5 correction at 2% base-step norm,
  active 2000:2250.

floor111_random002:
  floor111 plus same-shape random correction at 2% base-step norm.

ramp111:
  no LocoProp; smooth multiplier ramp 2000:2250:2250:2400:1.7777777778,
  approximately preserving the step-2000 LR through 2250 without an abrupt
  permanent floor.

Optional add-ons:
  floor111_orthogonal002, natural, norm002, random, orthogonal, hold115.
```

Gates:

```text
If floor111 beats control:
  the post-2000 failure is primarily LR/velocity starvation.

If ramp111 beats control but floor111 does not:
  the state wants a smooth LR-shape handoff, not a hard floor.

If floor111_norm002 beats floor111 and floor111_random002:
  late c_fc LocoProp direction still matters once LR starvation is controlled.

If floor111_random002 matches floor111_norm002:
  late benefit is not LocoProp-direction-specific; it is perturbation/scale
  under a repaired schedule.

If all lanes match control:
  the 2000 state has already lost the recoverable leverage; branch earlier
  around 1800-1900 or test different surfaces.
```

## Unresolved Question

Is the 1600->1800 prefix improvement LocoProp-specific, or is it mostly the cold
schedule plus any small state-decoupled perturbation?

Post-1800 controls do not answer that, because by then active LocoProp,
cap-random, and no-correction suffixes all match. The missing decisive control
is a prefix run from the same `1600` checkpoint:

Next prepared screen:

```text
tools/launch_modal_track3_locom_k5_k10_coldp2_array.sh
```

This older K-depth launcher is now less important than a prefix specificity
launcher. If reused, prioritize these lanes instead:

```text
active K5 true-post c_fc: known prefix curve
no-correction 1600->1800: tests whether cold schedule alone explains it
cap-random 1600->1800: tests whether small displacement/noise explains it
orthogonal/parallel correction 1600->1800: tests whether c_fc direction matters
```

Run gate:

```text
At 1800:
  active true-post should reproduce ~3.3987.
  no-correction/cap-random near active => prefix effect is not LocoProp-specific.
  no-correction/cap-random materially worse => LocoProp direction/state matters.
  orthogonal/parallel distinguishes "new direction" from "descent component."
```

The current evidence says not to spend more on K-depth until the prefix
specificity control is done. K-depth is not the bottleneck in the validation
curve we have.

Prepared layer-subset runner:

```text
tools/run_track3_locom_layer_subset_probe.sh
```

It runs:

```text
active_all:     known all-layer active K5 prefix
core_7_10:      TRACK3_LOCOM_LAYERS=7,8,9,10
expanded_6_10:  TRACK3_LOCOM_LAYERS=6,7,8,9,10
noloco:         exact no-Loco control
```

Decision rule:

```text
active_all fails to reproduce ~3.3987 @1800:
    invalid run; do not interpret subsets.

core_7_10 matches active_all:
    useful prefix is carried by the robust core; use the cheaper subset.

expanded_6_10 beats core_7_10 or matches active_all when core does not:
    layer 6 is part of the useful state despite weak K5 status.

both subsets trail active_all:
    prefix effect is distributed or weak layers are needed for state formation.
```

## Post-1800 Control Update

Prime SXM pod `461e0ceb6a3743f98ebd2b621fba42ca` answered a key control that
was missing from the previous synthesis.

Through `1800`, external validation was insensitive to K-depth:

```text
K10 lr2e-4: 3.39873 @1800
K8  lr2e-4: 3.39870 @1800
K5  lr2e-4: 3.39870 @1800
```

From the K5 `1800` checkpoint, three suffixes matched to noise:

```text
active LocoProp continuation: ~3.36217 @2125
cap-random continuation:       3.36216 @2125
no-correction continuation:    3.36213 @2125
```

Read:

- The post-1800 suffix descent is not evidence that continued LocoProp-M is
  helping. Plain no-correction continuation gives the same curve.
- The LocoProp-specific effect, if any, is in creating the prefix/checkpoint
  state by `1800`, not in the correction applied after `1800`.
- A clean no-correction checkpoint was saved at:

```text
/root/.cache/track3_checkpoints/track3_noloco_ckpt2125_seed3710_seed3710_step2125.pt
```

No-correction suffix probes from that checkpoint:

```text
cold power2:
  2125 3.36215
  2250 3.35305
  2400 3.34512

full PR287 h3105,p1.20:
  2150 3.40302
  2200 3.41107
  stopped; too hot

power2 + LR_MIN_ETA=0.08:
  2200 3.35668
  2250 3.35419
  stopped; worse than cold power2
```

This changes the current theory:

1. Do not keep spending on continued post-1800 LocoProp unless a pre-1800
   random/no-correction prefix control shows the prefix itself is not specific.
2. Do not rewarm this state with a direct PR287 jump or a simple LR floor.
3. The remaining record path must preserve the prefix advantage and solve the
   late slope collapse with a more state-aware late optimizer/schedule change.

## Post-2000 Normalized Suffix Result

The direct test of "maybe late LocoProp was washed out by tiny norm" was
negative.

From the saved/replayed `2000` state:

```text
no-Loco cold:
2000 3.37333
2025 3.37098
2050 3.36867
2075 3.36655
2100 3.36420
2125 3.36215

norm002 true-post LocoProp, active 2000:2250:
2000 3.37337
2025 3.37101
2050 3.36870
2075 3.36658
2100 3.36423
2125 3.36217
```

The normalized path really did apply visible corrections:

```text
effective correction/base-step fraction: 0.020 median
K10 local loss/loss0 median: ~0.855-0.893
median cosine: ~0.004-0.009
```

Read:

- This was not a too-small-correction failure.
- The local objective improved, but external validation stayed at exact
  parity/slightly worse.
- The late c_fc local correction direction does not compose with this suffix
  state, even when scaled to a meaningful relative size.

## What Would Make It Tick

The best current concise model:

```text
LocoProp-M works when it changes the training trajectory early enough that the
base Muon optimizer continues from a better state.

LocoProp-M does not work when it is treated as a late additive polish step on
top of a state whose remaining problem is scheduler/optimizer-state slope.
```

Concrete conditions that look necessary:

```text
surface:        c_fc, not yet all surfaces
target:         true post-gradient target, not post-approx or preactivation
local solve:    SGD K>=5, inner_lr ~= 2e-4, prox 0.1
gate:           local loss decrease plus nonnegative cosine
scale:          natural ~0.5-2% base-step fraction is enough in prefix
placement:      separate parameter displacement, not Muon momentum mutation
timing:         useful before ~1800-2000; not useful after 2000 in c_fc
schedule:       cold enough not to dilute correction; not a hot PR287 rewarm
```

Things now ruled out for this exact state:

```text
more sample tokens: 1024 -> 2048 no validation movement
more K in prefix: K5/K8/K10 tied externally through 1800
continued post-1800 c_fc LocoProp: active/random/no-correction tied
late scalar LR floor: floor 0.08/0.09 was worse
late normed c_fc LocoProp: 2% base-step correction stayed parity/worse
all layers equally valuable: cross-K layer health points to a robust 7-10 core
```

The next high-value question is not "more LocoProp steps." It is whether the
1600->1800 prefix effect is actually direction-specific. Run active/no-correction
/cap-random/orthogonal from the local `1600` checkpoint before spending on more
late-tail variants.

Prepared runner:

```text
tools/run_track3_locom_prefix_specificity.sh
```

It assumes an already-prepared GPU machine and runs:

```text
active_k5:             true-post c_fc K5, natural scale
noloco:                same cold schedule, no LocoProp
random_norm002:        same shape random correction at 2% base-step norm
orthogonal_k5_norm002: true-post correction with descent component removed,
                       scaled to 2% base-step norm
```

It also writes:

```text
track3_prefix_specificity_decision.md
```

generated by:

```text
tools/analyze_track3_locom_prefix_probe.py
```

Decision rule:

```text
active_k5 fails to reproduce ~3.3987 @1800 within tolerance:
    run is invalid; do not interpret controls.

active_k5 beats noloco/random:
    c_fc true-post direction matters in the prefix.

random_norm002 matches active:
    prefix gain is likely generic perturbation/noise plus schedule.

orthogonal matches active:
    useful part is not the descent-aligned component; local correction is acting
    more like state-space exploration/regularization.

noloco matches active:
    LocoProp is not the prefix cause; the cold schedule/checkpoint state is.
```
