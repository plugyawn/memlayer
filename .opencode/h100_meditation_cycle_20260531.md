# H100 / Meditation Cycle Log - 2026-05-31

All times are local IST unless noted.

## Cycle D

```text
GPU block start: 2026-05-31 02:01 IST
GPU block end:   2026-05-31 02:38 IST
Budget:          under the 1 hour H100 allowance
Apps:
  ap-jfbq8qftdizA0vppDREKQS stopped, local-client disconnect during V noop2
  ap-cVsqLgl3enFJjEhP7LtWUw stopped, completed MLP c_fc and O, canceled during QK compile
```

Implementation work:

```text
fc52161 Add paired additive surface screen runner
f4f7791 Prefer local Modal client for GPU runner
87c9be1 Allow detached Modal speedrun screens
```

H100 result files:

```text
.opencode/modal_lpa_surface_matrix_fixed80_h100_20260531.launch.log
.opencode/modal_lpa_surface_rest_fixed80_h100_20260531.launch.log
.opencode/modal_lpa_surface_fixed80_h100_20260531.parsed.md
.opencode/modal_lpa_surface_fixed80_h100_20260531.summary.md
```

Fixed-control additive finite-t surface screen:

| surface | active | noop1 | noop2 | delta vs mean noop | read |
| --- | ---: | ---: | ---: | ---: | --- |
| V | `4.5250` | `4.5250` | incomplete | n/a | no visible active win |
| MLP c_fc | `4.5251` | `4.5235` | `4.5224` | `+0.0022` | worse |
| O headwise | `4.5239` | `4.5189` | `4.5209` | `+0.0040` | worse |
| QK | incomplete | incomplete | incomplete | n/a | canceled during compile |

Conclusion:

```text
The state-decoupled additive LocoProp-style correction is not currently a hit
under fixed paired controls. The earlier positive additive results were likely
from the broken runtime-noop path or control spread, not stable optimizer alpha.

The additive diagnostics need careful interpretation. The `target_cos` field is
not meaningful for additive corrections because the logger assumes an in-place
blended preconditioner, while additive uses `blend` later as a separate LR
scale. The meaningful field is `ref_cos`, which measures the local correction
against the base NorMuon update:

  V:      ref_cos around 0.15-0.20
  MLP fc: ref_cos around 0.16-0.39
  O:      ref_cos around 0.15-0.30

So the local correction is not sign-flipped. It is weakly positive-aligned with
the base update, and the raw unnormalized correction often has a much larger
norm than the base update. The current "add normalized GC-filtered correction on
top of NorMuon" interpretation is therefore suspect because it may mostly be a
small extra partially aligned step, not because it points exactly backward.

The right-feature axis is still theoretically real, but the usable form is not:
  1. hard Muon-path insertion gets washed/confounded,
  2. post-varred/full-metric insertion faded,
  3. additive finite correction fights the base update,
  4. soft/metric-soft V did not beat paired noops.
```

Next meditation targets:

```text
1. Explain why right-preconditioned raw gradients are only weakly aligned with
   the NorMuon base update after cautious/variance-reduced polar.
2. Test whether additive correction needs projection control: parallel-only,
   orthogonal-only, or norm cap below 5%.
3. Verify the sign convention with a tiny deterministic local tensor test, but
   do not treat `target_cos` as evidence for a sign bug in additive mode.
4. Avoid further H100 screens until we resolve this directionality issue from
   diagnostics or a tiny deterministic local tensor test.
```

## Cycle D Meditation Update

```text
Meditation start: 2026-05-31 02:38 IST
Current check:     2026-05-31 02:53 IST
Next GPU allowed:  about 2026-05-31 03:38 IST
Modal apps:        all recent apps stopped, no active tasks
Modal billing:     nanogpt-speedrun-newton-muon about $60.01 month-to-date pre-credit
                  exact remaining grant still requires Modal dashboard
Data preflight:    CPU-only Modal prepare returned fineweb train shards 1-2 and
                  validation shard, elapsed 0.44s remote
```

Committed during meditation:

```text
9fa7ea4 Add additive component ladder runner
5c85288 Prefer local Modal client for billing check
5577c8f Add paired case summary parser
0c4b06f Add additive correction norm cap
1f6e60a Report early loss in paired summaries
ba5b189 Add preconditioner reference summary parser
```

Sidecar review conclusions:

