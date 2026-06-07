# Track 3 LocoProp-M Tick Evidence Audit - 2026-06-07

Objective under audit:

```text
after this, try sitting down with the locoprop on just a few iterations
(maybe 5-10) and figure out exactly what would make locoprop tick
```

This audit is intentionally strict. It separates what is proven by current
logs from what is still only a hypothesis.

## Proven

### K=5 Is Enough For The Prefix Screen

Evidence:

```text
.opencode/track3_locom_mechanism_kdepth_20260607.md
.opencode/track3_locom_window_health_kdepth_20260607.md
```

Observed validation:

```text
K5:  3.48241 @1600 -> 3.39870 @1800
K8:  3.48241 @1600 -> 3.39870 @1800
K10: 3.48241 @1600 -> 3.39873 @1800
```

Read:

```text
More local steps improve the local objective, but do not improve validation
through the 1600->1800 prefix. K=5 is externally sufficient in this state.
```

### True-Post c_fc Is The Only Validated Surface/Target

Evidence:

```text
.opencode/locoprop_m_tick_synthesis_20260606.md
```

Current validated shape:

```text
surface: c_fc only
target_space=post
true_post_grad=1
inner_lr ~= 2e-4
require_loss_decrease=1
min_cos_desc=0.0
norm_cap=0.20
natural scale in prefix
separate parameter displacement
```

Prefix-control exception:

```text
orthogonal_k5_norm002 uses min_cos_desc=-1.0
```

Reason: the orthogonal control removes the descent-parallel component. Keeping
the normal nonnegative-cosine gate would make tiny roundoff around zero capable
of rejecting the control correction.

Read:

```text
This is not evidence that LocoProp-M works on QKV/O, c_proj, embeddings, or
all affine surfaces. Those remain separate unproven surface hypotheses.
```

### The Local Solve Is Real But Weakly Descent-Aligned

Evidence:

```text
.opencode/track3_locom_mechanism_kdepth_20260607.md
```

At 1600/1700:

```text
K5 median loss/loss0: about 0.904 and 0.909
K8 median loss/loss0: about 0.859 and 0.874
K10 median loss/loss0: about 0.833 and 0.881
median cos: about 0.005-0.019
```

Read:

```text
LocoProp-M is solving the local objective, but the descent cosine is small.
The external prefix effect, if real, is not explained as a simple LR boost
along the base Muon direction.
```

### The Useful Window Survives After LocoProp Turns Off

Evidence:

```text
.opencode/track3_locom_lr_slope_1800_suffix_20260607.md
.opencode/track3_locom_tick_decision_20260607.md
```

No-Loco replay after the K5 prefix:

```text
1800: 3.39867
1900: 3.38474
2000: 3.37334
2100: 3.36420
2125: 3.36213
```

Window read:

```text
1800->1900: healthy
1900->2000: healthy
2000->2100: marginal
2100->2125: cold
```

Read:

```text
The 1900->2000 window is not the problem. The first actionable break is after
2000. Intervene at 2000 or with a smooth 1950->2050 continuity guard, not a
hard 1900 switch.
```

### Existing Post-2000 Lanes Are Slope-Starved

Evidence:

```text
.opencode/track3_locom_2000_suffix_slope_decision_20260607.md
```

Against the healthy `1900->2000` reference of `0.01140` loss per 100 steps:

```text
best saved 2000->2100 preservation: 0.80x
norm002 active 2100->2125:          0.72x
old floor009 scheduler 2100->2125:  0.67x
```

Read:

```text
The old suffixes did not fail because we missed a tiny validation polish. They
failed because they did not preserve the healthy descent rate after 2000.
```

### The Applied c_fc Layer Set Is Moving

Evidence:

```text
.opencode/track3_locom_acceptance_k5_20260607.md
.opencode/track3_locom_layer_health_k5_20260607.md
```

K5 accepted layers are broad and changing:

```text
1600: 0,3,4,6,7,8,9,10
1625: 0,1,2,4,5,6,7,8,9,10,11
1700: 0,1,2,3,4,5,6,8,9,10
1775: 0,1,2,3,4,5,6,7,8,9,10,11
```

Layer-health candidates:

```text
K5 strong: 2,7,8,9,10
cross-K robust core from prior synthesis: 7,8,9,10
expanded likely core: 6,7,8,9,10
risky/opposing: 11, and layer 2 is K-sensitive
```

Read:

```text
The all-layer c_fc setting is not literally all layers on every step; the local
gate selects a moving subset. Static subset probes are still needed to separate
"robust useful core" from "moving-gate state formation."
```

## Contradicted Or Ruled Out

### More K Is Not The Missing Ingredient

