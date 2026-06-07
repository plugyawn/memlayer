# Track 3 LocoProp-M Tick Decision - 2026-06-07

Scope: simple Track 3 Muon + LocoProp-M from the known seed `3710`
step-1600 checkpoint:

```text
/root/.cache/track3_checkpoints/track3_cd500red_softmerge_pr2872000_p110_ckpt1600_seed3710_step1600.pt
```

Strict evidence audit:

```text
.opencode/track3_locom_tick_evidence_audit_20260607.md
```

## Prefix Specificity Update

The active K5 prefix reproduced the visually good 1900->2000 segment, but a
same-harness alpha-zero control reproduced it too.

Evidence:

```text
.opencode/track3_locom_prefix_effect_size_20260607.md
.opencode/track3_locom_tick_requirements_20260607.md
.opencode/current_track3_ledger_20260607_logs/prime_track3_locom_tick_ladder_20260607T022549Z.tar.gz
```

Shared-screen loss match:

```text
active K5:
  1900: 3.38478
  2000: 3.37337
  1900->2000 drop/100: 0.01141

same-harness alpha-zero:
  1900: 3.38478
  2000: 3.37338
  1900->2000 drop/100: 0.01140

max absolute active/control delta over 1600..2000: 0.00004
final control-active delta @2000: 0.00001
```

Correction geometry on the active lane:

```text
median eff_corr/base_step: about 0.005-0.010
median cos: mostly near zero
eff*cos: about -1e-5 to 1.2e-4 of the Muon step
```

Read:

```text
1900->2000 was good and real.
The applied natural K5 c_fc LocoProp correction did not cause it.
The causal object is now schedule/checkpoint/optimizer state, not this applied
c_fc local-solve displacement.
```

## Current Read

`1900->2000` was still a good window. Do not treat `1900` as the failure
point.

The confirmed no-Loco replay after the K5 LocoProp prefix was:

```text
1800: 3.39867
1900: 3.38474
2000: 3.37334
2100: 3.36420
2125: 3.36213
```

Window slopes:

```text
1800->1900: drop 0.01393 per 100, healthy
1900->2000: drop 0.01140 per 100, healthy
2000->2100: drop 0.00914 per 100, marginal
2100->2125: drop 0.00828 per 100 equivalent, cold
```

From `3.37334 @2000`, landing at `3.28 @3000` needs:

```text
required: (3.37334 - 3.28) / 10 = 0.00933 loss per 100 steps
```

So the `1900->2000` rate is not merely okay; it is more than enough. Preserving
about `82%` of that rate from `2000->3000` would reach the target. If the
`1900->2000` rate itself continued, the run would land around `3.259` by
`3000`.

Straight-line target from the `2000` state:

```text
2400: 3.33600
2500: 3.32667
2600: 3.31734
2800: 3.29867
3000: 3.28000
```

The first actionable slope break is therefore after `2000`, with the sharper
cooling visible by `2100->2125`, not before `1900`.

## Practical Consequence

Treat `1800->2000` as protected trajectory.

The next useful suffix probe should preserve the existing `1900->2000` state
and try to carry that slope into `2000->2250`. A hard optimizer or LR change at
`1900` is risky because it can disturb the last confirmed healthy window.

Acceptable intervention timing:

```text
best:      start at 2000
acceptable: smooth continuity guard from 1950->2050
avoid:     hard switch at 1900
too late:  2400+ rescue-only suffixes
```

If a probe branches before `2000`, it should be a continuity-preserving ramp,
not an abrupt replacement. The thing to protect is the `1900->2000` descent
rate.

Guarded mechanism ladder:

```text
tools/run_track3_locom_tick_ladder.sh
```

Default: prefix specificity at `2000`, then layer subset at `2000`. It stops
before suffix probes unless the mechanism gates pass.

Completion audit:

```text
python3 tools/audit_track3_locom_tick.py
```

The guarded ladder also writes:

```text
${TRACK3_TICK_LOG_ROOT:-/root/prime_track3_locom_tick_ladder}/tick_completion_audit.md
```

It also packages the copied-back run evidence by default:

```text
${TRACK3_TICK_LOG_ROOT:-/root/prime_track3_locom_tick_ladder}_<timestamp>.tar.gz
```

Disable packaging only for local smoke tests:

```text
TRACK3_TICK_PACK_ARTIFACTS=0 tools/run_track3_locom_tick_ladder.sh
```

## What Is Already Known

LocoProp-M tick conditions for this line:

```text
target_space=post
true_post_grad=1
K=5 is externally enough through 1800
inner_lr ~= 2e-4
require_loss_decrease=1
min_cos_desc=0.0
norm_to_base=0
norm_target=0
norm_cap=0.20
surface=c_fc only
placement=separate parameter displacement, not Muon momentum mutation
```

Prefix-control exception:

```text
orthogonal_k5_norm002 uses min_cos_desc=-1.0
```