```text
Both read-only sidecars agreed that the next GPU spend should be the V component
ladder before adding a new rawscale/natural-magnitude correction.

Reason:
  LPA_NORM_TO_BASE=1 projects the right-feature correction, rescales it to the
  base NorMuon update norm, then applies it with additive LR blend. Therefore:
    orthogonal:0.02 = 2% base-norm orthogonal kick
    orthogonal:0.05 = 5% base-norm orthogonal kick
    parallel:0.05 = LR/schedule/control comparator

Rawscale with LPA_NORM_TO_BASE=0 is not a cap unless LPA_NORM_CAP is set.
Existing diagnostics show raw V corrections often around 8-13x the base-update
norm, and MLP/O can be larger. At blend=0.05 that can be a large uncontrolled
perturbation. Commit 0c4b06f added a disabled-by-default cap so the fallback can
use LPA_NORM_TO_BASE=0 plus LPA_NORM_CAP=1 without another implementation cycle.
```

Next H100 ladder:

```bash
NANOGPT_MODAL_GPU='H100!' MODAL_GPU='H100!' MODAL_DETACH=1 \
MODAL_RUN_NAME='lpa-v-components-20260531' \
MODAL_RUNNER='tools/run_lpa_component_matrix_gate.sh' \
SCREEN_STEPS=80 SCREEN_VAL_EVERY=40 \
MODAL_EXTRA_ENV_JSON='{"LPA_COMPONENT_MATRIX":"parallel:0.05,orthogonal:0.02,orthogonal:0.05","LPA_SUITE_LABEL_PREFIX":"lpa_v_components_fixed80_20260531","LPA_SURFACE":"v","LPA_LAYERS":"0-1","LPA_COLLECT_WINDOWS":"0-64","LPA_WINDOWS":"48-64","LPA_REFRESH_INTERVAL":"16","LPA_EMA_BETA":"0.8","LPA_RIDGE_REL":"0.2","LPA_BLEND_STEPS":"16","LPA_FINITE_T":"2.0","LPA_POWER_CLIP":"2.0","LPA_NORM_TO_BASE":"1","LPA_LOG_PRECOND":"1","LPA_LOG_PRECOND_DETAIL":"0"}' \
tools/run_modal_newtonv_raw_gate.sh 2>&1 | tee .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log
```

Post-run parse:

```bash
python3 tools/parse_newtonv_logs.py .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log > .opencode/modal_lpa_v_components_fixed80_h100_20260531.parsed.md
python3 tools/summarize_paired_cases.py .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log > .opencode/modal_lpa_v_components_fixed80_h100_20260531.summary.md
python3 tools/parse_loco_full_diagnostics.py .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log > .opencode/modal_lpa_v_components_fixed80_h100_20260531.diagnostics.md
python3 tools/summarize_precond_refs.py --name full_v_add --name full_v_add_rawscale .opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log > .opencode/modal_lpa_v_components_fixed80_h100_20260531.refs.md
```

Promotion and falsification:

```text
Promote only if an orthogonal active case beats both noops at step 80 by at
least 0.003-0.005. If orthogonal:0.02 wins and orthogonal:0.05 loses, run
orthogonal 0.01/0.02/0.03 at 200 steps. If parallel wins but orthogonal loses,
treat it as LR/schedule perturbation, not feature-axis alpha. If both
orthogonal cases lose, falsify this additive finite V form for now.

Diagnostic sanity:
  orthogonal full_v_add ref_cos_mean should be near 0
  parallel full_v_add ref_cos_mean should be near +1 or -1
  full_v_add_rawscale should be parsed separately to estimate natural magnitude
```

Fallback if V component ladder fails:

```text
The paper-focused sidecar recommends switching contract, not continuing V local
correction tuning: run MLP c_fc soft-polar spectral transfer at alpha=0.5,
eps=1e-6, window 48-64, norm-restore on, paired noop/active/noop2. Caveat:
alpha=0.5, eps=6e-5 already lost badly against both noops, so this is a
lower-priority fallback, not a fresh high-confidence path. Rationale: if the V
orthogonal local correction fails, the next distinct mathematical lever is
partial singular-value flattening on the Muon path, not another separate
additive correction. MLP c_fc is the clean 768-dimensional affine surface
already implemented for soft-polar.
```

Fallback command shape:

```bash
NEWTONV_SUITE=softpolar_paired \
NEWTONV_SUITE_LABEL=sp_mlpfc_a05_win48_64 \
SP_STEPS=80 SP_VAL_EVERY=40 \
SP_LAYERS=0-1 SP_WINDOWS=48-64 \
SP_ALPHA=0.5 SP_EPS=1e-6 \
SP_BLEND_MAX=1.0 SP_BLEND_STEPS=16 \
SP_NORM_RESTORE=1 \
SP_PAIRED_CASES=noop,active,noop2 \
SP_LOG_PRECOND=1 SP_LOG_PRECOND_DETAIL=1 \
bash tools/run_newtonv_experiment_suite.sh
```

## Cycle E

```text
GPU block start: 2026-05-31 03:38 IST
GPU block end:   2026-05-31 03:58 IST
Budget:          about 19.6 minutes H100 wall time
App:             ap-wVBWgST7LA4lMC55kwDhqz
Runner:          tools/run_lpa_component_matrix_gate.sh
Next GPU allowed: about 2026-05-31 04:58 IST
```

Artifacts:

```text
.opencode/modal_lpa_v_components_fixed80_h100_20260531.launch.log
.opencode/modal_lpa_v_components_fixed80_h100_20260531.parsed.md
.opencode/modal_lpa_v_components_fixed80_h100_20260531.summary.md
.opencode/modal_lpa_v_components_fixed80_h100_20260531.diagnostics.md
.opencode/modal_lpa_v_components_fixed80_h100_20260531.refs.md
```

Result:

| component | blend | step 40 delta vs noop mean | step 80 active | noops | step 80 delta vs noop mean | beats both |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| parallel | `0.05` | `+0.0142` | `4.5352` | `4.5336 / 4.5213` | `+0.0077` | no |
| orthogonal | `0.02` | `-0.0394` | `4.5284` | `4.5377 / 4.5272` | `-0.0040` | no |
| orthogonal | `0.05` | `-0.0135` | `4.5258` | `4.5289 / 4.5236` | `-0.0004` | no |

Diagnostic sanity:

```text
parallel full_v_add:
  ref_cos ~= 1.0
  ref_delta ~= 0
  Interpretation: after projection/norm-to-base, this is basically a small
  extra copy of the base NorMuon update. It hurts, so this is not an LR-like win.

orthogonal full_v_add:
  ref_cos ~= 0
  ref_delta ~= sqrt(2)
  Interpretation: the projection test worked and really injected an orthogonal
  base-norm direction scaled by blend.

rawscale orthogonal V:
  ref_norm roughly 8x at step 64 in active cases, with spikes over 20x in noops.
  Natural-magnitude additive needs a true cap if tested.
```

Decision:

```text
Do not promote the V additive finite component form. Orthogonal 0.02 is
suggestive because it beats the mean noop and has a large step-40 signal, but
it does not beat both noops at step 80. Orthogonal 0.05 fades to essentially
parity with the noop mean. Parallel is clearly worse.

This is not a proof that right-preconditioning is useless. It says:
  1. the feature-derived direction is mechanically nontrivial;
  2. pure parallel/LR-like correction is bad;
  3. a small orthogonal component may help briefly;
  4. this finite V additive form is not reliable enough for WR promotion.
```

Meditation targets before another GPU:

```text
1. Decide whether orthogonal 0.02 deserves a replication/finer 0.01/0.02/0.03
   run despite missing the strict beats-both gate.
2. Compare that against switching contracts: true norm-capped natural
   correction, metric-soft V, or MLP c_fc soft-polar with eps=1e-6.
3. Avoid spending the next H100 hour on broad surfaces unless a sidecar can
   explain why this result specifically predicts transfer.
```

## Cycle E Meditation Update

```text
Meditation start: 2026-05-31 03:58 IST
Current check:     2026-05-31 04:10 IST
Next GPU allowed:  about 2026-05-31 04:58 IST
Modal apps:        ap-wVBWgST7LA4lMC55kwDhqz stopped, no active tasks
Repo state:        clean after 8e4d833
```

Read-only sidecar recommendations:

```text
Avicenna:
  Recommendation: run exactly one narrow V orthogonal fine ladder, then kill
  this additive finite V form if it misses.

  Reason: orthogonal:0.02 was not a strict step-80 win because active 4.5284
  missed the best noop 4.5272 by 0.0012. But it beat both noops hard at step
  40 and diagnostics show the injection was mechanically clean: ref_cos ~= 0,
  ref_delta ~= sqrt(2). Parallel 0.05 was bad, so this was not simply an
  LR-like perturbation.

  Proposed run: V only, orthogonal blends 0.01/0.02/0.03, 200 steps.
  Gate: continue only if one case beats both paired noops at step 200 by
  at least 0.003-0.005 and is not only a step-40 blip.

Anscombe:
  Recommendation: switch contracts to true norm-capped natural-magnitude
  additive LPA across v,o,mlp_fc with full component.

  Reason: the orthogonal 0.02 hint is too weak to promote, and forced
  norm-matching may be the wrong intervention. Newton/LocoProp/K-FAC/Shampoo
  all care about curvature-scaled magnitude, while Polar-Muon erases most
  singular-value magnitude. Test a small additive trust-region term capped by
  the Muon update norm instead of renormalizing it to the base update.

  Proposed run: v,o,mlp_fc, component=full, LPA_NORM_TO_BASE=0,
  LPA_NORM_CAP=1, blend=0.05, 80 steps.
  Gate: keep only if one surface beats both paired noops at step 80 and
  improves the noop mean by at least 0.003, without step-40 regression > 0.02
  or step-time overhead > 1%.
```

Decision for next GPU:

```text
Prefer the natural-capped additive surface screen next.

Reason:
  1. The V orthogonal fine ladder is a replication of a near-miss; useful, but
     it mostly asks whether a small no-op-control variance gap flips at 200.
  2. The natural-capped screen asks a distinct mechanistic question: whether
     right-preconditioned magnitude is what gets lost when we force norm-to-base
     or push the metric through Polar/Muon.
  3. It is already implemented, uses fixed paired noops, touches only the
     three most plausible cheap surfaces, and should fit within the next
     one-hour H100 block.
  4. If no surface clears the strict gate, additive LocoProp magnitude in the
     early 48-64 window should be stopped rather than tuned.
```

Plan correction:

```text
The initial natural-cap command used LPA_NORM_CAP=1 and LPA_BLEND_MAX=0.05.
That is not a distinct test from norm-to-base when rawscale ref_norm is already
well above 1x. The prior fixed-surface full-V run had active rawscale
ref_norm around 7.7x-13.9x, O around 10x-16x, and MLP c_fc around 15x-36x.

Therefore cap=1 would clip nearly every active correction to exactly the base
update norm, then apply the same 5% additive blend as the failed norm-to-base
screen. It would mostly retest the old contract.

The corrected natural-magnitude screen uses:
  LPA_NORM_TO_BASE=0
  LPA_NORM_CAP=20
  LPA_BLEND_MAX=0.005

This keeps the maximum additive correction to 10% of the base update norm, but
preserves raw magnitude differences below the 20x cap. It is a real test of
whether local right-metric magnitude contains useful signal.
```

Prepared command for the 04:58 IST gate:

```bash
NANOGPT_MODAL_GPU='H100!' MODAL_GPU='H100!' MODAL_DETACH=1 \
MODAL_RUN_NAME='lpa-natcap20-surface80-20260531' \
MODAL_RUNNER='tools/run_lpa_surface_matrix_gate.sh' \
SCREEN_STEPS=80 SCREEN_VAL_EVERY=40 \
MODAL_EXTRA_ENV_JSON='{"LPA_SUITE_LABEL_PREFIX":"lpa_natcap20_surface80_20260531","LPA_SURFACE_MATRIX":"v,o,mlp_fc","LPA_COMPONENT":"full","LPA_NORM_TO_BASE":"0","LPA_NORM_CAP":"20","LPA_STEPS":"80","LPA_VAL_EVERY":"40","LPA_LAYERS":"0-1","LPA_COLLECT_WINDOWS":"0-64","LPA_WINDOWS":"48-64","LPA_REFRESH_INTERVAL":"16","LPA_EMA_BETA":"0.8","LPA_RIDGE_REL":"0.2","LPA_BLEND_MAX":"0.005","LPA_BLEND_STEPS":"16","LPA_FINITE_T":"2.0","LPA_POWER_CLIP":"2.0","LPA_PAIRED_CASES":"noop,active,noop2","LPA_LOG_PRECOND":"1","LPA_LOG_PRECOND_DETAIL":"1"}' \
tools/run_modal_newtonv_raw_gate.sh 2>&1 | tee .opencode/modal_lpa_natcap20_surface80_h100_20260531.launch.log
```