`K=8` and `K=10` improve local loss more than `K=5`, but match validation
through 1800. That contradicts "just run more local steps" for this prefix.

### More Sample Tokens Was Not Enough

Prior logged read says `1024 -> 2048` reduced noise but did not move validation.
That contradicts "sample noise alone is the bottleneck" for the current path.

### Late c_fc LocoProp Is Not Enough

The saved post-2000 normalized active LocoProp lane applies real `2%`
base-step corrections and improves local loss, but validation is parity/worse
than no-Loco. That contradicts "apply the same c_fc correction later and it
will rescue the run."

### Existing Random/No-Loco Survival Controls Do Not Prove Prefix Specificity

The current random/no-Loco controls start after the K5 prefix, at 1800. They
show the prefix-created state survives into 2000; they do not prove that the
1600->1800 prefix was direction-specific.

## Missing Evidence

### Prefix Direction Specificity

Still missing:

```text
active K5 vs no-Loco vs random 2% vs orthogonal 2%
from the same 1600 checkpoint, with the intervention active through 1800 and
all lanes continued without LocoProp through 2000
```

Required lane semantics:

```text
active_k5:              natural true-post K5, min_cos_desc=0.0
noloco:                 no correction
random_norm002:         same-shape random correction, norm_target=0.02
orthogonal_k5_norm002:  true-post correction minus descent-parallel component,
                        norm_target=0.02, min_cos_desc=-1.0
```

Decision point:

```text
2000, not 1800
```

Reason:

```text
1900->2000 is still a healthy slope window. The experiment must show whether
the 1600->1800 LocoProp direction creates the state that survives into that
window.
```

Prepared command:

```text
tools/run_track3_locom_prefix_specificity.sh
```

Guarded ladder command:

```text
tools/run_track3_locom_tick_ladder.sh
```

Default behavior:

```text
prefix specificity -> layer subset
```

Optional suffix gate:

```text
TRACK3_TICK_STOP_AFTER=suffix tools/run_track3_locom_tick_ladder.sh
```

Completion audit command:

```text
python3 tools/audit_track3_locom_tick.py
```

Current expected result before the GPU gates land:

```text
NOT COMPLETE
blocking: prefix specificity, static layer subset
```

Decisive read:

```text
active K5 beats no-Loco and random at 2000:
    true-post c_fc direction matters.

random or orthogonal matches active at 2000:
    effect is not clearly local-solve-direction-specific.

no-Loco matches active at 2000:
    the cold schedule/checkpoint, not LocoProp, caused the prefix.
```

### Static Layer Subset

Still missing:

```text
all moving-gated c_fc vs 7,8,9,10 vs 6,7,8,9,10 vs no-Loco,
with the intervention active through 1800 and all lanes continued without
LocoProp through 2000
```

Prepared command:

```text
tools/run_track3_locom_layer_subset_probe.sh
```

The guarded ladder only reaches this stage if prefix specificity passes at
`2000`.

Decisive read:

```text
core matches all-layer:
    reduce to the robust local-gain core.

static subsets trail all-layer:
    moving gate / distributed state formation matters.
```

### Post-2000 Slope Preservation

Still missing:

```text
a suffix lane that preserves >=90% of the 1900->2000 slope after 2000
```

Prepared command:

```text
MODE=save2000 tools/run_track3_locom_2000_suffix_probe.sh
MODE=suffixes tools/run_track3_locom_2000_suffix_probe.sh
```

The guarded ladder only reaches this stage when explicitly requested with
`TRACK3_TICK_STOP_AFTER=suffix`, and only after the static-layer stage passes.

The analyzer now scores this directly:

```text
tools/analyze_track3_locom_suffix_probe.py
--reference-drop-per-100 0.01140
--preserve-threshold 0.90
```

## Current Best Mechanism Model

```text
LocoProp-M, as currently implemented, is a small local c_fc displacement that
can alter the training trajectory before 1800. The benefit then persists for a
while under plain Muon, which means the useful object may be the prefix state,
not a continually applied late correction.

The local solve itself is real: it decreases local target loss. But the
direction has small global/Muon cosine, and late application does not preserve
validation slope. Therefore the thing that "ticks" is not "more local solving"
or "bigger late additive correction"; it is the interaction between early
c_fc local displacement, the local gate's moving layer set, and a schedule that
lets Muon exploit that prefix state without starving after step 2000.
```

## Completion Status

Not complete.

The current evidence is strong enough to state the K-depth, target-space,
timing, and suffix-failure rules. It is not strong enough to say "exactly" what
makes LocoProp-M tick because the prefix-direction and static-layer-subset
controls have not landed.
