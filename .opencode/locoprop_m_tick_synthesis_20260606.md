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
K ~= 5-10
inner_lr ~= 2e-4
require_loss_decrease=1
min_cos_desc=0.0
norm_to_base=0
norm_target=0
norm_cap=0.20
base schedule cold enough that the local correction is not diluted
```

This makes the applied correction a small, state-decoupled local displacement,
not a replacement for Muon momentum/state.

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
useful for K5 because it may match K10's correction scale with fewer local
steps.

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

## Unresolved Question

Is K10 essential, or is the useful object just the true-post local correction at
the right effective norm?

Next prepared screen:

```text
tools/launch_modal_track3_locom_k5_k10_coldp2_array.sh
```

Lanes:

```text
k10-lr2e4: control; known good local shape
k8-lr2e4:  tests whether last two local steps matter
k5-lr2e4:  half-cost weaker correction
k5-lr3e4:  half-cost, scale-closer correction
```

Run gate:

```text
At 1800:
  K10 control should reproduce ~3.3987.
  K8 or K5-lr3e4 within <=0.003 of K10 is a promotion candidate.
  K5-lr2e4 within <=0.005 of K10 is still interesting because it is cheaper.
```

If K5/K8 matches K10, the next engineering path is to make the true-post local
solve cheap/fused enough for real speedrun use. If only K10 works, keep K10 as
an algorithmic probe and focus on the LR-tail floor/hold experiments before
kernel work.