Post-run parse:

```bash
python3 tools/parse_newtonv_logs.py .opencode/modal_lpa_natcap20_surface80_h100_20260531.launch.log > .opencode/modal_lpa_natcap20_surface80_h100_20260531.parsed.md
python3 tools/summarize_paired_cases.py .opencode/modal_lpa_natcap20_surface80_h100_20260531.launch.log > .opencode/modal_lpa_natcap20_surface80_h100_20260531.summary.md
python3 tools/parse_loco_full_diagnostics.py .opencode/modal_lpa_natcap20_surface80_h100_20260531.launch.log > .opencode/modal_lpa_natcap20_surface80_h100_20260531.diagnostics.md
python3 tools/summarize_precond_refs.py --name full_v_add_rawscale --name full_o_add_rawscale --name full_mlp_fc_add_rawscale --name full_v_add --name full_o_add --name full_mlp_fc_add .opencode/modal_lpa_natcap20_surface80_h100_20260531.launch.log > .opencode/modal_lpa_natcap20_surface80_h100_20260531.refs.md
python3 tools/summarize_natcap_gate.py .opencode/modal_lpa_natcap20_surface80_h100_20260531.launch.log > .opencode/modal_lpa_natcap20_surface80_h100_20260531.gate.md
```

Launch guard incident:

```text
At 2026-05-31 04:12 IST a malformed zsh string-comparison guard fell through
early and initialized app ap-KRLqoFpRZZs0WroKYNLsCG. The app was stopped with
`modal app stop -y`, local launcher processes were killed, and `modal app list`
showed the app stopped with 0 tasks. The output only reached image/object
creation logs before the stop; do not count this as a valid H100 experiment.

Fix for the actual gate: do not use zsh `[ ... '<' ... ]`; launch manually or
use a Python wall-clock guard.
```

Post-plan sidecar synthesis:

```text
Dewey:
  If natural-cap is negative, it falsifies only this contract:
    surfaces v,o,mlp_fc; layers 0-1; collect 0-64; apply 48-64;
    finite_t=2.0; ridge=0.2; blend=0.005; cap=20x base update before blend;
    80-step screen.

  It does not falsify right-preconditioning generally, all-layer/later-window
  variants, QK, true Newton-Muon path insertion, metric-soft,
  activation-metric polar, or lower additive caps.

  If negative, the single next run should be the narrow V orthogonal
  0.01/0.02/0.03 200-step persistence ladder. If that misses, kill this
  additive finite-V family.

Confucius:
  The useful diagnostic is not target_cos for additive logs. Watch rawscale
  ref_norm_mean, ref_cos_mean, and ref_delta_mean:

    ref_norm_mean:
      5x-30x means the cap is essential and the run is testing a large local
      natural correction clipped into a trust region.
      near 1x means norm-to-base was probably not the main problem.

    ref_cos_mean:
      near 1.0 means LR/schedule clone, not a real metric win.
      0.1-0.5 means distinct but not adversarial, the promising zone.
      near 0 means orthogonal feature signal.
      negative means likely wrong sign/object/window unless loss proves
      otherwise.

    ref_delta_mean:
      large and stable means the metric materially changes the update;
      large and noisy means the local solve/eigen tail is probably unstable.

  If a surface beats both noops and rawscale ref_cos is not near 1, the metric
  is not useless. If rawscale is structured but active loses, the metric is
  probably entering the wrong object or time window.
```

## Cycle F

```text
GPU block start: 2026-05-31 05:04 IST
GPU block status: completed
Apps:
  ap-SI4mPLZWIHv0omZG4kgNRd stopped during Modal image build, no training
  ap-7UXFoA81Pqco4Wdcitfei1 completed V then failed during O setup
  ap-xAjg3zgyNryI0DTaBS2p4c completed O and MLP c_fc rest run
  ap-IOZ8bKtwuqWQxk3OuGa73H completed MLP c_fc 200-step persistence follow-up
```

Natural-cap20 surface screen:

```text
Contract:
  surfaces: v,o,mlp_fc
  layers: 0-1
  collect: 0-64
  apply: 48-64
  finite_t: 2.0
  ridge: 0.2
  LPA_NORM_TO_BASE=0
  LPA_NORM_CAP=20
  LPA_BLEND_MAX=0.005
```