That lane intentionally removes the descent-parallel component, so a
nonnegative cosine gate would risk rejecting the control due to numerical
roundoff around zero.

Known negatives:

```text
K8/K10 do not beat K5 externally through 1800
2048 sample tokens did not move validation versus 1024
continued post-1800 LocoProp, random, and no-Loco matched through 2125
normalized 2% post-2000 true-post LocoProp applied real corrections but stayed parity/worse
late floor/ramp probes after the slope is already cold have not rescued the run
```

## Gate Read

The prefix-specificity gate has now failed for the natural K5 c_fc correction.
Do not promote layer-subset or suffix probes as LocoProp-M mechanism probes
until a new positive correction mechanism exists.

1. Prefix specificity:

```text
tools/run_track3_locom_prefix_specificity.sh
```

Result: alpha-zero matched active to logged precision through 2000. The good
prefix is schedule/checkpoint state, not the active natural K5 c_fc correction.

The manifest now verifies that the orthogonal lane is not accidentally
cosine-gated away:

```text
tools/check_track3_locom_prefix_manifest.py --manifest-only
orthogonal_k5_norm002: mode=orthogonal, norm_target=0.02, min_cos_desc=-1.0
```

2. Layer subset:

```text
tools/run_track3_locom_layer_subset_probe.sh
```

Status: deprioritized. A layer-subset probe only makes sense if a future
nonzero correction variant first beats alpha-zero.

3. Suffix preservation:

```text
MODE=save2000 tools/run_track3_locom_2000_suffix_probe.sh
MODE=suffixes tools/run_track3_locom_2000_suffix_probe.sh
```

Purpose: still useful as a schedule/optimizer-state probe, but not as evidence
that the current LocoProp-M correction is working. The suffix problem remains
to preserve the `1900->2000` rate after 2000.

The suffix analyzer now reports slope preservation directly against the
observed healthy `1900->2000` reference:

```text
reference_drop_per_100 = 0.01140
line_start_step = 2000
preserved = lane_drop_per_100 >= 0.90 * reference_drop_per_100
```

So the readout should not be based only on final loss or a plot. The first
question is whether any lane keeps the `2000->2100` and `2000->2250` slopes
near the healthy reference.

Current saved readout:

```text
.opencode/track3_locom_2000_suffix_slope_decision_20260607.md
```

Corrected analyzer read, anchored at `2000`:

```text
control @2100 is 3.36420
straight-line target @2100 is 3.36400
control - target is +0.00020
```

So the `2000->2100` segment is almost enough for the final target, but it is
already below the healthy `1900->2000` rate. The `2100->2125` segment is the
first visibly cold segment.

The available `2000+` logs did not preserve the reference slope:

```text
best slope preservation: 0.80x on 2000->2100
norm002 active:          0.80x on 2000->2100, 0.72x on 2100->2125
old floor009 scheduler:  0.80x on 2000->2100, 0.67x on 2100->2125
```

That confirms the old suffixes were slope-starved, not merely missing a late
validation-polish step.

## Kill And Promotion Rules

Prefix specificity:

```text
active K5 not near 3.3987 @1800 within 0.003:
    invalid replay; stop.

active K5 not better than no-Loco by >=0.0015 @1800:
    LocoProp prefix is not specific enough.

random or orthogonal within 0.0005 of active:
    prefix effect is not clearly the local-solve descent direction.
```

Layer subset:

```text
core_7_10 matches all-layer within 0.0005:
    promote core; stop paying for full moving layer set.

expanded_6_10 wins or matches when core_7_10 does not:
    layer 6 is part of the useful core.

all static subsets trail all-layer by >0.0005:
    moving local gate / distributed state formation matters.
```

Suffix:

```text
post-2000 control still follows 1900->2000-like slope through 2250:
    do not add LocoProp; protect schedule/state.

no lane preserves >=90% of the 1900->2000 reference slope:
    this is still slope starvation, not a solved suffix.

floor/ramp beats control but LocoProp lanes do not:
    missing lever is LR/velocity, not local-solve direction.

no suffix lane beats control:
    this 2000 state has already lost the c_fc-specific leverage.
```

## Bottom Line

The current best hypothesis is:

```text
The cold prefix schedule/checkpoint state produces the good 1800->2000
trajectory. Natural K5 c_fc LocoProp-M is locally sane but externally neutral:
active and alpha-zero match.

The remaining speedrun problem is preserving the healthy 1900->2000 slope after
2000, or finding a materially different LocoProp expression whose nonzero
correction beats alpha-zero before we spend on suffix tuning.
```

The next minimal LocoProp-specific probe is scale, not more local iterations:

```text
tools/run_track3_locom_prefix_scale_probe.sh
```

It tests alpha-zero, natural K5, true-post K5 normalized to 2% and 5% of the
base step, and a same-shape random 2% control from the same step-1600
checkpoint. Promote only if a normalized active lane beats alpha-zero by at
least `0.001` at `2000` and random does not match it.