Result:

| surface | active_40 | delta_40 | active | noop1 | noop2 | noop_mean | delta | beats both | overhead | raw ref_norm | raw ref_cos | read |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | --- | ---: | ---: | ---: | --- |
| V | `5.6117` | `+0.0133` | `4.5245` | `4.5166` | `4.5335` | `4.5251` | `-0.0006` | no | `+0.27%` | `9.8554` | `0.2069` | no gate |
| O | `5.6079` | `-0.0029` | `4.5345` | `4.5350` | `4.5240` | `4.5295` | `+0.0050` | no | `+0.20%` | `10.1390` | `0.3290` | worse |
| MLP c_fc | `5.6076` | `-0.0222` | `4.5247` | `4.5286` | `4.5297` | `4.5291` | `-0.0044` | yes | `+0.24%` | `18.6070` | `0.4073` | pass |

Interpretation:

```text
This is the first clean positive result in the current fixed-control cycle.
MLP c_fc natural-cap20 additive LPA beats both paired noops at step 80, clears
the -0.003 noop-mean threshold, improves at step 40, and has negligible timing
overhead. The rawscale diagnostic is not an LR clone: ref_cos is about 0.41 and
raw ref_norm is about 18.6x before the cap. The cap is active and meaningful.

V did not pass despite structured rawscale. O was worse. The immediate next
H100 spend should be a 200-step MLP c_fc persistence test with the same
contract, not a broad new surface sweep.
```

MLP c_fc 200-step persistence follow-up:

```text
App: ap-IOZ8bKtwuqWQxk3OuGa73H
GPU block end: 2026-05-31T05:18:16Z / 2026-05-31 10:48:16 IST
Next H100 allowed after meditation: 2026-05-31 11:48:16 IST

Contract:
  surface: mlp_fc
  layers: 0-1
  collect: 0-64
  apply: 48-64
  finite_t: 2.0
  ridge: 0.2
  LPA_NORM_TO_BASE=0
  LPA_NORM_CAP=20
  LPA_BLEND_MAX=0.005
  paired cases: noop, active, noop2
```

Result:

| step | active | noop1 | noop2 | read |
| ---: | ---: | ---: | ---: | --- |
| 40 | `5.8629` | unavailable in gate table | unavailable in gate table | active was worse than noop mean by `+0.0038` |
| 200 | `3.8876` | `3.8850` | `3.8843` | active worse than both noops |

Gate summary:

```text
active=3.8876
noop_mean=3.8846
delta_vs_noop_mean=+0.0030
beats_both=no
gate_pass=no
raw_step=64
raw_ref_norm=14.1530
raw_ref_delta=13.8240
raw_ref_cos=0.3628
```

Timing note:

```text
paired_noop step_avg was contaminated by a large one-off step spike, so the
negative overhead in the gate table is not meaningful. The loss comparison is
still valid because active lost to both paired noops.
```

Updated interpretation:

```text
The 80-step MLP c_fc natural-cap hit did not persist. More importantly, the
200-step run did not reproduce a clean 80-step advantage inside the longer
run: active was already worse than noop mean at step 40, and by step 200 it was
worse than both noops.

This downgrades natural-cap20 MLP c_fc from "first clean positive" to
"transient / variance-sensitive early hit." It does not falsify
right-preconditioning generally, because the raw correction remains structured
and non-collinear with the base update. It does falsify this exact promotion
contract:
  mlp_fc, layers 0-1, collect 0-64, apply 48-64, finite_t=2.0,
  ridge=0.2, cap20, blend0.005, additive state-decoupled correction.

Do not launch another immediate GPU run from this result. The next hour should
be spent reasoning about why 80-step wins are not 200-step-persistent and what
diagnostic would distinguish a real right-metric benefit from an early
trajectory nudge.
```

## Cycle G Plan

```text
Current local time when plan was recorded: 2026-05-31 10:58 IST
Last H100 block ended: 2026-05-31 10:48:16 IST
Next H100 allowed: 2026-05-31 11:48:16 IST
```

User correction:

```text
Before spending more time on C / feature-Gram variants, gather a no-C control:
drop feature covariance collection and right preconditioning, and adapt/test
Soft-Muon from PR291 / Nilin's note.
```

Interpretation:

```text
PR291 Soft-Muon is not feature-Gram right-preconditioning. It changes the
singular-value transfer of the Muon update itself. The PR291 value p=0.1 is
roughly equivalent to our exact spectral-transfer parameter alpha=0.9 because:

  T_alpha(X) = X (X^T X + eps I)^(-alpha/2)
  sigma -> sigma^(1-alpha)

so p = 1 - alpha.

Our previous no-C soft-polar screen used alpha=0.5, i.e. p=0.5. That was much
softer and does not falsify PR291-style Soft-Muon. The next no-C screen should
therefore use alpha=0.9, p~=0.1, and should not enable LOCO_FULL/LOCO_DIAG.
```

Prepared next H100 command:

```bash
NANOGPT_MODAL_GPU='H100!' MODAL_GPU='H100!' MODAL_DETACH=1 \
MODAL_RUN_NAME='softmuon-noc-mlpfc-a09-200-20260531' \
MODAL_RUNNER='tools/run_softpolar_mlpfc_gate.sh' \
SCREEN_STEPS=200 SCREEN_VAL_EVERY=40 \
MODAL_EXTRA_ENV_JSON='{"TRAIN_SYNC_BOS_INDEX":"1","NEWTONV_PAIRED_CASES":"noop,active,noop2","LOCO_SOFT_POLAR_SURFACES":"mlp_fc","LOCO_SOFT_POLAR_ALPHA":"0.9","LOCO_SOFT_POLAR_EPS":"1e-6","LOCO_SOFT_POLAR_WINDOWS":"48-64","LOCO_SOFT_POLAR_BLEND_MAX":"1.0","LOCO_SOFT_POLAR_BLEND_STEPS":"16","LOCO_SOFT_POLAR_NORM_RESTORE":"1","LOCO_DIAG_MLP_LAYERS":"0-1","LOCO_FULL_LOG_PRECOND":"1","LOCO_FULL_LOG_PRECOND_DETAIL":"0","LOCO_DIAG_LOG_STEPS":"48,50,56,64,80,120,160,200"}' \
tools/run_modal_newtonv_raw_gate.sh 2>&1 | tee .opencode/modal_softmuon_noc_mlpfc_a09_200_h100_20260531.launch.log
```

Readout:

```text
If alpha=0.9 MLP c_fc clears paired noops at 200, the immediate lesson is that
the useful lever may be no-C Muon spectral transfer, not feature-Gram C.

If it fails but is harmless, broaden/no-C test later to V or all Muon surfaces
before returning to C.

If it is bad, PR291-style Soft-Muon cannot be inferred from this one early
MLP-only pulse, because PR291 uses a late schedule and all/selected Muon
matrices; but it would say our current local alpha=0.9 pulse is not the missing
control.
```

Implementation update:

```text
Commit 833fe93 extends the no-C Soft-Muon probe beyond MLP c_fc so future
screens can set:
  LOCO_SOFT_POLAR_SURFACES=qk,v,o,mlp_fc

The first guarded H100 run remains MLP c_fc only, because it is the clean
control for the latest cap20 MLP c_fc feature-Gram result. If MLP-only is
neutral rather than bad, the next no-C run should broaden surfaces before
returning to C.
```

## Cycle G Result

No-C Soft-Muon MLP c_fc alpha0.9 200-step paired control:

```text
App: ap-1toEjKsdSXk81T8gxlRyio
GPU block end: 2026-05-31T06:27:39Z / 2026-05-31 11:57:39 IST
Next H100 allowed after meditation: 2026-05-31 12:57:39 IST

Contract:
  LOCO_SOFT_POLAR_SURFACES=mlp_fc
  LOCO_SOFT_POLAR_ALPHA=0.9
  LOCO_SOFT_POLAR_EPS=1e-6
  LOCO_SOFT_POLAR_WINDOWS=48-64
  LOCO_SOFT_POLAR_BLEND_MAX=1.0
  LOCO_SOFT_POLAR_BLEND_STEPS=16
  LOCO_SOFT_POLAR_NORM_RESTORE=1
  LOCO_DIAG_MLP_LAYERS=0-1
  no LOCO_FULL / no LOCO_DIAG / no feature-Gram C
  paired cases: noop, active, noop2
```

Result:

| step | active | noop1 | noop2 | noop mean | active delta vs mean | read |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 40 | `5.8661` | `5.8724` | `5.8851` | `5.8788` | `-0.0126` | active better |
| 80 | `5.0898` | `5.1156` | `5.1175` | `5.1166` | `-0.0268` | active much better |
| 120 | `4.3825` | `4.3911` | `4.3843` | `4.3877` | `-0.0052` | active better |
| 160 | `4.0497` | `4.0510` | `4.0501` | `4.0506` | `-0.0008` | active slightly better |
| 200 | `3.8840` | `3.8854` | `3.8859` | `3.8857` | `-0.0017` | active beats both |

Diagnostics:

```text
step 50: blend=0.125, delta=0.0229, target_delta=0.1829, cos=0.999739
step 56: blend=0.500, delta=0.0906, target_delta=0.1813, cos=0.995868
step 64: blend=1.000, delta=0.1842, target_delta=0.1842, cos=0.982980
```

Timing:

```text
paired_noop:  step_avg=547.36ms, contaminated by a large one-off spike.
paired_active: step_avg=448.01ms.
paired_noop2: step_avg=447.55ms.

The loss comparison is clean. The first noop timing is not.
```

Interpretation:

```text
This is the first clean 200-step paired win in the immediate control family,
and it uses no feature Gram. The active effect is large at 80, remains visible
at 120, then fades to a small but still positive 200-step margin.

The full-blend perturbation is mild: cos ~= 0.983 and delta ~= 0.184 versus
hard Muon. This is much closer to PR291's p=0.1 / alpha=0.9 Soft-Muon idea
than the earlier alpha=0.5 no-C probe, which was a far stronger singular-value
change.

Do not claim right-feature preconditioning from this result. The immediate
lesson is narrower:
  no-C Muon singular-value transfer can reproduce the same early-persistent
  pattern we were trying to extract from C, with essentially no C plumbing.

Next GPU priority after the one-hour meditation should be to broaden no-C
alpha0.9 surfaces before returning to feature C:
  1. qk,v,o,mlp_fc alpha0.9 80-step paired screen, or
  2. v,mlp_fc alpha0.9 200-step paired screen if we want a lower-risk promote.

The alpha0.9 MLP-only result is not large enough by itself for a WR claim, but
it is strong enough to make PR291-style no-C Soft-Muon the top immediate branch.
```

## Cycle H Prep

PR291 polynomial adaptation:

```text
Added a separate no-C implementation flag:
  LOCO_SOFT_POLAR_IMPL=exact   # current eig T_alpha control
  LOCO_SOFT_POLAR_IMPL=pr291   # p=0.1 PR291 polynomial Soft-Muon

The PR291 path uses the p=0.1 linear combination of 12 Newton-Schulz basis
terms, with the same gram-Frobenius / Schatten-4 style input normalization
from the PR. It still runs inside our controlled no-C probe:
  raw grad -> Nesterov operand -> baseline Polar Express update
  raw grad -> Nesterov operand -> PR291 soft polynomial
  blend/norm-restore soft update into baseline update
  then ordinary NorMuon variance reduction and update

This deliberately does not implement SOAP, contra-Muon, or the PR291 late
2500-step schedule yet. The next H100 run is a clean local adaptation test of
the Soft-Muon singular-value transfer only.
```

Next queued decision:

```text
When the H100 meditation window opens at 12:57:39 IST, run a short broad no-C
surface screen with the polynomial path before returning to feature C.

Preferred command:
  MODAL_RUNNER=tools/run_softpolar_pr291_two_screen.sh
  LOCO_SOFT_POLAR_IMPL=pr291
  LOCO_SOFT_POLAR_ALPHA=0.9
  LOCO_SOFT_POLAR_POWER=0.1
  LOCO_SOFT_POLAR_WINDOWS=48-64
  SCREEN_STEPS=80
  paired cases noop,active,noop2

This compound runner executes two screens in one Modal container:
  1. mlp_fc schedule-only, to measure the split momentum / polar_from_operand
     path with zero soft update;
  2. mlp_fc active, to check whether the PR291 polynomial preserves the exact
     alpha0.9 MLP c_fc hit;
  3. qk,v,o,mlp_fc active on layers 0-1, to test broader surface coverage.

If broad all-surface polynomial is bad or too noisy, rerun a lower-risk
v,mlp_fc polynomial screen. If broad is positive at 80, promote to 200.
```
